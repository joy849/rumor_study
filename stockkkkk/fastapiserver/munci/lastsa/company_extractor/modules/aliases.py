from __future__ import annotations
from collections import defaultdict
from typing import Dict, List, Set, Optional
from . import utils, error_handler


def _merge_krx_aliases(extractor, path: str) -> None:
    """
    normalized_aliases.json 로드하여 회사 별칭 매핑 구축
    """
    # JSON 파일 로드 (예외 처리 포함)
    krx_data = error_handler.safe_json_load(path)
    if not krx_data:
        return

    # === krx_data의 각 회사 순회 ===
    # official_name = "삼성전자", "LG전자" 등
    # aliases_list = ["005930", "삼성전자", "삼성", "Samsung"]
    for official_name, aliases_list in krx_data.items():
        if not isinstance(aliases_list, list) or len(aliases_list) == 0:
            continue

        # === 1단계: 종목코드와 별칭 분리 ===
        ticker, aliases = _parse_krx_aliases(aliases_list)
        # ticker = "005930"
        # aliases = ["삼성전자", "삼성", "Samsung"]

        # === 2단계: company_master에 등록 & 별칭 매핑 구축 ===
        _register_company(extractor, official_name, ticker, aliases)
        # - extractor.company_master["삼성전자"] 등록됨
        # - extractor.company_aliases["삼성전자"] = ["삼성전자", "삼성", "Samsung"]
        # - extractor.alias_to_official["삼성"] = "삼성전자"
        # - extractor.alias_to_official["Samsung"] = "삼성전자"


def _parse_krx_aliases(aliases_list: List[str]) -> tuple[Optional[str], List[str]]:
    """
    KRX aliases 리스트에서 종목코드와 별칭 분리

    입력: ["005930", "삼성전자", "삼성", "Samsung"]
    출력: ("005930", ["삼성전자", "삼성", "Samsung"])

    종목코드 조건: 숫자 6자리
    """
    ticker = None
    aliases = []

    for item in aliases_list:
        if item.isdigit() and len(item) == 6:
            # 숫자 6자리 → 종목코드
            ticker = item
        else:
            # 나머지 → 별칭
            aliases.append(item)

    return ticker, aliases


def _register_company(extractor, official_name: str, ticker: Optional[str], aliases: List[str]) -> None:
    """
    회사를 company_master에 등록하고 별칭 매핑 구축

    예시 입력:
    - official_name = "삼성전자"
    - ticker = "005930"
    - aliases = ["삼성전자", "삼성", "Samsung"]

    처리:
    1. extractor.company_master에 회사 정보 등록
    2. extractor.company_aliases에 별칭 리스트 저장
    3. extractor.alias_to_official에 역매핑 저장
    """

    # === 1. company_master에 등록 ===
    if official_name not in extractor.company_master:
        extractor.company_master[official_name] = {
            "code": ticker,  # "005930"
            "name": official_name,  # "삼성전자"
            "market": "KRX",
            "length": len(official_name),
            "type": "listed",
            "verified": True
        }
        # extractor.company_master["삼성전자"] = {"code": "005930", ...}

    # === 2. company_aliases에 별칭 병합 ===
    existing_aliases: Set[str] = set(extractor.company_aliases.get(official_name, []))
    # existing_aliases = set()  (처음이라면 빈 set)

    existing_aliases.update(aliases)
    # existing_aliases = {"삼성전자", "삼성", "Samsung"}

    existing_aliases.add(official_name)
    # existing_aliases = {"삼성전자", "삼성", "Samsung"}  (이미 포함)

    extractor.company_aliases[official_name] = list(existing_aliases)
    # extractor.company_aliases["삼성전자"] = ["삼성전자", "삼성", "Samsung"]

    # === 3. alias_to_official에 역매핑 구축 ===
    for alias in aliases:
        extractor.alias_to_official[alias] = official_name
    # extractor.alias_to_official["삼성"] = "삼성전자"
    # extractor.alias_to_official["Samsung"] = "삼성전자"

    # 이제 텍스트에서 "삼성" 또는 "Samsung"을 발견하면
    # → alias_to_official로 "삼성전자"로 정규화 가능!


def _build_enhanced_company_aliases(extractor) -> Dict[str, List[str]]:
    """
    회사명에서 자동으로 별칭 생성 (규칙 기반)

    처리 과정:
    1. extractor.company_master의 모든 회사 순회
    2. 접미사 규칙 적용하여 별칭 생성
       - "삼성전자" → "삼성" 추가
       - "현대자동차" → "현대", "현대차" 추가
       - "삼성홀딩스" → "삼성" 추가
    3. extractor.company_aliases에 저장
    4. extractor.alias_to_official에 역매핑 저장

    예시:
    입력: company_master에 "삼성전자", "현대자동차" 존재
    출력:
    - company_aliases["삼성전자"] = ["삼성전자", "삼성"]
    - company_aliases["현대자동차"] = ["현대자동차", "현대", "현대차"]
    - alias_to_official["삼성"] = "삼성전자"
    - alias_to_official["현대"] = "현대자동차"
    - alias_to_official["현대차"] = "현대자동차"
    """
    aliases = extractor.company_aliases if hasattr(extractor, 'company_aliases') else defaultdict(list)

    # === 접미사 규칙 정의 ===
    suffix_rules = {
        "전자": _create_electronics_aliases,  # "삼성전자" → ["삼성"]
        "자동차": _create_automotive_aliases,  # "현대자동차" → ["현대", "현대차"]
        "홀딩스": _create_holding_aliases,  # "삼성홀딩스" → ["삼성"]
    }

    # === company_master의 모든 회사 순회 ===
    for company_name in extractor.company_master.keys():
        # company_name = "삼성전자", "현대자동차", "네이버" 등

        # 기본 별칭 초기화 (자기 자신)
        if company_name not in aliases:
            aliases[company_name] = []
        if company_name not in aliases[company_name]:
            aliases[company_name].append(company_name)
        # aliases["삼성전자"] = ["삼성전자"]

        # === 접미사 규칙 적용 ===
        for suffix, rule_func in suffix_rules.items():
            if suffix in company_name:
                # "전자"가 "삼성전자"에 포함됨
                new_aliases = rule_func(company_name, suffix)
                # new_aliases = ["삼성"]

                _add_aliases(extractor, company_name, aliases, new_aliases)
                # aliases["삼성전자"] = ["삼성전자", "삼성"]
                # alias_to_official["삼성"] = "삼성전자"

    # === 중복 제거 ===
    for company in aliases:
        aliases[company] = list(set(aliases[company]))

    print(f"[OK] Total {len(extractor.alias_to_official)} alias mappings built")
    # extractor.alias_to_official = {
    #     "삼성": "삼성전자",
    #     "Samsung": "삼성전자",
    #     "현대": "현대자동차",
    #     "현대차": "현대자동차",
    #     ...
    # }

    return dict(aliases)


def _create_electronics_aliases(company_name: str, suffix: str) -> List[str]:
    """
    전자 회사 별칭 생성

    입력: company_name="삼성전자", suffix="전자"
    처리: "삼성전자".replace("전자", "") = "삼성"
    출력: ["삼성"]
    """
    base = company_name.replace(suffix, "")
    return [base] if len(base) > 1 else []


def _create_automotive_aliases(company_name: str, suffix: str) -> List[str]:
    """
    자동차 회사 별칭 생성

    입력: company_name="현대자동차", suffix="자동차"
    처리:
      - "현대자동차".replace("자동차", "") = "현대"
      - "현대" + "차" = "현대차"
    출력: ["현대", "현대차"]
    """
    base = company_name.replace(suffix, "")
    if len(base) <= 1:
        return []

    aliases = [base]  # ["현대"]
    base_with_cha = base + "차"  # "현대차"
    aliases.append(base_with_cha)  # ["현대", "현대차"]
    return aliases


def _create_holding_aliases(company_name: str, suffix: str) -> List[str]:
    """
    홀딩스 회사 별칭 생성

    입력: company_name="삼성홀딩스", suffix="홀딩스"
    처리: "삼성홀딩스".replace("홀딩스", "") = "삼성"
    출력: ["삼성"]
    """
    base = company_name.replace(suffix, "")
    return [base] if len(base) > 1 else []


def _add_aliases(extractor, official_name: str, aliases_dict: Dict, new_aliases: List[str]) -> None:
    """
    별칭을 추가하고 역매핑 구축

    예시 입력:
    - official_name = "삼성전자"
    - aliases_dict = {"삼성전자": ["삼성전자"]}
    - new_aliases = ["삼성"]

    처리:
    1. aliases_dict["삼성전자"]에 "삼성" 추가
    2. alias_to_official["삼성"] = "삼성전자" 저장
    """
    for alias in new_aliases:
        if alias not in aliases_dict[official_name]:
            # aliases_dict에 별칭 추가
            aliases_dict[official_name].append(alias)
            # aliases_dict["삼성전자"] = ["삼성전자", "삼성"]

            # 역매핑 저장
            extractor.alias_to_official[alias] = official_name
            # alias_to_official["삼성"] = "삼성전자"


def _normalize_to_official_name(extractor, company: str) -> str:
    """
    별칭을 정식 회사명으로 변환

    우선순위:
    1. alias_to_official 직접 매핑 확인
    2. company_master에 직접 존재하는지 확인
    3. 유사도 기반 매칭 (0.9 이상)

    예시:
    입력: company="삼성"
    처리:
      1. alias_to_official["삼성"] = "삼성전자" 발견!
    출력: "삼성전자"

    입력: company="삼성전자"
    처리:
      1. alias_to_official에 없음
      2. company_master["삼성전자"] 존재!
    출력: "삼성전자"
    """
    # 1순위: alias_to_official에서 찾기
    if company in extractor.alias_to_official:
        return extractor.alias_to_official[company]
        # "삼성" → "삼성전자" 변환

    # 2순위: company_master에 직접 존재
    if company in extractor.company_master:
        return company
        # "삼성전자" → "삼성전자" (그대로)

    # 3순위: 유사도 기반 매칭
    for official in extractor.company_master.keys():
        similarity = utils._calculate_string_similarity(company, official)
        if similarity > 0.9:
            return official
            # "삼성전가" → "삼성전자" (오타 보정)

    # 매칭 실패 시 원본 반환
    return company


def _find_similar_companies(extractor, company: str, threshold: float = 0.8) -> List[str]:
    """
    유사한 회사명 찾기 (최대 3개)

    예시:
    입력: company="삼성", threshold=0.8
    처리:
      - "삼성전자"와 유사도 0.85 → 추가
      - "삼성SDI"와 유사도 0.82 → 추가
      - "삼성생명"와 유사도 0.81 → 추가
    출력: ["삼성전자", "삼성SDI", "삼성생명"]
    """
    similar = []

    for master_company in extractor.company_master.keys():
        similarity = utils._calculate_string_similarity(company, master_company)
        if similarity >= threshold:
            similar.append(master_company)

    return similar[:3]  # 최대 3개만 반환
