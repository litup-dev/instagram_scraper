"""
가격 추출기 테스트
"""
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.parser.price_extractor import PriceExtractor

# ========== 테스트 코드 ==========

def test_price_extractor():
    """가격 추출기 테스트"""
    extractor = PriceExtractor()
    
    test_cases = [
        # 표준 패턴
        {
            'name': '표준 - 예매',
            'text': 'ADV 25,000원 / DOOR 30,000원',
            'expected': 25000
        },
        {
            'name': '표준 - Ticket',
            'text': 'Ticket: 20,000₩',
            'expected': 20000
        },
        {
            'name': '표준 - 입장료',
            'text': '입장료：15,000원',
            'expected': 15000
        },
        # 만원 패턴
        {
            'name': '만원 단위',
            'text': '예매 3만원 / 현장 4만원',
            'expected': 30000
        },
        {
            'name': '만원 - 숫자만',
            'text': '5만원',
            'expected': 50000
        },
        # 복합 패턴
        {
            'name': '복합 - clubbang',
            'text': '''<INDIE NIGHT>
2025.11.15 (FRI)
ADV 20,000원
DOOR 25,000원''',
            'expected': 20000
        },
        {
            'name': '복합 - unplugged',
            'text': '''Unplugged Live
티켓 정보:
예매 18,000원
현장 22,000원''',
            'expected': 18000
        },
        
        # 영문 표기
        {
            'name': '영문 - Cover',
            'text': 'Cover: 15,000 KRW',
            'expected': 15000
        },
        {
            'name': '영문 - Ticket',
            'text': 'Ticket 12,000won',
            'expected': 12000
        },
        
        # 쉼표 없는 패턴
        {
            'name': '쉼표 없음',
            'text': 'ADV 10000',
            'expected': 10000
        },
        
        # 무료 공연
        {
            'name': '무료 (추출 실패 예상)',
            'text': '입장료: 무료',
            'expected': None
        },
        
        # 가격 없음
        {
            'name': '가격 정보 없음',
            'text': '2025.11.15 공연',
            'expected': None
        },

        # 🎫 25,000 KRW
        {
            'name': '이모지 포함된 가격 정보',
            'text': '🎫 25,000 KRW',
            'expected': 25000
        },
    ]
    
    print("\n" + "=" * 70)
    print("가격 추출기 테스트".center(70))
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for i, case in enumerate(test_cases, 1):
        result = extractor.extract(case['text'])
        expected = case['expected']
        
        is_success = result == expected
        status = "✅ 성공" if is_success else "❌ 실패"
        
        print(f"\n[테스트 {i}] {case['name']}: {status}")
        print(f"  입력: {case['text'][:50]}...")
        print(f"  예상: {expected}원" if expected else "  예상: None")
        print(f"  결과: {result}원" if result else "  결과: None")
        
        if is_success:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"가격 테스트 결과: ✅ {passed}개 성공 / ❌ {failed}개 실패")
    print("=" * 70)


if __name__ == "__main__":
    test_price_extractor()