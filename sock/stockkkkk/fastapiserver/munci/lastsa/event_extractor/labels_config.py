# -*- coding: utf-8 -*-
"""
labels_config.py
- LABEL_REGISTRY_BASE: 라벨 메타(세분 여부, 기본 priority, 정규식 트리거)
- PRIORITY_PROFILES: 상황별 우선순위 덮어쓰기(필요 시만 적용)
- get_registry(profile): 기본 레지스트리에 프로파일을 적용한 사본 반환
"""

from copy import deepcopy

# =========================
# 기본 레지스트리 (SSOT)
# =========================
LABEL_REGISTRY_BASE = {
    # ---------- Flow ----------
    "flow.trading_resumption": {"fine": True,  "priority": 160, "triggers": [r"(거래|매매)\s*(재개|재개\s*공시)"]},
    "flow.trading_halt_cb":    {"fine": False, "priority": 300, "triggers": [r"(매매|거래)\s*정지", r"\bVI\b", r"(서킷|써킷)\s*브레이커"]},
    "flow.index_inout":        {"fine": False, "priority": 217, "triggers": [r"(편입|편출).*(코스피200|코스닥150|KOSPI|MSCI|FTSE|정기\s*변경|리밸런싱)"]},
    "flow.options_expiry":     {"fine": False, "priority": 320, "triggers": []},

    # ---------- Company (세분) ----------
    # M&A cycle
    "company.mna_letter_of_intent":     {"fine": True, "priority": 110, "triggers": [r"\bLOI\b", r"\bMOU\b", r"인수\s*의향서", r"양해각서", r"조건부?\s*합의", r"프레임워크\s*협약"]},
    "company.mna_binding_agreement":    {"fine": True, "priority": 111, "triggers": [r"\bSPA\b", r"본\s*계약\s*체결", r"최종\s*계약", r"주식\s*매매\s*계약"]},
    "company.mna_regulatory_clearance": {"fine": True, "priority": 112, "triggers": [r"(공정위|공정거래위원회|FTC|EC|SAMR).*(승인|심사\s*통과|클리어런스)"]},
    "company.mna_termination":          {"fine": True, "priority": 113, "triggers": [r"(딜|거래|합병|인수).*(해지|무산|종료|철회|termination)"]},

    # Equity/Lockup/Stock option
    "company.major_shareholder_change":    {"fine": True, "priority": 124, "triggers": [r"(최대\s*주주|지배\s*주주).*(변경|교체)"]},
    "company.share_pledge_change":         {"fine": True, "priority": 125, "triggers": [r"(질권|담보).*(설정|해지)"]},
    "company.lockup_expiry":               {"fine": True, "priority": 120, "triggers": [r"(보호\s*예수|락업).*(해제|만료)"]},
    "company.stock_option_grant":          {"fine": True, "priority": 122, "triggers": [r"스톡\s*옵션.*(부여|grant)"]},
    "company.stock_option_exercise":       {"fine": True, "priority": 123, "triggers": [r"스톡\s*옵션.*(행사|exercise)"]},
    "company.treasury_share_cancellation": {"fine": True, "priority": 121, "triggers": [r"(자사주|자기주식).*(소각|말소)"]},

    # Finance/Credit
    "company.debt_restructuring":    {"fine": True, "priority": 130, "triggers": [r"(리파이낸싱|재조정|재무\s*구조\s*개선|만기\s*연장)"]},
    "company.covenant_waiver":       {"fine": True, "priority": 131, "triggers": [r"(재무\s*약정|코버넌트).*(면제|유예|waiver)"]},
    "company.rating_watch_outlook":  {"fine": True, "priority": 132, "triggers": [r"(관찰\s*대상|Watch|전망|Outlook).*(상향|하향|부여|변경)"]},
    "company.early_redemption_call": {"fine": True, "priority": 133, "triggers": [r"(조기\s*상환|콜\s*옵션\s*행사|early\s*redemption|call)"]},

    # Operations/Facility/Safety
    "company.capex_expansion":            {"fine": True, "priority": 140, "triggers": [r"(대규모|대형)\s*(설비|공장|fab|라인).*(증설|투자|capex|CAPEX|확대)"]},
    "company.plant_shutdown_maintenance": {"fine": True, "priority": 141, "triggers": [r"(정기\s*보수|셧\s*다운|shutdown|가동\s*중단)"]},
    "company.plant_restart_rampup":      {"fine": True, "priority": 142, "triggers": [r"(재\s*가동|가동\s*재개|램프\s*업|ramp[\s-]*up)"]},
    "company.operational_incident":       {"fine": True, "priority": 143, "triggers": [r"(화재|폭발|누출|정전|침수|사고|사망|부상)"]},
    "company.service_launch_termination": {"fine": True, "priority": 144, "triggers": [r"(서비스|상품|플랫폼).*(출시|론칭|종료|단종|terminate)"]},

    # Legal/Regulatory
    "company.regulatory_sanction_fine":     {"fine": True,  "priority": 150, "triggers": [r"(과징금|행정\s*제재|고발|징계).*(부과|처분|확정)"]},
    "company.litigation_filed":             {"fine": True,  "priority": 151, "triggers": [r"(소송|집단\s*소송|소제기|제소|complaint\s*filed)"]},
    "company.litigation_outcome":           {"fine": True,  "priority": 152, "triggers": [r"(판결|합의|소취하|승소|패소|일부승소|settlement|verdict)"]},
    "company.violation_of_law":             {"fine": False, "priority": 218, "triggers": [r"(구속|압수수색|기소|수사|위법|혐의)"]},
    "company.whistleblowing_investigation": {"fine": False, "priority": 180, "triggers": [r"(내부\s*고발|제보)", r"(내부\s*조사|감사)\s*(개시|착수)"]},
    "company.labor_strike_negotiation":     {"fine": False, "priority": 106, "triggers": [r"(파업|쟁의|단체\s*행동|노조)", r"(교섭|협상|중재)"]},

    # Listing/Trading status
    "company.delisting_watch": {"fine": True, "priority": 161, "triggers": [r"(관리\s*종목|상장\s*폐지|상폐).*(사유|통지|우려|리스크)"]},

    # ---------- Company (포괄) ----------
    "company.mna_deal":            {"fine": False, "priority": 210, "triggers": [r"(인수|합병|M&A|지분\s*인수|경영권\s*인수)"]},
    "company.big_contract_update": {"fine": False, "priority": 211, "triggers": [r"(공급\s*계약|납품\s*계약|장기\s*공급|대규모\s*계약|수주)"]},
    "company.stock_split":         {"fine": False, "priority": 212, "triggers": [r"(액면\s*분할|주식\s*분할|역\s*분할)"]},
    "company.earnings_result":     {"fine": False, "priority": 213, "triggers": [r"(실적|영업익|매출|순이익|흑자|적자|컨센서스)"]},
    "company.guidance_update":     {"fine": False, "priority": 214, "triggers": [r"(가이던스|전망|가이드).*(상향|하향|조정)"]},

    # ---------- Sector ----------
    # Semiconductor
    "sector.semicon_node_transition":   {"fine": False, "priority": 215, "triggers": [r"(HBM|양산|수율|노드|nm|공정)"]},
    "sector.semicon_tapeout":           {"fine": True,  "priority": 180, "triggers": [r"(테이프\s*아웃|tape[-\s]*out)"]},
    "sector.semicon_qualification_pass":{"fine": True,  "priority": 181, "triggers": [r"(퀄|qualification|인증|검증).*(통과|승인)"]},
    "sector.semicon_capacity_commit":   {"fine": True,  "priority": 182, "triggers": [r"(capacity|캐파|CAPA|증설).*(커밋|commit|장기\s*공급)"]},
    "sector.semicon_capex_yield":       {"fine": False, "priority": 366, "triggers": []},

    # Biotech
    "sector.biotech_clinical_result":        {"fine": False, "priority": 220, "triggers": []},
    "sector.biotech_regulatory":             {"fine": False, "priority": 216, "triggers": [r"(FDA|EMA|허가|승인)"]},
    "sector.biotech_ind_clearance":          {"fine": True,  "priority": 170, "triggers": [r"\bIND\b.*(승인|접수|허가)"]},
    "sector.biotech_nda_bla_filing":         {"fine": True,  "priority": 171, "triggers": [r"\b(NDA|BLA)\b.*(제출|접수|filing)"]},
    "sector.biotech_pdufa_set":              {"fine": True,  "priority": 172, "triggers": [r"\bPDUFA\b.*(일|데드라인|타깃|목표\s*일)"]},
    "sector.biotech_fasttrack_designation":  {"fine": True,  "priority": 173, "triggers": [r"(Fast[-\s]*Track|가속\s*승인|희귀\s*의약품|Orphan)\s*(지정|승인)"]},
    "sector.biotech_trial_enrollment_complete":{"fine": True,"priority": 174, "triggers": [r"(등록|모집).*(완료|마감)"]},
    "sector.biotech_primary_endpoint_result": {"fine": True, "priority": 175, "triggers": [r"(주\s*평가\s*지표|Primary\s*Endpoint).*(달성|충족|실패|미달성)"]},
    "sector.biotech_clinical_hold_lifted":   {"fine": True, "priority": 176, "triggers": [r"(임상).*(중지|보류|Hold).*(해제|Lifted)"]},

    # 기타 섹터
    "sector.retail_sssg_inventory":         {"fine": False, "priority": 360, "triggers": []},
    "sector.software_saas_metrics":         {"fine": False, "priority": 361, "triggers": []},
    "sector.energy_oil_gas":                {"fine": False, "priority": 362, "triggers": []},
    "sector.shipping_freight_index":        {"fine": False, "priority": 363, "triggers": []},
    "sector.financial_nim_provision_capital":{"fine": False, "priority": 364, "triggers": []},
    "sector.auto_ev_policy_recall":         {"fine": False, "priority": 365, "triggers": []},

    # ---------- Calendar ----------
    "calendar.earnings_date":             {"fine": False, "priority": 380, "triggers": []},
    "calendar.dividend_dates":            {"fine": False, "priority": 381, "triggers": []},
    "calendar.options_expiry_date":       {"fine": False, "priority": 382, "triggers": []},
    "calendar.index_rebalance_effective": {"fine": False, "priority": 383, "triggers": []},
    "calendar.lockup_expiration":         {"fine": False, "priority": 384, "triggers": []},
    "calendar.investor_day_ndr":          {"fine": False, "priority": 385, "triggers": []},
    "calendar.shareholder_meeting":       {"fine": False, "priority": 386, "triggers": []},

    # ---------- KRX ----------
    "krx.shortselling_ban_toggle": {"fine": False, "priority": 400, "triggers": []},
    "krx.short_sale_hot_stock":    {"fine": False, "priority": 401, "triggers": []},
    "krx.single_price_auction":    {"fine": False, "priority": 402, "triggers": []},
    "krx.watchlist_designation":   {"fine": False, "priority": 403, "triggers": []},
    "krx.query_disclosure":        {"fine": False, "priority": 404, "triggers": []},
    "krx.unfaithful_disclosure":   {"fine": False, "priority": 405, "triggers": []},
    "krx.delisting_notice":        {"fine": False, "priority": 406, "triggers": []},
    "krx.trading_halt_vi":         {"fine": False, "priority": 407, "triggers": []},

    # ---------- Analyst ----------
    "analyst.target_price": {"fine": False, "priority": 450, "triggers": []},
    "analyst.rating_change": {"fine": False, "priority": 451, "triggers": []},
    "analyst.report":        {"fine": False, "priority": 452, "triggers": []},
    "analyst.conference":    {"fine": False, "priority": 453, "triggers": []},

    # ---------- Capital/Debt 추가 ----------
    "company.capital_increase_rights":  {"fine": False, "priority": 339, "triggers": [r"유상\s*증자", r"신주\s*발행", r"제3자\s*배정"]},
    "company.bonus_issue":              {"fine": False, "priority": 340, "triggers": [r"무상\s*증자"]},
    "company.capital_reduction":        {"fine": False, "priority": 341, "triggers": []},
    "company.capital_increase_mixed":   {"fine": False, "priority": 342, "triggers": []},
    "company.at1_issue":                {"fine": False, "priority": 343, "triggers": []},
    "company.convertible_bond_issue":   {"fine": False, "priority": 344, "triggers": []},
    "company.bw_issue":                 {"fine": False, "priority": 345, "triggers": []},
    "company.exchangeable_bond_issue":  {"fine": False, "priority": 346, "triggers": []},

    # ---------- M&A/분할/교환 ----------
    "company.mna_merger":              {"fine": False, "priority": 347, "triggers": []},
    "company.share_exchange_transfer": {"fine": False, "priority": 348, "triggers": []},
    "company.split_merger":            {"fine": False, "priority": 349, "triggers": []},
    "company.listing_overseas":        {"fine": False, "priority": 350, "triggers": [r"해외\s*(상장|상장\s*추진)", r"(NYSE|NASDAQ|LSE|HKEX).*(상장|listing)"]},

    # ---------- 영업/자산/지분 ----------
    "company.business_acquisition":       {"fine": False, "priority": 351, "triggers": []},
    "company.business_disposal":          {"fine": False, "priority": 352, "triggers": []},
    "company.tangible_asset_acquisition": {"fine": False, "priority": 353, "triggers": []},
    "company.tangible_asset_disposal":    {"fine": False, "priority": 354, "triggers": []},
    "company.equity_acquisition":         {"fine": False, "priority": 355, "triggers": []},
    "company.equity_disposal":            {"fine": False, "priority": 356, "triggers": []},
    "company.security_bond_rights_acq":   {"fine": False, "priority": 357, "triggers": []},
    "company.security_bond_rights_disp":  {"fine": False, "priority": 358, "triggers": []},
    "company.asset_transaction_misc":     {"fine": False, "priority": 359, "triggers": []},
    "company.putback_option":             {"fine": False, "priority": 360, "triggers": []},

    # ---------- Buyback ----------
    "company.buyback_acquire":          {"fine": False, "priority": 361, "triggers": []},
    "company.buyback_dispose":          {"fine": False, "priority": 362, "triggers": []},
    "company.buyback_trust_sign":       {"fine": False, "priority": 363, "triggers": []},
    "company.buyback_trust_terminate":  {"fine": False, "priority": 364, "triggers": []},

    # ---------- Distress ----------
    "company.default_event":        {"fine": False, "priority": 365, "triggers": []},
    "company.business_suspension":  {"fine": False, "priority": 366, "triggers": []},
    "company.rehabilitation_apply": {"fine": False, "priority": 367, "triggers": []},
    "company.dissolution_cause":    {"fine": False, "priority": 368, "triggers": []},

    # ---------- 기타 ----------
    "company.preannouncement_warning": {"fine": False, "priority": 305, "triggers": []},
    "company.dividend_change":        {"fine": False, "priority": 306, "triggers": []},
    "company.convertible_pref_update":{"fine": False, "priority": 310, "triggers": []},
    "company.management_change":      {"fine": False, "priority": 312, "triggers": []},
    "company.insider_transaction":    {"fine": False, "priority": 313, "triggers": []},
    "company.product_pricing_update": {"fine": False, "priority": 314, "triggers": []},
    "company.supply_chain_disruption":{"fine": False, "priority": 315, "triggers": []},
    "company.accounting_audit_issue": {"fine": False, "priority": 316, "triggers": []},
    "company.litigation_regulatory":  {"fine": False, "priority": 317, "triggers": []},
    "company.esg_labor_incident":     {"fine": False, "priority": 318, "triggers": []},
    "company.dart_correction":        {"fine": False, "priority": 319, "triggers": []},
    "company.credit_rating_change":   {"fine": False, "priority": 321, "triggers": []},
    "company.product_safety_recall":  {"fine": False, "priority": 322, "triggers": []},
    "company.data_breach":            {"fine": False, "priority": 323, "triggers": []},

    # Fallback
    "other": {"fine": False, "priority": 10**6, "triggers": []},
}

# =========================
# 우선순위 프로파일(우선순위만 덮어쓰기)
# =========================
PRIORITY_PROFILES = {
    "intraday_kr": {
        # 거래/생존
        "flow.trading_resumption": 10,
        "company.operational_incident": 12,
        "company.default_event": 14,
        "company.business_suspension": 16,
        "company.rehabilitation_apply": 18,
        "krx.delisting_notice": 20,
        "company.delisting_watch": 22,
        "krx.watchlist_designation": 24,
        "krx.trading_halt_vi": 26,
        "flow.trading_halt_cb": 27,

        # M&A
        "company.mna_binding_agreement": 30,
        "company.mna_merger": 31,
        "company.mna_termination": 32,
        "company.share_exchange_transfer": 33,
        "company.split_merger": 35,
        "company.mna_regulatory_clearance": 36,
        "company.mna_letter_of_intent": 38,
        "company.mna_deal": 39,

        # 자본/주식 구조
        "company.capital_increase_rights": 50,
        "company.capital_reduction": 52,
        "company.at1_issue": 54,
        "company.convertible_bond_issue": 56,
        "company.exchangeable_bond_issue": 57,
        "company.bw_issue": 58,
        "company.buyback_acquire": 60,
        "company.buyback_trust_sign": 61,
        "company.buyback_dispose": 62,
        "company.buyback_trust_terminate": 63,
        "company.stock_split": 65,
        "company.bonus_issue": 68,

        # 계약/설비/자산
        "company.big_contract_update": 70,
        "company.capex_expansion": 72,
        "sector.semicon_capacity_commit": 73,
        "company.business_acquisition": 74,
        "company.business_disposal": 75,
        "company.tangible_asset_acquisition": 76,
        "company.tangible_asset_disposal": 77,
        "company.listing_overseas": 78,
        "flow.index_inout": 79,

        # 운영(정기)/서비스
        "company.plant_shutdown_maintenance": 95,
        "company.plant_restart_rampup": 96,
        "company.service_launch_termination": 98,
        "company.labor_strike_negotiation": 106,

        # 실적/가이던스/신용
        "company.earnings_result": 100,
        "company.guidance_update": 101,
        "company.credit_rating_change": 104,
        "company.rating_watch_outlook": 105,

        # 바이오
        "sector.biotech_primary_endpoint_result": 110,
        "sector.biotech_regulatory": 112,
        "sector.biotech_clinical_hold_lifted": 114,
        "sector.biotech_nda_bla_filing": 118,
        "sector.biotech_ind_clearance": 119,
        "sector.biotech_pdufa_set": 122,
        "sector.biotech_trial_enrollment_complete": 126,

        # 반도체
        "sector.semicon_node_transition": 130,
        "sector.semicon_tapeout": 131,
        "sector.semicon_qualification_pass": 132,

        # 법무/규제 일반
        "company.violation_of_law": 170,
        "company.regulatory_sanction_fine": 172,
        "company.litigation_outcome": 174,
        "company.litigation_filed": 176,
        "company.data_breach": 178,
        "company.product_safety_recall": 179,
        "company.whistleblowing_investigation": 180,

        # 캘린더/섹터지표
        "flow.options_expiry": 320,
        "calendar.earnings_date": 330,
        "calendar.dividend_dates": 331,
        "calendar.options_expiry_date": 332,
        "calendar.index_rebalance_effective": 333,
        "calendar.lockup_expiration": 334,
        "calendar.investor_day_ndr": 335,
        "calendar.shareholder_meeting": 336,
        "sector.retail_sssg_inventory": 360,
        "sector.software_saas_metrics": 361,
        "sector.energy_oil_gas": 362,
        "sector.shipping_freight_index": 363,
        "sector.financial_nim_provision_capital": 364,
        "sector.auto_ev_policy_recall": 365,
        "sector.semicon_capex_yield": 366,
        "krx.shortselling_ban_toggle": 380,
    },
    # 필요 시 다른 프로파일 추가 가능
}

def get_registry(profile: str | None = None) -> dict:
    """기본 레지스트리에 프로파일 우선순위를 덮어씌운 사본을 반환"""
    reg = deepcopy(LABEL_REGISTRY_BASE)
    if profile:
        patch = PRIORITY_PROFILES.get(profile)
        if patch:
            for k, v in patch.items():
                if k in reg:
                    reg[k]["priority"] = int(v)
    return reg
