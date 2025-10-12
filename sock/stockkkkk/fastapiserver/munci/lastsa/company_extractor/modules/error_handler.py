"""
예외 처리 중앙 관리 모듈
모든 try-catch 로직을 이 파일에서 관리
"""
from __future__ import annotations
import re
from typing import Optional, List, Callable, Any, TypeVar

T = TypeVar('T')


def safe_compile_pattern(alias: str) -> Optional[re.Pattern]:
    """
    정규식 패턴 컴파일 (예외 처리)

    Args:
        alias: 회사명 또는 별칭

    Returns:
        컴파일된 패턴 또는 None (실패 시)
    """
    try:
        return re.compile(re.escape(alias), re.IGNORECASE)
    except Exception as e:
        print(f"[WARNING] Pattern compilation failed: {alias} - {e}")
        return None


def safe_pattern_finditer(pattern: re.Pattern, text: str) -> List[re.Match]:
    """
    정규식 매칭 실행 (예외 처리)

    Args:
        pattern: 컴파일된 정규식 패턴
        text: 검색할 텍스트

    Returns:
        매칭 결과 리스트 (실패 시 빈 리스트)
    """
    try:
        return list(pattern.finditer(text))
    except Exception as e:
        print(f"[WARNING] Pattern matching failed: {e}")
        return []


def safe_dict_get(dictionary: dict, key: str, default: Any = None) -> Any:
    """
    딕셔너리 조회 (예외 처리)

    Args:
        dictionary: 조회할 딕셔너리
        key: 키
        default: 기본값

    Returns:
        값 또는 기본값 (실패 시)
    """
    try:
        return dictionary.get(key, default)
    except Exception as e:
        print(f"[WARNING] Dictionary lookup failed: {key} - {e}")
        return default


def safe_list_get(lst: list, index: int, default: Any = None) -> Any:
    """
    리스트 조회 (예외 처리)

    Args:
        lst: 조회할 리스트
        index: 인덱스
        default: 기본값

    Returns:
        값 또는 기본값 (실패 시)
    """
    try:
        return lst[index] if 0 <= index < len(lst) else default
    except Exception as e:
        print(f"[WARNING] List access failed: index={index} - {e}")
        return default


def safe_execute(func: Callable[..., T], *args, default: T = None,
                 error_msg: str = "Function execution failed", **kwargs) -> T:
    """
    함수 실행 (예외 처리)

    Args:
        func: 실행할 함수
        *args: 함수 인자
        default: 실패 시 반환할 기본값
        error_msg: 에러 메시지
        **kwargs: 함수 키워드 인자

    Returns:
        함수 실행 결과 또는 기본값
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"[WARNING] {error_msg}: {e}")
        return default


def safe_json_load(file_path: str) -> Optional[dict]:
    """
    JSON 파일 로드 (예외 처리)

    Args:
        file_path: JSON 파일 경로

    Returns:
        JSON 데이터 또는 None
    """
    import json
    import os

    try:
        if not os.path.exists(file_path):
            print(f"[WARNING] File not found: {file_path}")
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"[WARNING] JSON parsing failed: {file_path} - {e}")
        return None
    except Exception as e:
        print(f"[WARNING] File load failed: {file_path} - {e}")
        return None


def safe_file_write(file_path: str, content: str) -> bool:
    """
    파일 쓰기 (예외 처리)

    Args:
        file_path: 파일 경로
        content: 쓸 내용

    Returns:
        성공 여부
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"[WARNING] File write failed: {file_path} - {e}")
        return False


def safe_string_similarity(s1: str, s2: str) -> float:
    """
    문자열 유사도 계산 (예외 처리)

    Args:
        s1, s2: 비교할 문자열

    Returns:
        유사도 (0.0 ~ 1.0) 또는 0.0 (실패 시)
    """
    try:
        from difflib import SequenceMatcher
        return SequenceMatcher(None, s1, s2).ratio()
    except Exception as e:
        print(f"[WARNING] Similarity calculation failed: {s1} vs {s2} - {e}")
        return 0.0
