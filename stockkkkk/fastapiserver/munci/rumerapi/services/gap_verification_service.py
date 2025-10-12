from __future__ import annotations
import logging
import uuid
import pymysql
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import math

from munci.rumerapi.models.gap_schemas import (
    GapVerifyRequest, GapVerifyResponse, GapSignal, NewsValidation
)
from munci.rumerapi.models.schemas import Evidence, EvidenceType
from munci.rumerapi.extractors.companyGpt import extract_companies, initialize_extractor
from munci.lastsa.event_with_translate import classify_event, initialize_event_classifier
from munci.main_utils.date_context import extract_date_context
from munci.main_utils.optional_imports import try_import_trust_evaluator, try_import_dart_verifier
from munci.rumerapi.core.config import settings
from munci.news_es.search import search_with_api_params
from munci.news_es.es_client import create_es_client

TrustEvaluator = try_import_trust_evaluator()
OpenDARTVerifier = try_import_dart_verifier()

logger = logging.getLogger(__name__)


def _clip_adj(value: float) -> float:
    """DART 조정값 클리핑"""
    return max(-0.5, min(0.5, value))


class GapVerificationService:
    """Gap 중심 통합 검증 서비스 (Rumor 로직 통합)"""

    def __init__(self):
        self.es = create_es_client()
        self.index = settings.es_index
        self.evaluator = TrustEvaluator() if TrustEvaluator else None

        # DB 설정
        db_config = None
        if all([settings.db_host, settings.db_username, settings.db_password, settings.db_database]):
            db_config = {
                'host': settings.db_host,
                'username': settings.db_username,
                'password': settings.db_password,
                'database': settings.db_database,
                'port': settings.db_port
            }
            self.db_config = {
                'host': settings.db_host,
                'user': settings.db_username,
                'password': settings.db_password,
                'database': settings.db_database,
                'port': settings.db_port
            }
            logger.info("DB 설정 완료 - 하이브리드 모드 (DB + API)")
        else:
            self.db_config = None
            logger.info("DB 설정 없음 - API 전용 모드")

        # DART Verifier 초기화
        if OpenDARTVerifier and settings.dart_api_key:
            self.dart_verifier = OpenDARTVerifier(
                api_key=settings.dart_api_key,
                db_config=db_config
            )
        else:
            self.dart_verifier = None

    def verify(self, req: GapVerifyRequest) -> GapVerifyResponse:
        """Gap 중심 통합 검증"""
        initialize_extractor()
        initialize_event_classifier()

        # 1. 회사명/이벤트 추출
        extraction_result = extract_companies(req.query_text)
        companies = extraction_result.get('companies', [])
        company_details = extraction_result.get('company_details', {})

        event_result = classify_event(req.query_text)
        date_range = extract_date_context(req.query_text)

        logger.info(f"Extracted companies: {companies}")
        if company_details:
            logger.info(f"Company details: {company_details}")
        logger.info(f"Event result: {event_result.labels}, phrases: {event_result.event_phrases}")
        logger.info(f"Date range: {date_range}")

        # 회사명 추출 (종목코드 6자리 패딩)
        stock_codes = []
        stock_code_map = {}  # {stock_code: stock_name}
        for name, details in company_details.items():
            if details and details.get('stock_code'):
                code = details['stock_code'].zfill(6)  # 6자리로 패딩
                stock_codes.append(code)
                stock_code_map[code] = name

        # 2. 뉴스 검색
        search_result = search_with_api_params(
            es=self.es,
            index=self.index,
            query=req.query_text,
            companies=companies,
            event_phrases=event_result.event_phrases,
            event_labels=event_result.labels,
            date_range=date_range,
            use_flexible_matching=True
        )

        logger.info(f"Search result - total_hits: {search_result.get('total_hits', 0)}")
        results = search_result.get("results", [])

        # 매칭 분석
        exact_matches = []
        partial_matches = []

        for r in results:
            doc_companies = r.get("companies", [])
            doc_event_codes = r.get("event_codes", [])

            company_match = any(c in doc_companies for c in companies) if companies else False
            event_match = False

            if event_result.labels and event_result.labels != ["other"]:
                event_match = any(label in doc_event_codes for label in event_result.labels)

            if not event_match and event_result.event_phrases:
                title_lower = (r.get("title") or "").lower()
                for phrase in event_result.event_phrases:
                    if phrase and phrase.lower() in title_lower:
                        event_match = True
                        break

            if company_match and event_match:
                exact_matches.append(r)
            elif company_match or event_match:
                partial_matches.append(r)

        # 3. 뉴스 검증 (기존 Rumor 로직)
        news_validation = self._validate_news(
            req.query_text, companies, results,
            exact_matches, partial_matches,
            search_result, date_range, company_details, event_result
        )

        # 4. 괴리 분석
        gap_signals = []
        if stock_codes and self.db_config:
            gap_signals = self._analyze_gaps(
                stock_codes, stock_code_map,
                event_result.labels, req.query_text, req.days
            )

        # 5. 증거 추출
        news_evidence = self._extract_evidence_from_results(exact_matches or results)
        dart_evidence = news_validation.get('dart_evidence', [])
        all_evidence = (dart_evidence + news_evidence)[:5]

        # 6. 최종 요약
        summary = self._build_summary(news_validation, gap_signals)

        return GapVerifyResponse(
            id=str(uuid.uuid4()),
            query=req.query_text,

            extracted={
                "companies": companies,
                "stock_codes": stock_codes,
                "events": event_result.labels
            },

            news_validation=NewsValidation(**news_validation),
            gap_signals=gap_signals,
            evidence=all_evidence,

            summary=summary,
            risk_alert=self._build_risk_alert(news_validation, gap_signals),

            analyzed_at=datetime.now()
        )

    def _validate_news(
            self, query_text: str, companies: List[str], results: List[Dict],
            exact_matches: List, partial_matches: List,
            search_result: Dict, date_range: tuple,
            company_details: Dict, event_result
    ) -> Dict:
        """뉴스 검증 (기존 Rumor 로직)"""

        # 기본 신뢰도 평가
        base_score = self._evaluate_trust(search_result, exact_matches, partial_matches)

        # 모순 탐지
        contradictions = self._detect_contradictions(results)
        contradiction_penalty = -0.5 if contradictions else 0.0

        # 핵심 주장 검증
        claim_support = self._verify_key_claims(query_text, companies, results)
        claim_penalty = 0.0
        if claim_support < 0.3:
            claim_penalty = -0.2
        elif claim_support < 0.5:
            claim_penalty = -0.1

        # 시간적 일치도
        temporal_score = self._verify_temporal_consistency(query_text, date_range, results)
        temporal_penalty = 0.0
        if temporal_score < 0.2:
            temporal_penalty = -0.15
        elif temporal_score < 0.4:
            temporal_penalty = -0.05

        # 점수 조정
        base_score = max(0.0, base_score + contradiction_penalty + claim_penalty + temporal_penalty)

        # DART 검증
        dart_adj = 0.0
        dart_evidence = []
        dart_confirmed = False

        if companies and self.dart_verifier:
            try:
                if hasattr(self.dart_verifier, 'verify_with_event'):
                    dart_res = self.dart_verifier.verify_with_event(
                        company_names=companies,
                        article_title=query_text[:100],
                        article_content=query_text,
                        event_labels=event_result.labels,
                        event_phrases=event_result.event_phrases,
                        window_days=7,
                        company_details=company_details
                    )
                else:
                    dart_res = self.dart_verifier.verify(
                        company_names=companies,
                        article_title=query_text[:100],
                        article_content=query_text,
                        window_days=7,
                        company_details=company_details
                    )

                if dart_res.rumor_score_adjustment is not None:
                    raw_adj = -1 * (dart_res.rumor_score_adjustment / 100.0)
                    dart_adj = _clip_adj(raw_adj)
                    logger.info(f"DART adjustment: {dart_adj}")

                if dart_res.relevant_disclosures:
                    dart_confirmed = True
                    for disc in dart_res.relevant_disclosures[:3]:
                        dart_evidence.append(Evidence(
                            type=EvidenceType.DISCLOSURE,
                            title=f"[공시] {disc.corp_name}: {disc.report_nm[:120]}",
                            url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={disc.rcept_no}",
                            published_at=datetime.strptime(disc.rcept_dt, "%Y%m%d") if disc.rcept_dt else None,
                        ))
            except Exception as e:
                logger.exception(f"DART verification failed: {e}")

        final_score = max(0.0, min(1.0, base_score + dart_adj))

        # 신뢰도 레벨
        if final_score >= 0.7:
            reliability_level = "HIGH"
        elif final_score >= 0.4:
            reliability_level = "MEDIUM"
        else:
            reliability_level = "LOW"

        return {
            "trust_score": round(final_score, 2),
            "news_found": len(results),
            "exact_matches": len(exact_matches),

            "has_contradictions": len(contradictions) > 0,
            "contradiction_count": len(contradictions),
            "claim_support_ratio": round(claim_support, 2),
            "temporal_consistency": round(temporal_score, 2),

            "dart_confirmed": dart_confirmed,
            "dart_evidence_count": len(dart_evidence),
            "dart_evidence": dart_evidence,

            "is_reliable": final_score >= 0.4,
            "reliability_level": reliability_level
        }

    def _analyze_gaps(
            self, stock_codes: List[str], stock_code_map: Dict[str, str],
            event_labels: List[str], query_text: str, days: int
    ) -> List[GapSignal]:
        """
        괴리 분석 (복수 종목 지원)

        예: "현대차와 삼성전자 괴리 있음?"
        → stock_codes = ["005380", "005930"]
        → 각 종목별 괴리 신호 조회하여 리스트로 반환
        """
        if not self.db_config:
            logger.warning("DB 설정 없음 - 괴리 분석 불가")
            return []

        if not stock_codes:
            logger.info("회사명 없음 - 괴리 분석 건너뜀")
            return []

        logger.info(f"괴리 분석 시작 - 종목: {stock_codes}, 이벤트: {event_labels}")

        conn = pymysql.connect(**self.db_config)
        gap_signals = []

        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

                # 각 종목별로 괴리 조회
                for stock_code in stock_codes:
                    stock_name = stock_code_map.get(stock_code, stock_code)

                    logger.info(f"  → {stock_name}({stock_code}) 괴리 조회 중...")

                    # DB에서 괴리 신호 조회
                    cursor.execute("""
                                   SELECT news_title,
                                          event_code,
                                          news_date,
                                          z_score,
                                          direction,
                                          magnitude,
                                          actual_return,
                                          expected_return,
                                          sample_count
                                   FROM news_gaps
                                   WHERE stock_code = %s
                                     AND news_date >= %s
                                   ORDER BY ABS(z_score) DESC LIMIT 5
                                   """, (stock_code, start_date))

                    rows = cursor.fetchall()

                    if not rows:
                        logger.info(f"    괴리 신호 없음")
                        # 괴리 없는 종목도 표시 (has_gap=False)
                        gap_signals.append(GapSignal(
                            stock_code=stock_code,
                            stock_name=stock_name,
                            news_title="",
                            event_code="",
                            news_date="",

                            has_gap=False,
                            direction=None,
                            magnitude=None,
                            z_score=None,

                            actual_return=0.0,
                            expected_return=0.0,
                            sample_count=0,

                            interpretation=f"{stock_name}: 최근 {days}일간 괴리 신호 없음",
                            risk_level="LOW"
                        ))
                        continue

                    logger.info(f"    괴리 신호 {len(rows)}건 발견")

                    for row in rows:
                        # 이벤트 매칭 확인
                        # - 정확 매칭: company.earnings_result == company.earnings_result
                        # - Prefix 매칭: company.earnings_result 시작 부분이 company와 일치
                        # - 이벤트 없음/other → 괴리 반환 안함

                        if event_labels and event_labels != ["other"]:
                            db_event = row['event_code']
                            matched = False

                            for query_event in event_labels:
                                # 정확 일치
                                if db_event == query_event:
                                    matched = True
                                    logger.debug(f"      ✅ 매칭: {db_event} == {query_event} (정확 일치)")
                                    break

                                # Prefix 매칭
                                # DB: "company.earnings_result"
                                # Query: "company" → 매칭 O
                                # Query: "company.contract" → 매칭 X
                                db_prefix = db_event.split('.')[0] if '.' in db_event else db_event
                                query_prefix = query_event.split('.')[0] if '.' in query_event else query_event

                                if db_prefix == query_prefix:
                                    matched = True
                                    logger.debug(f"      ✅ 매칭: {db_event} ≈ {query_event} (prefix: {db_prefix})")
                                    break

                            if not matched:
                                logger.debug(f"      ❌ 스킵: {db_event} (query: {event_labels})")
                                continue
                        else:
                            # 이벤트 없거나 other → 괴리 조회 안함
                            logger.debug(f"      ❌ 스킵: 이벤트 없음 (event_labels={event_labels})")
                            continue

                        z_score = float(row['z_score']) if row['z_score'] else None

                        # 해석 생성
                        interpretation = self._build_gap_interpretation(
                            stock_name,
                            row['event_code'],
                            z_score,
                            float(row['actual_return']) * 100,
                            float(row['expected_return']) * 100
                        )

                        # 위험 레벨
                        if z_score is not None:
                            risk_level = "HIGH" if abs(z_score) >= 3.0 else "MEDIUM" if abs(z_score) >= 2.0 else "LOW"
                        else:
                            risk_level = "LOW"

                        gap_signals.append(GapSignal(
                            stock_code=stock_code,
                            stock_name=stock_name,
                            news_title=row['news_title'],
                            event_code=row['event_code'],
                            news_date=row['news_date'],

                            has_gap=True,
                            direction=row['direction'],
                            magnitude=row['magnitude'],
                            z_score=z_score,

                            actual_return=float(row['actual_return']) * 100,
                            expected_return=float(row['expected_return']) * 100,
                            sample_count=row['sample_count'],

                            interpretation=interpretation,
                            risk_level=risk_level
                        ))

                        logger.info(
                            f"      ✅ {row['event_code']}: Z={z_score:.2f}, {row['direction']}/{row['magnitude']}")

        except Exception as e:
            logger.exception(f"Gap analysis failed: {e}")

        finally:
            conn.close()

        logger.info(f"괴리 분석 완료 - 총 {len(gap_signals)}건")
        return gap_signals

    def _build_gap_interpretation(
            self, stock_name: str, event_code: str, z_score: float,
            actual: float, expected: float
    ) -> str:
        """괴리 해석 생성 (종목명 포함)"""
        event_names = {
            'earnings_update': '실적 발표',
            'investment_expansion': '투자 확대',
            'ma_merger': 'M&A',
            'contract_win': '계약 체결',
            'product_launch': '신제품 출시',
            'stock_issuance': '유상증자',
            'dividend': '배당',
            'leadership_change': '임원 변동',
        }

        event_name = event_names.get(event_code, event_code)
        direction = "높은" if z_score > 0 else "낮은"

        return f"{stock_name}: 과거 유사 '{event_name}' 이벤트 대비 {abs(z_score):.1f}배 {direction} 시장 반응"

    def _build_summary(self, news_validation: Dict, gap_signals: List[GapSignal]) -> str:
        """최종 요약 생성 (복수 종목 지원)"""
        parts = []

        # 뉴스 신뢰도
        level = news_validation['reliability_level']
        score = news_validation['trust_score']
        parts.append(f"뉴스 신뢰도 {level} ({score:.2f})")

        # 주요 포인트
        if news_validation['has_contradictions']:
            parts.append(f"{news_validation['contradiction_count']}건의 부인/해명 기사 발견")
        elif news_validation['dart_confirmed']:
            parts.append("공시로 공식 확인")

        # 괴리 신호 (종목별 요약)
        if gap_signals:
            # has_gap=True인 것만 카운트
            actual_gaps = [g for g in gap_signals if g.has_gap]

            if actual_gaps:
                # 종목별 괴리 요약
                stock_summaries = []
                extreme_count = 0

                # 종목별로 그룹화
                by_stock = {}
                for g in actual_gaps:
                    if g.stock_name not in by_stock:
                        by_stock[g.stock_name] = []
                    by_stock[g.stock_name].append(g)

                for stock_name, gaps in by_stock.items():
                    extreme = [g for g in gaps if g.magnitude == 'EXTREME']
                    if extreme:
                        extreme_count += len(extreme)
                        stock_summaries.append(f"{stock_name} 극심한 괴리 {len(extreme)}건")
                    else:
                        stock_summaries.append(f"{stock_name} 괴리 {len(gaps)}건")

                if extreme_count > 0:
                    parts.append(f"⚡ {', '.join(stock_summaries)}")
                else:
                    parts.append(f"괴리 신호: {', '.join(stock_summaries)}")
            else:
                # 조회는 했지만 괴리 없음
                no_gap_stocks = [g.stock_name for g in gap_signals if not g.has_gap]
                if no_gap_stocks:
                    parts.append(f"{', '.join(no_gap_stocks)}: 괴리 없음")

        return " - ".join(parts)

    def _build_risk_alert(self, news_validation: Dict, gap_signals: List[GapSignal]) -> Optional[str]:
        """위험 경고 생성 (복수 종목 지원)"""
        alerts = []

        if news_validation['has_contradictions']:
            alerts.append("부인/해명 기사 존재")

        # has_gap=True이고 magnitude가 EXTREME인 것만
        extreme_gaps = [g for g in gap_signals if g.has_gap and g.magnitude == 'EXTREME']
        if extreme_gaps:
            # 종목별로 그룹화
            by_stock = {}
            for g in extreme_gaps:
                if g.stock_name not in by_stock:
                    by_stock[g.stock_name] = []
                by_stock[g.stock_name].append(g)

            stock_alerts = [f"{name}({len(gaps)}건)" for name, gaps in by_stock.items()]
            alerts.append(f"비정상적 시장 반응 감지: {', '.join(stock_alerts)}")

        if news_validation['reliability_level'] == 'LOW':
            alerts.append("뉴스 신뢰도 낮음")

        return " | ".join(alerts) if alerts else None

    # ===== 기존 Rumor 로직 (내부 메서드) =====

    def _evaluate_trust(self, search_result: Dict, exact_matches: List, partial_matches: List) -> float:
        """신뢰도 평가 (기존 rumor_service 로직)"""
        results = search_result.get("results", [])
        total_hits = search_result.get("total_hits", 0)

        base_score = 0.0
        source_diversity_bonus = 0.0
        relevance_bonus = 0.0

        if exact_matches:
            num_sources = len(exact_matches)

            if num_sources == 1:
                base_score = 0.5
            elif num_sources == 2:
                base_score = 0.65
            elif num_sources >= 3 and num_sources < 5:
                base_score = 0.75
            elif num_sources >= 5 and num_sources < 10:
                base_score = 0.85
            else:
                base_score = 0.9

            unique_sources = set()
            for match in exact_matches[:10]:
                source = match.get("publisher", "")
                if source:
                    unique_sources.add(source)

            if len(unique_sources) >= 5:
                source_diversity_bonus = 0.05

            top_scores = [r.get("score", 0) for r in exact_matches[:5]]
            if top_scores:
                avg_score = sum(top_scores) / len(top_scores)
                if avg_score > 30:
                    relevance_bonus = 0.05
                elif avg_score > 20:
                    relevance_bonus = 0.03
                elif avg_score > 10:
                    relevance_bonus = 0.02

        elif partial_matches:
            num_sources = len(partial_matches)

            if num_sources == 1:
                base_score = 0.25
            elif num_sources == 2:
                base_score = 0.35
            elif num_sources >= 3 and num_sources < 5:
                base_score = 0.45
            else:
                base_score = 0.5

        elif results:
            top_score = results[0].get("score", 0)
            if top_score > 20:
                base_score = 0.15
            elif top_score > 10:
                base_score = 0.1
            else:
                base_score = 0.05
        else:
            return 0.0

        final_score = min(1.0, base_score + source_diversity_bonus + relevance_bonus)
        return final_score

    def _detect_contradictions(self, results: List[Dict]) -> List[Dict]:
        """모순 탐지 (기존 rumor_service 로직)"""
        contradiction_keywords = [
            "부인", "사실무근", "해명", "아니다", "없다", "틀렸다",
            "조회공시", "해당사항없음", "검토한바없", "추진사실없",
            "계획없", "근거없", "사실과다름", "허위", "오보"
        ]

        contradictions = []

        for result in results[:20]:
            title = (result.get('title') or '').lower()
            body = (result.get('body') or '').lower()
            full_text = title + " " + body

            for keyword in contradiction_keywords:
                if keyword in full_text:
                    contradictions.append({
                        "title": result.get('title'),
                        "publisher": result.get('publisher'),
                        "keyword": keyword,
                        "url": result.get('url')
                    })
                    break

        return contradictions

    def _verify_key_claims(self, query_text: str, companies: List[str], results: List[Dict]) -> float:
        """핵심 주장 검증 (기존 rumor_service 로직)"""
        import re

        claims = []
        claims.extend(companies)

        amounts = re.findall(r'\d+[\.,]?\d*\s*(?:조|억|만|천|백|달러|원|%)', query_text)
        claims.extend(amounts)

        key_terms = [
            "인수", "매각", "투자", "확대", "발표", "체결", "결정",
            "합병", "계약", "수주", "증자", "감자", "상장", "폐쇄"
        ]
        found_terms = [term for term in key_terms if term in query_text]
        claims.extend(found_terms)

        if not claims:
            return 0.5

        supported_claims = set()

        for result in results[:10]:
            article_text = f"{result.get('title', '')} {result.get('body', '')}".lower()

            for claim in claims:
                if claim.lower() in article_text:
                    supported_claims.add(claim)

        return len(supported_claims) / len(claims)

    def _verify_temporal_consistency(
            self, query_text: str, date_range: tuple, results: List[Dict]
    ) -> float:
        """시간적 일치도 (기존 rumor_service 로직)"""
        from datetime import timezone, timedelta

        if not results:
            return 0.5

        if date_range and date_range[0] and date_range[1]:
            start_date = date_range[0]
            end_date = date_range[1]
        else:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=90)

        articles_in_range = 0
        total_articles = 0

        for result in results[:20]:
            published_at_str = result.get('published_at')
            if not published_at_str:
                continue

            total_articles += 1

            try:
                if isinstance(published_at_str, str):
                    article_date = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
                else:
                    continue

                if start_date <= article_date <= end_date:
                    articles_in_range += 1

            except Exception:
                continue

        if total_articles == 0:
            return 0.5

        return articles_in_range / total_articles

    def _extract_evidence_from_results(self, results: List[Dict], max_items: int = 3) -> List[Evidence]:
        """증거 추출 (기존 rumor_service 로직)"""
        evs = []
        for r in results[:max_items]:
            title = r.get("title", "제목 없음")
            url = r.get("url", "")
            dt_str = r.get("published_at")
            dt_obj = None
            if isinstance(dt_str, str):
                try:
                    dt_obj = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                except Exception:
                    dt_obj = None
            evs.append(Evidence(type=EvidenceType.NEWS, title=title[:200], url=url, published_at=dt_obj))
        return evs
