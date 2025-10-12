from __future__ import annotations
import os, json, logging, re
from typing import List, Dict, Tuple, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class SubGptCompanyExtractor:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
        self.translate_model = os.getenv("OPENAI_TRANSLATE_MODEL", "gpt-5-mini")
        self.post_translate_to = os.getenv("COMPANY_POST_TRANSLATE_TO")
        self._last_translated_companies = None

        self.alias2canon, self.canon2ticker = self._load_alias_index()

    def _load_alias_index(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        candidates = [os.getenv("COMPANY_ALIAS_PATH"), "config/normalized_aliases.json", "normalized_aliases.json"]
        for path in candidates:
            if not path: continue
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    alias2canon, canon2ticker = {}, {}
                    for key, values in data.items():
                        if not isinstance(values, list) or not values: continue
                        ticker = values[0] or ""
                        canonical = values[1] if len(values) > 1 and values[1] else key
                        canon2ticker.setdefault(canonical, ticker)
                        for alias in [key] + values:
                            alias2canon[alias.lower()] = canonical
                    return alias2canon, canon2ticker
                except Exception:
                    logger.warning("Failed to load alias dict from %s", path)
                    continue
        minimal = {
            "lg에너지솔루션": "LG에너지솔루션", "lges": "LG에너지솔루션",
            "삼성전자": "삼성전자", "samsung": "삼성전자",
            "sk하이닉스": "SK하이닉스", "하이닉스": "SK하이닉스",
            "현대차": "현대자동차", "현대자동차": "현대자동차",
            "테슬라": "Tesla", "tesla": "Tesla",
        }
        return minimal, {}

    def _translate(self, text: str, target_lang: Optional[str]) -> str:
        if not self.openai_client or not target_lang or not text:
            return ""
        try:
            resp = self.openai_client.chat.completions.create(
                model=self.translate_model,
                temperature=0,
                max_tokens=200,
                messages=[
                    {"role": "system",
                     "content": f"You are a professional translation engine. Translate into {target_lang}. Output only the translation. Keep official corporate names; do not hallucinate."},
                    {"role": "user", "content": text},
                ],
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception:
            logger.exception("company name translation failed")
            return ""

    def extract_by_chatgpt(self, text: str) -> List[str]:
        if not self.openai_client:
            return []
        try:
            SYSTEM_MSG = (
                "너는 한국 회사명 NER(고유명사 인식) 전문가다. "
                "반드시 한국어만 사용한다."
                "목표: 입력 텍스트에서 '한국어 공식 회사명'만 추출한다. "
                "출력은 반드시 JSON 배열(문자열만) 하나이며, 그 외 어떤 설명/코드블록/주석도 출력하지 않는다. "
                "중복을 제거하되 '처음 등장한 순서'를 유지한다. "
                "영문/약칭/티커는 한국어 정식 명칭으로 표준화하고, '주식회사/㈜/(주)/유한회사' 등 법형태 표기는 제거한다. "
                "그룹명 단독(삼성, LG, SK, 현대 등)은 제외하되, 지주/홀딩스가 공식 법인명인 경우는 포함한다(예: 롯데지주, 한화홀딩스). "
                "서비스·브랜드·제품명 단독은 제외한다(예: 삼성페이, 네이버쇼핑, 쿠팡이츠). 다만 명확한 독립 법인(예: 카카오페이, 쿠팡페이)은 포함한다. "
                "정부·공공기관·학교·협회·언론사·정당·국제기구 등 비영리는 제외한다. "
                "불확실하면 추측해 생성하지 말고 제외한다. "
                "빈 경우에는 반드시 []만 출력한다. "
            )

            user_prompt = f"""아래 텍스트에서 회사명을 추출하세요. '한국어 공식 명칭'만 반환합니다.

입력 텍스트:
{text}

추출 규칙:
1) 표준화
   - 영어/약칭/티커 → 한국어 정식 명칭
   - 법형태(주식회사/㈜/(주)/유한회사 등) 제거
2) 제외 규칙
   - 그룹명 단독 제외: 삼성, LG, SK, 현대 등
   - 서비스/브랜드/제품명 단독 제외
   - 공공·학교·협회·언론사 제외
3) 결과 구성
   - 중복 제거 + **최초 등장 순서 유지**
   - 불확실하면 제외

출력 형식:
- **오직 JSON 배열 문자열만** 출력
- 비어 있으면 **[]**만 출력

응답:"""

            messages = [
                {"role": "system", "content": SYSTEM_MSG},
                {"role": "user", "content": "아래 텍스트에서 회사명을 추출하세요.\n\n입력 텍스트:\nSamsung Electronics와 현대차\n\n출력 형식: JSON 배열만."},
                {"role": "assistant", "content": '["삼성전자", "현대자동차"]'},
                {"role": "user", "content": "아래 텍스트에서 회사명을 추출하세요.\n\n입력 텍스트:\n삼성·LG·SK와 협력\n\n출력 형식: JSON 배열만."},
                {"role": "assistant", "content": "[]"},
                {"role": "user", "content": user_prompt},
            ]

            resp = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                temperature=0,
                max_tokens=200,
            )

            content = (resp.choices[0].message.content or "").strip()
            logger.debug(f"GPT response: {content}")

            companies: List[str] = []
            if content.startswith("[") and content.endswith("]"):
                try:
                    companies = json.loads(content)
                except json.JSONDecodeError:
                    pass
            if not companies:
                match = re.search(r"\[[^\]]*\]", content)
                if match:
                    try:
                        companies = json.loads(match.group(0))
                    except json.JSONDecodeError:
                        items = [x.strip().strip('"').strip("'") for x in match.group(0)[1:-1].split(",")]
                        companies = [x for x in items if x]

            if not isinstance(companies, list):
                return []

            normalized: List[str] = []
            for c in companies:
                if isinstance(c, str):
                    name = c.strip()
                    if name:
                        normalized.append(name)

            if self.post_translate_to:
                try:
                    self._last_translated_companies = [
                        self._translate(n, self.post_translate_to) for n in normalized[:10]
                    ]
                except Exception:
                    logger.exception("post-translation step failed")
                    self._last_translated_companies = None
            return normalized[:10]
        except Exception as e:
            logger.exception("OpenAI company extraction failed: %s", e)
            return []

    def extract_by_alias_dict(self, text: str) -> List[str]:
        if not text:
            return []
        t = text.lower()
        found: List[str] = []
        variants = {t, t.replace(" ", ""), t.replace("-", "")}
        for token in sorted(self.alias2canon.keys(), key=len, reverse=True):
            for v in variants:
                if token in v:
                    found.append(self.alias2canon[token])
                    break
        uniq, seen = [], set()
        for c in found:
            if c not in seen:
                seen.add(c)
                uniq.append(c)
        return uniq

    def extract_companies(self, text: str) -> List[str]:
        if not text:
            return []

        results = {"chatgpt": [], "alias_dict": []}

        try:
            res = self.extract_by_chatgpt(text)
            if res:
                results["chatgpt"] = res
                logger.info(f"ChatGPT found: {res}")
        except Exception as e:
            logger.error(f"ChatGPT error: {e}")

        res = self.extract_by_alias_dict(text)
        if res:
            results["alias_dict"] = res
            logger.info(f"Alias dict found: {res}")

        all_companies = []
        seen = set()

        for company in results["chatgpt"]:
            if company not in seen:
                all_companies.append(company)
                seen.add(company)

        for company in results["alias_dict"]:
            if company not in seen:
                all_companies.append(company)
                seen.add(company)

        logger.debug(f"Final companies extracted: {all_companies[:5]}")
        return all_companies[:5]

    def get_last_translated_companies(self) -> Optional[list]:
        return self._last_translated_companies


_extractor: Optional[SubGptCompanyExtractor] = None


def initialize_extractor() -> SubGptCompanyExtractor:
    global _extractor
    if _extractor is None:
        _extractor = SubGptCompanyExtractor()
    return _extractor


def extract_companies(text: str) -> List[str]:
    return initialize_extractor().extract_companies(text)
