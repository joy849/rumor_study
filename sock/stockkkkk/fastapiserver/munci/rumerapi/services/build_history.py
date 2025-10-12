"""
역사적 이벤트-수익률 DB 구축

과거 공시 이벤트에 대한 1D/3D/5D 수익률 계산 및 저장
"""
from __future__ import annotations
from typing import Optional
import pymysql
import logging
from datetime import datetime

from munci.signal_gap.core.event_price_mapper import EventPriceMapper
from munci.signal_gap.core.return_calculator import ReturnCalculator

logger = logging.getLogger(__name__)

# 이벤트 코드 분류 규칙 (간소화 버전)
EVENT_CLASSIFICATION_RULES = {
    # M&A 관련
    "합병": "company.mna_merger",
    "인수": "company.mna_acquisition",
    "매각": "company.mna_disposal",

    # 자본 관련
    "유상증자": "company.capital_increase_rights",
    "무상증자": "company.bonus_issue",
    "감자": "company.capital_reduction",

    # 계약 관련
    "계약": "company.big_contract_update",
    "수주": "company.big_contract_update",
    "공급계약": "company.big_contract_update",

    # 실적
    "실적": "company.earnings_result",
    "영업이익": "company.earnings_result",
    "순이익": "company.earnings_result",

    # 조회공시
    "조회공시": "company.inquiry_disclosure",
    "풍문": "company.inquiry_disclosure",
}


def classify_event_code(report_nm: str) -> str:
    """
    공시명 → event_code 분류

    Args:
        report_nm: 공시명

    Returns:
        event_code (예: company.mna_deal)
    """
    report_lower = report_nm.lower()

    # 규칙 매칭
    for keyword, event_code in EVENT_CLASSIFICATION_RULES.items():
        if keyword in report_lower:
            return event_code

    return "company.other"


def get_stock_code(corp_code: str, conn) -> Optional[str]:
    """
    corp_code → stock_code 변환

    Args:
        corp_code: 법인코드 (8자리)
        conn: DB 연결

    Returns:
        stock_code (6자리) or None
    """
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(
            "SELECT stock_code FROM krx_gongsi_code WHERE corp_code = %s",
            (corp_code,)
        )
        row = cursor.fetchone()
        return row['stock_code'] if row else None


def build_event_returns_history(
        db_config: dict,
        start_date: str = "20200101",
        end_date: str = "20241231",
        batch_size: int = 1000
):
    """
    과거 이벤트의 수익률 이력 구축

    절차:
    1. DART 공시 DB에서 이벤트 추출
    2. 각 이벤트에 대해 앵커 가격 조회
    3. 1D/3D/5D 수익률 계산
    4. event_returns_history 테이블에 저장

    Args:
        db_config: DB 연결 설정
        start_date: 시작일 (YYYYMMDD)
        end_date: 종료일 (YYYYMMDD)
        batch_size: 배치 크기
    """
    logger.info(f"역사적 수익률 DB 구축 시작: {start_date} ~ {end_date}")

    mapper = EventPriceMapper(db_config)
    calculator = ReturnCalculator(db_config)
    conn = pymysql.connect(**db_config)

    total_processed = 0
    total_saved = 0

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # Step 1: 공시 이벤트 조회
            sql = """
                  SELECT corp_code, \
                         rcept_dt as event_date, \
                         report_nm, \
                         corp_name
                  FROM rumors_opendart
                  WHERE rcept_dt BETWEEN %s AND %s
                  ORDER BY rcept_dt \
                  """
            cursor.execute(sql, (start_date, end_date))
            events = cursor.fetchall()

            logger.info(f"총 {len(events)}건의 이벤트 발견")

            for idx, event in enumerate(events, 1):
                total_processed += 1

                # 진행 상황 출력
                if idx % 100 == 0:
                    logger.info(
                        f"진행: {idx}/{len(events)} "
                        f"({idx / len(events) * 100:.1f}%), "
                        f"저장: {total_saved}건"
                    )

                try:
                    # Step 2: event_code 분류
                    event_code = classify_event_code(event['report_nm'])

                    # Step 3: 종목코드 조회
                    stock_code = get_stock_code(event['corp_code'], conn)
                    if not stock_code:
                        logger.debug(f"종목코드 없음: {event['corp_code']}")
                        continue

                    # Step 4: 앵커 가격 조회
                    anchor = mapper.get_anchor_price(
                        stock_code,
                        event['event_date']
                    )
                    if not anchor:
                        logger.debug(
                            f"앵커 없음: {stock_code} @ {event['event_date']}"
                        )
                        continue

                    # Step 5: 수익률 계산
                    returns = calculator.calculate_returns(
                        stock_code,
                        anchor.anchor_date,
                        anchor.anchor_close,
                        horizons=[1, 3, 5]
                    )

                    # 수익률이 하나라도 있어야 저장
                    if all(v is None for v in returns.horizons.values()):
                        logger.debug(f"수익률 없음: {stock_code}")
                        continue

                    # Step 6: DB 저장
                    insert_sql = """
                                 INSERT INTO event_returns_history
                                 (stock_code, event_date, event_code, anchor_date,
                                  anchor_price, return_1d, return_3d, return_5d,
                                  volume, market_cap, created_at)
                                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()) \
                                 """
                    cursor.execute(insert_sql, (
                        stock_code,
                        event['event_date'],
                        event_code,
                        anchor.anchor_date,
                        anchor.anchor_close,
                        returns.horizons.get(1),
                        returns.horizons.get(3),
                        returns.horizons.get(5),
                        anchor.volume,
                        anchor.market_cap
                    ))

                    total_saved += 1

                    # 배치마다 커밋
                    if total_saved % batch_size == 0:
                        conn.commit()
                        logger.info(f"배치 커밋: {total_saved}건")

                except Exception as e:
                    logger.error(
                        f"이벤트 처리 실패: {event['corp_name']} "
                        f"@ {event['event_date']}: {e}"
                    )
                    continue

        # 최종 커밋
        conn.commit()

        logger.info("=" * 60)
        logger.info(f"✅ 역사적 수익률 DB 구축 완료")
        logger.info(f"   - 처리: {total_processed}건")
        logger.info(f"   - 저장: {total_saved}건")
        logger.info(f"   - 성공률: {total_saved / total_processed * 100:.1f}%")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"배치 작업 실패: {e}", exc_info=True)
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 환경 변수 로드
    load_dotenv()

    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USERNAME'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_DATABASE'),
        'port': int(os.getenv('DB_PORT', 3306))
    }

    # 실행
    build_event_returns_history(
        db_config,
        start_date="20230101",  # 최근 2년
        end_date="20241231"
    )
