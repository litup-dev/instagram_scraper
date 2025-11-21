"""
가격 추출기 테스트
"""
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.parser.price_extractor import PriceExtractor
from scraper.instagram_scraper import InstagramScraper
from utils.logger import setup_logger
import json

logger = setup_logger('test_price_extractor')

def test_post_url(post_url: str):
    """게시물 URL로 가격 정보 테스트"""
    try:
        logger.info(f"🔍 게시물 테스트: {post_url}")
        
        scraper = InstagramScraper()
        extractor = PriceExtractor()
        
        # URL에서 media_pk 추출
        media_pk = scraper.client.media_pk_from_url(post_url)
        media = scraper.client.media_info(media_pk)
        
        caption = media.caption_text or ''
        
        print("\n" + "="*80)
        print("📋 게시물 정보")
        print("="*80)
        print(f"🔗 게시물 URL: {post_url}")
        print(f"👤 사용자: @{media.user.username}")
        print(f"\n📝 Caption :\n{caption}...")
        
        # 가격 추출
        result = extractor.extract(caption)
        
        print("\n" + "="*80)
        print("💰 가격 추출 결과")
        print("="*80)
        print(json.dumps({
            'booking_price': result.get('booking_price'),
            'onsite_price': result.get('onsite_price'),
            'booking_price_formatted': f"{result.get('booking_price'):,}원" if result.get('booking_price') else "없음",
            'onsite_price_formatted': f"{result.get('onsite_price'):,}원" if result.get('onsite_price') else "없음"
        }, ensure_ascii=False, indent=2))
        print("="*80)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


# ========== 테스트 코드 ==========

def test_price_extractor():
    """가격 추출기 테스트"""
    extractor = PriceExtractor()
    
    test_cases = [
        # 표준 패턴 (booking, onsite)
        {
            'name': '표준 - 예매',
            'text': 'ADV 25,000원 / DOOR 30,000원',
            'expected': {'booking_price': 25000, 'onsite_price': 30000}
        },
        {
            'name': '표준 - Ticket',
            'text': 'Ticket: 20,000₩',
            'expected': {'booking_price': 20000, 'onsite_price': None}
        },
        {
            'name': '표준 - 입장료',
            'text': '입장료：15,000원',
            'expected': {'booking_price': 15000, 'onsite_price': None}
        },
        # 만원 패턴
        {
            'name': '만원 단위',
            'text': '예매 3만원 / 현장 4만원',
            'expected': {'booking_price': 30000, 'onsite_price': 40000}
        },
        {
            'name': '만원 - 숫자만',
            'text': '5만원',
            'expected': {'booking_price': 50000, 'onsite_price': None}
        },
        # 복합 패턴
        {
            'name': '복합 - clubbang',
            'text': '''<INDIE NIGHT>
2025.11.15 (FRI)
ADV 20,000원
DOOR 25,000원''',
            'expected': {'booking_price': 20000, 'onsite_price': 25000}
        },
        {
            'name': '복합 - unplugged',
            'text': '''Unplugged Live
티켓 정보:
예매 18,000원
현장 22,000원''',
            'expected': {'booking_price': 18000, 'onsite_price': 22000}
        },
        
        # 영문 표기
        {
            'name': '영문 - Cover',
            'text': 'Cover: 15,000 KRW',
            'expected': {'booking_price': 15000, 'onsite_price': None}
        },
        {
            'name': '영문 - Ticket',
            'text': 'Ticket 12,000won',
            'expected': {'booking_price': 12000, 'onsite_price': None}
        },
        
        # 쉼표 없는 패턴
        {
            'name': '쉼표 없음',
            'text': 'ADV 10000',
            'expected': {'booking_price': 10000, 'onsite_price': None}
        },
        
        # 무료 공연
        {
            'name': '무료 (0원)',
            'text': '입장료: 무료',
            'expected': {'booking_price': 0, 'onsite_price': 0}
        },
        
        # 가격 없음 (날짜만 있는 경우)
        {
            'name': '가격 정보 없음',
            'text': '2025.11.15 공연',
            'expected': {'booking_price': None, 'onsite_price': None}
        },

        # 🎫 25,000 KRW
        {
            'name': '이모지 포함된 가격 정보',
            'text': '🎫 25,000 KRW',
            'expected': {'booking_price': 25000, 'onsite_price': None}
        },
    ]
    
    print("\n" + "=" * 70)
    print("가격 추출기 테스트".center(70))
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for i, case in enumerate(test_cases, 1):
        result = extractor.extract(case['text'])  # dict 반환됨
        expected = case['expected']
        
        booking_ok = result.get('booking_price') == expected.get('booking_price')
        onsite_ok = result.get('onsite_price') == expected.get('onsite_price')
        is_success = booking_ok and onsite_ok
        status = "✅ 성공" if is_success else "❌ 실패"
        
        print(f"\n[테스트 {i}] {case['name']}: {status}")
        print(f"  입력: {case['text'][:50]}...")
        print(f"  예상: booking={expected.get('booking_price')}, onsite={expected.get('onsite_price')}")
        print(f"  결과: booking={result.get('booking_price')}, onsite={result.get('onsite_price')}")
        print(f"  전체 결과 dict: {result}")
        
        if is_success:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"가격 테스트 결과: ✅ {passed}개 성공 / ❌ {failed}개 실패")
    print("=" * 70)


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("가격 추출기 테스트 선택".center(80))
    print("=" * 80)
    
    print("\n1. 미리 정의된 테스트 케이스 실행")
    print("2. 게시물 URL로 직접 테스트")
    
    choice = input("\n선택 (1-2): ").strip()
    
    if choice == "1":
        test_price_extractor()
    elif choice == "2":
        url = input("\n게시물 URL 입력: ").strip()
        if url:
            test_post_url(url)
        else:
            print("❌ URL을 입력하세요")
    else:
        print("❌ 잘못된 선택")
    
    print("\n" + "=" * 80)
    print("테스트 완료")
    print("=" * 80)