"""Thin OpenDART client for listing disclosures (list.json)."""
from __future__ import annotations
import time, random
import requests
from typing import List, Optional
import datetime as dt
from .utils import to_yyyymmdd
from .models import DisclosureMeta

BASE_URL = "https://opendart.fss.or.kr/api"


class DARTClient:
    def __init__(self, api_key: str, session: Optional[requests.Session] = None):
        if not api_key:
            raise ValueError("DART API Key가 필요합니다.")
        self.api_key = api_key
        self.session = session or requests.Session()

    def list_disclosures(
            self,
            corp_code: int | str,
            bgn_de: str | dt.date | dt.datetime,
            end_de: str | dt.date | dt.datetime,
            page_count: int = 100,
            last_reprt_at: str = "N",
            max_pages: int = 3,
            timeout: int = 7,
    ) -> List[DisclosureMeta]:
        # corp_code를 문자열로 변환 (8자리 제로패딩)
        if isinstance(corp_code, int):
            corp_code = str(corp_code).zfill(8)

        bgn_de = to_yyyymmdd(bgn_de)
        end_de = to_yyyymmdd(end_de)
        results: List[DisclosureMeta] = []

        for page_no in range(1, max_pages + 1):
            params = {
                "crtfc_key": self.api_key,
                "corp_code": corp_code,
                "bgn_de": bgn_de,
                "end_de": end_de,
                "page_no": page_no,
                "page_count": page_count,
                "last_reprt_at": last_reprt_at,
            }

            # simple retry with jitter
            for attempt in range(3):
                try:
                    r = self.session.get(f"{BASE_URL}/list.json", params=params, timeout=timeout)
                    if r.status_code == 200:
                        break
                    time.sleep((2 ** attempt) + random.random() * 0.3)
                except Exception:
                    if attempt == 2:
                        return results
                    time.sleep((2 ** attempt) + random.random() * 0.3)

            if r.status_code != 200:
                return results

            data = r.json()
            if data.get("status") != "000":
                return results

            items = data.get("list", []) or []
            for x in items:
                results.append(
                    DisclosureMeta(
                        rcept_no=x.get("rcept_no", ""),
                        rcept_dt=x.get("rcept_dt", ""),
                        corp_code=x.get("corp_code", ""),
                        corp_name=x.get("corp_name", ""),
                        report_nm=x.get("report_nm", ""),
                        flr_nm=x.get("flr_nm", ""),
                        rm=x.get("rm", ""),
                        pblntf_ty=x.get("pblntf_ty", ""),  # 공시유형 추가
                    )
                )

            if len(items) < page_count:
                break
            time.sleep(0.15)

        return results
