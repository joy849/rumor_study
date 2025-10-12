"""
이벤트 분류 헬퍼 함수들 (개선 버전)
"""
from __future__ import annotations
import logging
from typing import List, Tuple, Optional, Any
import functools

logger = logging.getLogger(__name__)


def safe_classify(
    default_return: Tuple = ([], 0.0, ""),
    log_prefix: str = "[CLASSIFY]",
    suppress_errors: bool = False
):
    """
    분류 함수에 대한 안전 실행 데코레이터

    Args:
        default_return: 에러 시 반환값
        log_prefix: 로그 접두사
        suppress_errors: True면 에러를 억제, False면 re-raise
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ImportError as e:
                logger.warning(f"{log_prefix} Module import failed in {func.__name__}: {e}")
                if not suppress_errors:
                    raise
                return default_return
            except AttributeError as e:
                logger.error(f"{log_prefix} Attribute error in {func.__name__}: {e}")
                if not suppress_errors:
                    raise
                return default_return
            except Exception as e:
                logger.error(f"{log_prefix} Unexpected error in {func.__name__}: {e}", exc_info=True)
                if not suppress_errors:
                    raise
                return default_return
        return wrapper
    return decorator


@safe_classify(default_return=([], 0.0, ""), log_prefix="[HCX]", suppress_errors=True)
def try_hyperclova_classify(
    classifier: Optional[Any],
    text: str
) -> Tuple[List[str], float, str]:
    """
    HyperCLOVA 분류 시도 (에러 처리 포함)

    Args:
        classifier: StockEventLabelClassifier 인스턴스
        text: 분류할 텍스트

    Returns:
        (labels, confidence, raw_response)

    Raises:
        ValueError: text가 비어있을 경우
    """
    if not text or not text.strip():
        raise ValueError("Empty text provided")

    if not classifier:
        logger.info("[HCX] Classifier not available")
        return [], 0.0, ""

    result = classifier.classify_event(text)

    # 안전한 속성 추출
    labels = getattr(result, "labels", None)
    if not isinstance(labels, list):
        logger.warning(f"[HCX] Invalid labels type: {type(labels)}")
        labels = []

    confidence = getattr(result, "confidence", 0.0)
    try:
        confidence = float(confidence)
        confidence = max(0.0, min(1.0, confidence))  # 범위 제한
    except (TypeError, ValueError):
        logger.warning(f"[HCX] Invalid confidence value: {confidence}")
        confidence = 0.0

    raw_response = str(getattr(result, "raw_response", ""))

    logger.info(f"[HCX] Success: labels={labels}, confidence={confidence:.2f}")
    return labels, confidence, raw_response


@safe_classify(default_return=([], 0.0, ""), log_prefix="[GPT]", suppress_errors=True)
def try_chatgpt_classify(text: str) -> Tuple[List[str], float, str]:
    """
    ChatGPT 분류 시도 (에러 처리 포함)

    Args:
        text: 분류할 텍스트

    Returns:
        (event_phrases, confidence, raw_response)

    Raises:
        ValueError: text가 비어있거나 API 키가 없을 경우
        ImportError: 필요한 모듈을 import할 수 없을 경우
    """
    import os

    if not text or not text.strip():
        raise ValueError("Empty text provided")

    if not os.getenv("OPENAI_API_KEY"):
        logger.debug("[GPT] OPENAI_API_KEY not set")
        raise ValueError("OPENAI_API_KEY not configured")

    from munci.lastsa.event_with_translate import classify_event_by_chatgpt

    result = classify_event_by_chatgpt(text)

    if not result or not isinstance(result, dict):
        logger.warning(f"[GPT] Invalid result type: {type(result)}")
        return [], 0.0, ""

    # 안전한 데이터 추출
    phrases = result.get("events")
    if not isinstance(phrases, list):
        logger.warning(f"[GPT] Invalid phrases type: {type(phrases)}")
        phrases = []

    confidence = result.get("confidence", 0.0)
    try:
        confidence = float(confidence)
        confidence = max(0.0, min(1.0, confidence))
    except (TypeError, ValueError):
        logger.warning(f"[GPT] Invalid confidence value: {confidence}")
        confidence = 0.0

    raw_response = str(result.get("raw_response", ""))

    logger.info(f"[GPT] Success: phrases={phrases}, confidence={confidence:.2f}")
    return phrases, confidence, raw_response


def merge_classification_results(
    hcx_result: Tuple[List[str], float, str],
    gpt_result: Tuple[List[str], float, str],
    prefer_source: str = "both"
) -> Tuple[List[str], List[str], float, str, str]:
    """
    HyperCLOVA와 ChatGPT 결과를 통합

    Args:
        hcx_result: (labels, confidence, raw_response)
        gpt_result: (phrases, confidence, raw_response)
        prefer_source: "hcx" | "gpt" | "both" 중 선호하는 소스

    Returns:
        (labels, phrases, confidence, combined_raw, source)
    """
    hcx_labels, hcx_conf, hcx_raw = hcx_result
    gpt_phrases, gpt_conf, gpt_raw = gpt_result

    hcx_valid = bool(hcx_labels and hcx_labels != ["other"])
    gpt_valid = bool(gpt_phrases)

    # 우선순위 결정
    if prefer_source == "hcx" and hcx_valid:
        return hcx_labels, [], hcx_conf, hcx_raw, "hyperclova"
    elif prefer_source == "gpt" and gpt_valid:
        return ["other"], gpt_phrases, gpt_conf, gpt_raw, "chatgpt"

    # 자동 선택
    if hcx_valid and gpt_valid:
        max_conf = max(hcx_conf, gpt_conf)
        combined_raw = f"HCX: {hcx_raw}\nGPT: {gpt_raw}"
        return hcx_labels, gpt_phrases, max_conf, combined_raw, "both"
    elif hcx_valid:
        return hcx_labels, [], hcx_conf, hcx_raw, "hyperclova"
    elif gpt_valid:
        return ["other"], gpt_phrases, gpt_conf, gpt_raw, "chatgpt"
    else:
        return ["other"], [], 0.0, "", "none"


# 통합 분류 함수
def classify_with_fallback(
    text: str,
    classifier: Optional[Any] = None,
    use_hcx: bool = True,
    use_gpt: bool = True
) -> Tuple[List[str], List[str], float, str]:
    """
    폴백 로직이 포함된 통합 분류

    Args:
        text: 분류할 텍스트
        classifier: HyperCLOVA 분류기 (선택)
        use_hcx: HyperCLOVA 사용 여부
        use_gpt: ChatGPT 사용 여부

    Returns:
        (labels, phrases, confidence, source)
    """
    if not text or not text.strip():
        logger.warning("[CLASSIFY] Empty text provided")
        return ["other"], [], 0.0, "none"

    hcx_result = ([], 0.0, "")
    gpt_result = ([], 0.0, "")

    if use_hcx:
        hcx_result = try_hyperclova_classify(classifier, text)

    if use_gpt:
        gpt_result = try_chatgpt_classify(text)

    labels, phrases, confidence, _, source = merge_classification_results(
        hcx_result, gpt_result
    )

    return labels, phrases, confidence, source
