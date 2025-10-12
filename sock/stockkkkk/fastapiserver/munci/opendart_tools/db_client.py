"""MariaDB에서 공시 데이터 조회 클라이언트"""
from __future__ import annotations
import pymysql
from typing import List, Optional
import logging

from .models import DisclosureMeta
from .utils import to_yyyymmdd

logger = logging.getLogger(__name__)


class DARTDBClient:
    """MariaDB rumors_opendart 테이블에서 공시 조회"""

    def __init__(self, db_config: dict):
        """
        Args:
            db_config: {
                'host': 'localhost',
                'username': 'user',
                'password': 'pass',
                'database': 'dbname',
                'port': 3306
            }
        """
        self.config = db_config

    def _get_connection(self):
        """DB 연결 생성"""
        return pymysql.connect(
            host=self.config.get('host', 'localhost'),
            user=self.config.get('username'),
            password=self.config.get('password'),
            database=self.config.get('database'),
            port=self.config.get('port', 3306),
            charset='utf8mb4'
        )

    def list_disclosures(
            self,
            corp_code: int | str,
            bgn_de: str,
            end_de: str,
            corp_name: str = None,
    ) -> List[DisclosureMeta]:
        """
        DB에서 공시 목록 조회 (1차: corp_code, 2차: corp_name)

        Args:
            corp_code: 기업 코드 (숫자 또는 8자리 문자열)
            bgn_de: 시작일 (YYYYMMDD)
            end_de: 종료일 (YYYYMMDD)
            corp_name: 회사명 (corp_code 없을 때 사용)

        Returns:
            공시 메타데이터 리스트
        """
        # corp_code를 문자열로 변환 (8자리 제로패딩)
        if isinstance(corp_code, int):
            corp_code = str(corp_code).zfill(8)

        conn = None
        try:
            conn = self._get_connection()

            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # 1차: corp_code로 조회
                if corp_code:
                    sql = """
                          SELECT rcept_no, \
                                 rcept_dt, \
                                 corp_code, \
                                 corp_name, \
                                 report_nm, \
                                 flr_nm, \
                                 rm, \
                                 counterparty
                          FROM rumors_opendart
                          WHERE corp_code = %s
                            AND rcept_dt BETWEEN %s AND %s
                          ORDER BY rcept_dt DESC \
                          """
                    cursor.execute(sql, (corp_code, bgn_de, end_de))
                    rows = cursor.fetchall()

                    if rows:
                        logger.info(f"✓ corp_code로 {len(rows)}건 조회 (corp_code={corp_code})")
                    else:
                        logger.info(f"corp_code로 조회 결과 없음 (corp_code={corp_code})")

                # 2차: corp_code로 조회 실패 시 corp_name으로 재시도
                if (not corp_code or not rows) and corp_name:
                    logger.info(f"corp_name으로 재시도 (corp_name={corp_name})")

                    sql = """
                          SELECT rcept_no, \
                                 rcept_dt, \
                                 corp_code, \
                                 corp_name, \
                                 report_nm, \
                                 flr_nm, \
                                 rm, \
                                 counterparty
                          FROM rumors_opendart
                          WHERE corp_name = %s
                            AND rcept_dt BETWEEN %s AND %s
                          ORDER BY rcept_dt DESC \
                          """
                    cursor.execute(sql, (corp_name, bgn_de, end_de))
                    rows = cursor.fetchall()

                    if rows:
                        logger.info(f"✓ corp_name으로 {len(rows)}건 조회 (corp_name={corp_name})")
                    else:
                        logger.info(f"corp_name으로도 조회 결과 없음 (corp_name={corp_name})")

                # 결과 변환
                results = []
                for row in rows:
                    results.append(DisclosureMeta(
                        rcept_no=row.get('rcept_no') or '',
                        rcept_dt=row.get('rcept_dt') or '',
                        corp_code=row.get('corp_code') or '',
                        corp_name=row.get('corp_name') or '',
                        report_nm=row.get('report_nm') or '',
                        flr_nm=row.get('flr_nm') or '',
                        rm=row.get('rm') or '',
                        pblntf_ty='I',
                        counterparty=row.get('counterparty') or ''
                    ))

                return results

        except Exception as e:
            logger.error(f"DB 조회 실패: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def find_inquiry_disclosures(
            self,
            corp_code: int | str,
            bgn_de: str,
            end_de: str,
            corp_name: str = None,
    ) -> List[DisclosureMeta]:
        """
        조회공시만 빠르게 조회 (1차: corp_code, 2차: corp_name)

        Args:
            corp_code: 기업 코드 (숫자 또는 8자리 문자열)
            bgn_de: 시작일 (YYYYMMDD)
            end_de: 종료일 (YYYYMMDD)
            corp_name: 회사명 (corp_code 없을 때 사용)

        Returns:
            조회공시 리스트
        """
        # corp_code를 문자열로 변환 (8자리 제로패딩)
        if isinstance(corp_code, int):
            corp_code = str(corp_code).zfill(8)

        conn = None
        try:
            conn = self._get_connection()

            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # 1차: corp_code로 조회
                if corp_code:
                    sql = """
                          SELECT rcept_no, \
                                 rcept_dt, \
                                 corp_code, \
                                 corp_name, \
                                 report_nm, \
                                 flr_nm, \
                                 rm, \
                                 counterparty
                          FROM rumors_opendart
                          WHERE corp_code = %s
                            AND rcept_dt BETWEEN %s AND %s
                            AND (
                              report_nm LIKE '%조회공시%'
                                  OR report_nm LIKE '%풍문%'
                                  OR report_nm LIKE '%해명%'
                              )
                          ORDER BY rcept_dt DESC \
                          """
                    cursor.execute(sql, (corp_code, bgn_de, end_de))
                    rows = cursor.fetchall()

                    if rows:
                        logger.info(f"✓ corp_code로 조회공시 {len(rows)}건 조회")
                    else:
                        logger.info(f"corp_code로 조회공시 없음")

                # 2차: corp_code로 조회 실패 시 corp_name으로 재시도
                if (not corp_code or not rows) and corp_name:
                    logger.info(f"corp_name으로 조회공시 재시도 (corp_name={corp_name})")

                    sql = """
                          SELECT rcept_no, \
                                 rcept_dt, \
                                 corp_code, \
                                 corp_name, \
                                 report_nm, \
                                 flr_nm, \
                                 rm, \
                                 counterparty
                          FROM rumors_opendart
                          WHERE corp_name = %s
                            AND rcept_dt BETWEEN %s AND %s
                            AND (
                              report_nm LIKE '%조회공시%'
                                  OR report_nm LIKE '%풍문%'
                                  OR report_nm LIKE '%해명%'
                              )
                          ORDER BY rcept_dt DESC \
                          """
                    cursor.execute(sql, (corp_name, bgn_de, end_de))
                    rows = cursor.fetchall()

                    if rows:
                        logger.info(f"✓ corp_name으로 조회공시 {len(rows)}건 조회")
                    else:
                        logger.info(f"corp_name으로도 조회공시 없음")

                # 결과 변환
                results = []
                for row in rows:
                    results.append(DisclosureMeta(
                        rcept_no=row.get('rcept_no') or '',
                        rcept_dt=row.get('rcept_dt') or '',
                        corp_code=row.get('corp_code') or '',
                        corp_name=row.get('corp_name') or '',
                        report_nm=row.get('report_nm') or '',
                        flr_nm=row.get('flr_nm') or '',
                        rm=row.get('rm') or '',
                        pblntf_ty='I',
                        counterparty=row.get('counterparty') or ''
                    ))

                return results

        except Exception as e:
            logger.error(f"조회공시 검색 실패: {e}")
            return []
        finally:
            if conn:
                conn.close()
