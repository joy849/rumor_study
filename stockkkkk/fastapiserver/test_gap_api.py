"""괴리 API 테스트 스크립트"""
import requests
import json


def test_gap_check(stock_code: str, days: int = 3):
    """특정 종목의 괴리 확인"""
    url = f"http://localhost:8000/gaps/check/{stock_code}"
    params = {"days": days}
    
    print(f"\n{'='*60}")
    print(f"종목코드: {stock_code}, 조회기간: {days}일")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\n 응답 성공 (Status: {response.status_code})")
        print(f"\n결과:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        if data.get("has_gap"):
            print(f"\n 괴리 발견! 신호 개수: {data.get('gap_count')}")
            
            for signal in data.get("gap_signals", []):
                print(f"\n  - 이벤트: {signal.get('event_code')}")
                print(f"    방향: {signal.get('direction')}")
                print(f"    크기: {signal.get('magnitude')}")
                print(f"    Z-Score: {signal.get('z_score'):.2f}")
        else:
            print(f"\n✓ 괴리 없음")
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"\n 요청 실패: {e}")
        return None


def test_gap_list(days: int = 30):
    """괴리 목록 조회"""
    url = "http://localhost:8000/gaps/list"
    params = {
        "days": days,
        "min_z": 2.0,
        "limit": 20
    }
    
    print(f"\n{'='*60}")
    print(f"괴리 목록 조회 (최근 {days}일)")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\n 응답 성공 (Status: {response.status_code})")
        print(f"\n총 {data.get('total')}개 괴리 발견")
        
        for gap in data.get('gaps', [])[:5]:  # 상위 5개만 출력
            print(f"\n  종목: {gap.get('stock_name')} ({gap.get('stock_code')})")
            print(f"  이벤트: {gap.get('event_code')}")
            print(f"  날짜: {gap.get('news_date')}")
            print(f"  방향: {gap.get('direction')}, 크기: {gap.get('magnitude')}")
            print(f"  Z-Score: {gap.get('z_score'):.2f}")
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"\n 요청 실패: {e}")
        return None


def test_gap_stats(days: int = 30):
    """괴리 통계 조회"""
    url = "http://localhost:8000/gaps/stats"
    params = {"days": days}
    
    print(f"\n{'='*60}")
    print(f"괴리 통계 (최근 {days}일)")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"\n 응답 성공 (Status: {response.status_code})")
        print(f"\n통계:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"\n 요청 실패: {e}")
        return None


def test_multiple_stocks():
    """여러 종목 테스트 (DB에 있는 2025-09-30 데이터 기준)"""
    stock_codes = [
        ("019490", "역시큐어사이트론"),
        ("035420", "네이버"),
        ("101000", "KS인더스트리"),
        ("456160", "지투지비아이오"),
        ("210980", "SK디앤디"),
        ("008500", "알정산업"),
    ]
    
    results = {}
    
    for stock_code, stock_name in stock_codes:
        print(f"\n{'='*80}")
        print(f"테스트: {stock_name} ({stock_code})")
        print(f"{'='*80}")
        
        result = test_gap_check(stock_code, days=30)
        if result:
            results[stock_code] = result
    
    print(f"\n{'='*60}")
    print(f"전체 테스트 완료: {len(results)}/{len(stock_codes)} 성공")
    print(f"{'='*60}")
    
    return results


if __name__ == "__main__":
    # 1. 괴리 목록 조회
    print("\n" + "="*80)
    print("1. 괴리 목록 조회 테스트")
    print("="*80)
    test_gap_list(days=30)
    
    # 2. 괴리 통계 조회
    print("\n" + "="*80)
    print("2. 괴리 통계 조회 테스트")
    print("="*80)
    test_gap_stats(days=30)
    
    # 3. 개별 종목 테스트
    print("\n" + "="*80)
    print("3. 개별 종목 괴리 확인 테스트")
    print("="*80)
    test_multiple_stocks()
