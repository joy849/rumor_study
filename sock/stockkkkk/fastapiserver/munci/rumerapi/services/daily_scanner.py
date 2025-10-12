"""
일일 괴리 스캔

매일 발생한 뉴스 이벤트에 대해 괴리 탐지 및 알림
"""
from __future__ import annotations
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pymysql
import logging
import math
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class DailyGapScanner:
    """일일 괴리 스캐너"""

    def __init__(
            self,
            db_config: dict,
            z_threshold: float = 1.0,
            min_samples: int = 10
    ):
        """
        Args:
            db_config: DB 연결 설정
            z_threshold: Z-score 임계값
            min_samples: 최소 샘플 수
        """
        self.db_config = db_config
        self.z_threshold = z_threshold
        self.min_samples = min_samples

        # 종목코드 매핑 로드
        self.stock_code_map = self._load_stock_code_map()

    def _load_stock_code_map(self) -> dict:
        """normalized_aliases.json에서 종목명 -> 종목코드 매핑 로드"""
        project_root = Path(__file__).parent.parent.parent.parent
        json_path = project_root / "examples" / "normalized_aliases.json"

        if not json_path.exists():
            logger.warning(f"종목코드 매핑 파일 없음: {json_path}")
            return {}

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        stock_map = {}
        for main_name, aliases in data.items():
            if not aliases or len(aliases) == 0:
                continue

            stock_code = None
            for alias in aliases:
                if alias.isdigit():
                    stock_code = alias
                    break

            if not stock_code:
                continue

            stock_map[main_name] = stock_code

            for alias in aliases:
                if not alias.isdigit():
                    stock_map[alias] = stock_code

        logger.info(f"종목코드 매핑 로드 완료: {len(stock_map)}개")
        return stock_map

    def scan(self, scan_date: str = None) -> List[dict]:
        """
        일일 괴리 스캔

        Args:
            scan_date: 스캔 날짜 (YYYYMMDD, None이면 어제)

        Returns:
            List[dict]: 괴리 신호 리스트
        """
        if scan_date is None:
            scan_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

        logger.info(f"{'=' * 60}")
        logger.info(f"일일 괴리 스캔 시작: {scan_date}")
        logger.info(f"{'=' * 60}")

        signals = self._scan_news(scan_date)

        # DB 저장
        self._save_signals(signals)

        # 요약
        self._print_summary(signals, scan_date)

        return signals

    def _scan_news(self, scan_date: str) -> List[dict]:
        """
        뉴스 이벤트 스캔

        Args:
            scan_date: YYYYMMDD

        Returns:
            List[dict]: 괴리 신호 리스트
        """
        conn = None
        signals = []

        try:
            conn = pymysql.connect(**self.db_config)

            # 날짜 형식 변환: YYYYMMDD -> YYYY-MM-DD
            scan_date_formatted = f"{scan_date[:4]}-{scan_date[4:6]}-{scan_date[6:]}"

            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # Step 1: 당일 뉴스 이벤트 조회
                sql = """
                      SELECT 링크   as news_id, \
                             제목   as title, \
                             회사명  as companies, \
                             이벤트명 as events, \
                             날짜   as news_date
                      FROM comprehensive_analyzed_news
                      WHERE 날짜 = %s
                        AND 회사명 IS NOT NULL
                        AND 이벤트명 IS NOT NULL
                      ORDER BY 날짜 \
                      """
                cursor.execute(sql, (scan_date_formatted,))
                news_list = cursor.fetchall()

                logger.info(f"[뉴스] {len(news_list)}건의 이벤트 발견")

                if not news_list:
                    logger.warning("뉴스 이벤트가 없습니다")
                    return []

            # Step 2: 가격 데이터 캐싱
            logger.info("가격 데이터 로딩 중...")
            price_cache = self._load_price_cache(conn, scan_date_formatted)
            logger.info(f"✅ 가격 캐시 로드 완료: {len(price_cache)}개 종목")

            # Step 3: 통계 데이터 캐싱
            logger.info("통계 데이터 로딩 중...")
            stats_cache = self._load_stats_cache(conn)
            logger.info(f"✅ 통계 캐시 로드 완료: {len(stats_cache)}개 이벤트")

            # Step 4: 각 뉴스 처리
            for idx, news in enumerate(news_list, 1):
                try:
                    news_id = news['news_id']
                    news_title = news.get('title', '')
                    companies = news.get('companies', '')
                    events = news.get('events', '')
                    news_date = news['news_date']

                    if not companies or not events:
                        continue

                    company_list = [c.strip() for c in str(companies).split(',') if c.strip()]
                    event_list = [e.strip() for e in str(events).split(',')
                                  if e.strip() and e.strip().lower() != 'other']

                    if not event_list:
                        continue

                    # 종목코드 변환
                    for company_name in company_list:
                        stock_code = self.stock_code_map.get(company_name)
                        if not stock_code:
                            continue

                        for event in event_list:
                            # 괴리 탐지 (캐시 사용)
                            gap = self._detect_gap_cached(
                                news_id, news_title, stock_code,
                                company_name, event, news_date,
                                price_cache, stats_cache
                            )

                            if gap:
                                signals.append(gap)
                                logger.info(
                                    f"[{idx}/{len(news_list)}] "
                                    f"✅ {gap['stock_name']}: {event}, "
                                    f"Z={gap['z_score']:.2f} "
                                    f"({gap['direction']}/{gap['magnitude']})"
                                )

                except Exception as e:
                    logger.error(
                        f"[{idx}/{len(news_list)}] "
                        f"뉴스 처리 실패: {e}"
                    )
                    continue

        except Exception as e:
            logger.error(f"뉴스 스캔 실패: {e}", exc_info=True)

        finally:
            if conn:
                conn.close()

        logger.info(f"[뉴스] {len(signals)}개 괴리 신호 탐지")
        return signals

    def _load_price_cache(self, conn, scan_date: str) -> dict:
        """가격 데이터를 메모리에 캐싱"""
        cache = {}

        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                           SELECT 종목코드, 날짜, 종가
                           FROM stock_daily_prices
                           WHERE 날짜 BETWEEN DATE_SUB(%s, INTERVAL 5 DAY)
                                     AND DATE_ADD(%s, INTERVAL 5 DAY)
                           ORDER BY 종목코드, 날짜
                           """, (scan_date, scan_date))

            for row in cursor:
                stock_code = row['종목코드']
                date = row['날짜']
                price = float(row['종가'])

                if stock_code not in cache:
                    cache[stock_code] = []
                cache[stock_code].append((date, price))

        return cache

    def _load_stats_cache(self, conn) -> dict:
        """이벤트별 통계를 메모리에 캐싱"""
        cache = {}

        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                           SELECT event_code,
                                  AVG(return_1d)    as mean,
                                  STDDEV(return_1d) as std,
                                  COUNT(*)          as cnt
                           FROM news_returns
                           WHERE return_1d IS NOT NULL
                             AND news_date >= DATE_SUB(CURDATE(), INTERVAL 365 DAY)
                           GROUP BY event_code
                           """)

            for row in cursor:
                cache[row['event_code']] = {
                    'mean': float(row['mean']) if row['mean'] else 0,
                    'std': float(row['std']) if row['std'] else 0,
                    'cnt': int(row['cnt'])
                }

        return cache

    def _detect_gap_cached(
            self, news_id: str, news_title: str,
            stock_code: str, stock_name: str, event_code: str, news_date: str,
            price_cache: dict, stats_cache: dict
    ) -> dict | None:
        """괴리 탐지 (캐시 사용)"""

        # 가격 데이터 확인
        if stock_code not in price_cache:
            return None

        prices = price_cache[stock_code]
        news_date_obj = datetime.strptime(str(news_date)[:10], '%Y-%m-%d').date()

        # 앵커 가격 찾기
        anchor_idx = None
        for idx, (date, price) in enumerate(prices):
            if date >= news_date_obj:
                anchor_idx = idx
                break

        if anchor_idx is None or anchor_idx + 1 >= len(prices):
            return None

        anchor_price = prices[anchor_idx][1]
        price_1d = prices[anchor_idx + 1][1]

        # 실제 수익률
        actual = math.log(price_1d / anchor_price)

        # 통계 확인
        if event_code not in stats_cache:
            return None

        stats = stats_cache[event_code]

        if stats['cnt'] < self.min_samples:
            return None

        expected = stats['mean']
        std = stats['std']

        if std < 1e-6:
            return None

        z = (actual - expected) / std

        if abs(z) < self.z_threshold:
            return None

        direction = "OVER" if z > 0 else "UNDER"

        if abs(z) >= 3.0:
            magnitude = "EXTREME"
        elif abs(z) >= 2.0:
            magnitude = "HIGH"
        elif abs(z) >= 1.0:
            magnitude = "MODERATE"
        else:
            magnitude = "LOW"

        return {
            "news_id": news_id,
            "news_title": news_title,
            "stock_code": stock_code,
            "stock_name": stock_name,
            "event_code": event_code,
            "news_date": news_date,
            "horizon": 1,
            "actual_return": actual,
            "expected_return": expected,
            "expected_std": std,
            "z_score": z,
            "direction": direction,
            "magnitude": magnitude,
            "sample_count": stats['cnt']
        }

    def _save_signals(self, signals: List[dict]):
        """신호를 DB에 저장"""
        if not signals:
            logger.info("저장할 신호가 없습니다")
            return

        conn = None
        try:
            conn = pymysql.connect(**self.db_config)

            with conn.cursor() as cursor:
                for s in signals:
                    # news_date를 YYYYMMDD 형식으로 변환
                    if isinstance(s['news_date'], str):
                        if len(s['news_date']) == 10:  # YYYY-MM-DD
                            news_date_str = s['news_date'].replace('-', '')  # YYYYMMDD
                        else:
                            news_date_str = s['news_date']
                    else:
                        news_date_str = s['news_date'].strftime('%Y%m%d')

                    cursor.execute("""
                                   INSERT INTO news_gaps
                                   (news_id, news_title, stock_code, stock_name, event_code,
                                    news_date, horizon, actual_return, expected_return, expected_std,
                                    z_score, direction, magnitude, sample_count)
                                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY
                                   UPDATE
                                       z_score =
                                   VALUES (z_score), direction =
                                   VALUES (direction), magnitude =
                                   VALUES (magnitude)
                                   """, (
                                       s['news_id'], s['news_title'], s['stock_code'], s['stock_name'],
                                       s['event_code'], news_date_str, s['horizon'],
                                       s['actual_return'], s['expected_return'], s['expected_std'],
                                       s['z_score'], s['direction'], s['magnitude'], s['sample_count']
                                   ))

                conn.commit()
                logger.info(f"✅ DB 저장 완료: {len(signals)}건")

        except Exception as e:
            logger.error(f"DB 저장 실패: {e}", exc_info=True)
            if conn:
                conn.rollback()

        finally:
            if conn:
                conn.close()

    def _print_summary(self, signals: List[dict], scan_date: str):
        """스캔 결과 요약 출력"""
        logger.info(f"{'=' * 60}")
        logger.info(f"📊 스캔 결과 요약 ({scan_date})")
        logger.info(f"{'=' * 60}")

        if not signals:
            logger.info("괴리 신호가 발견되지 않았습니다")
            return

        # 전체 통계
        logger.info(f"총 신호 수: {len(signals)}개")

        # 방향별 통계
        over_count = sum(1 for s in signals if s['direction'] == "OVER")
        under_count = sum(1 for s in signals if s['direction'] == "UNDER")
        logger.info(f"  - 과대반응 (OVER): {over_count}개")
        logger.info(f"  - 과소반응 (UNDER): {under_count}개")

        # 강도별 통계
        extreme_count = sum(1 for s in signals if s['magnitude'] == "EXTREME")
        high_count = sum(1 for s in signals if s['magnitude'] == "HIGH")
        moderate_count = sum(1 for s in signals if s['magnitude'] == "MODERATE")
        logger.info(f"  - EXTREME: {extreme_count}개")
        logger.info(f"  - HIGH: {high_count}개")
        logger.info(f"  - MODERATE: {moderate_count}개")

        # Top 5 신호
        logger.info(f"\n{'=' * 60}")
        logger.info("🔥 Top 5 신호 (|Z| 기준)")
        logger.info(f"{'=' * 60}")

        top_signals = sorted(signals, key=lambda s: abs(s['z_score']), reverse=True)[:5]

        for rank, sig in enumerate(top_signals, 1):
            logger.info(
                f"{rank}. {sig['stock_name']}({sig['stock_code']}) "
                f"Z={sig['z_score']:+.2f} ({sig['direction']})"
            )
            logger.info(
                f"   실제={sig['actual_return'] * 100:+.2f}%, "
                f"기대={sig['expected_return'] * 100:+.2f}%"
            )
            logger.info(f"   제목: {sig['news_title'][:50]}...")

        logger.info(f"{'=' * 60}")


def run_daily_scan(
        db_config: dict,
        scan_date: str = None,
        z_threshold: float = 1.0,
        min_samples: int = 10
) -> List[dict]:
    """
    일일 스캔 실행 (단독 함수)

    Args:
        db_config: DB 설정
        scan_date: 스캔 날짜 (YYYYMMDD, None이면 어제)
        z_threshold: Z-score 임계값
        min_samples: 최소 샘플 수

    Returns:
        List[dict]: 괴리 신호 리스트
    """
    scanner = DailyGapScanner(
        db_config,
        z_threshold=z_threshold,
        min_samples=min_samples
    )

    return scanner.scan(scan_date=scan_date)


def run_backfill_scan(
        db_config: dict,
        start_date: str,
        end_date: str,
        z_threshold: float = 1.0
):
    """
    과거 날짜 범위에 대한 일괄 스캔 (백필)

    Args:
        db_config: DB 설정
        start_date: 시작일 (YYYYMMDD)
        end_date: 종료일 (YYYYMMDD)
        z_threshold: Z-score 임계값
    """
    from datetime import datetime, timedelta

    logger.info(f"백필 스캔 시작: {start_date} ~ {end_date}")

    scanner = DailyGapScanner(db_config, z_threshold=z_threshold)

    # 날짜 범위 생성
    start = datetime.strptime(start_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")

    current = start
    total_signals = 0

    while current <= end:
        scan_date_str = current.strftime("%Y%m%d")

        try:
            signals = scanner.scan(scan_date=scan_date_str)
            total_signals += len(signals)
        except Exception as e:
            logger.error(f"스캔 실패 ({scan_date_str}): {e}")

        current += timedelta(days=1)

    logger.info(f"{'=' * 60}")
    logger.info(f"백필 스캔 완료")
    logger.info(f"  - 기간: {start_date} ~ {end_date}")
    logger.info(f"  - 총 신호: {total_signals}개")
    logger.info(f"{'=' * 60}")


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    import sys
    from munci.rumerapi.core.config import settings

    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # DB 설정
    db_config = {
        'host': settings.db_host,
        'user': settings.db_username,
        'password': settings.db_password,
        'database': settings.db_database,
        'port': settings.db_port
    }

    # 실행 모드 선택
    if len(sys.argv) > 1:
        mode = sys.argv[1]

        if mode == "backfill" and len(sys.argv) >= 4:
            # 백필 모드
            start_date = sys.argv[2]
            end_date = sys.argv[3]
            run_backfill_scan(db_config, start_date, end_date)

        elif mode == "date" and len(sys.argv) >= 3:
            # 특정 날짜 스캔
            scan_date = sys.argv[2]
            run_daily_scan(db_config, scan_date=scan_date)

        else:
            print("Usage:")
            print("  python daily_scanner.py                    # 어제 스캔")
            print("  python daily_scanner.py date 20240101      # 특정 날짜")
            print("  python daily_scanner.py backfill 20240101 20241012  # 백필")

    else:
        # 기본: 어제 스캔
        run_daily_scan(db_config)
