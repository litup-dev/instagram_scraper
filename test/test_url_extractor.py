"""
BookingUrlExtractor 테스트 코드
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.parser.url_extractor import UrlExtractor

def test_url_extractor():
    extractor = UrlExtractor()
    
    print("=" * 80)
    print("UrlExtractor 테스트 시작")
    print("=" * 80)
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "케이스 1: 게시글 내 네이버 예약 URL",
            "caption": """
* 날짜: 2025년 12월 6일 토요일
* 시간: 오후 6시
* 장소: 생기스튜디오 @senggistudio
* 러닝타임: 150분
* 티켓: 예매 45,000원 현매 50,000원 (총 90매 한정)
* 티켓오픈: 2025년 11월 8일 토요일 오후 6시
* 예매처: 네이버 예약 '이상의날개 2025 단독공연' 검색
* https://booking.naver.com/booking/5/bizes/1531812 (프로필 링크 참고)
            """,
            "profile_url": None,
            "expected": "https://booking.naver.com/booking/5/bizes/1531812"
        },
        {
            "name": "케이스 2: 프로필 링크 참조 (linktr.ee)",
            "caption": """
2025.12.20 (FRI) 8PM
예매는 모커의 프로필 링크를 참고해주세요
            """,
            "profile_url": "https://linktr.ee/mockerband",
            "expected": "https://linktr.ee/mockerband"
        },
        {
            "name": "케이스 3: 프로필상 링크 참조",
            "caption": """
공연 일시: 2025년 1월 10일 금요일 오후 7시
예매는 @studio.sanbo 프로필상 링크를 통해 가능합니다.
            """,
            "profile_url": "https://linktr.ee/studiosanbo",
            "expected": "https://linktr.ee/studiosanbo"
        },
        {
            "name": "케이스 4: Profile Linktree 참조",
            "caption": """
📅 2025.11.30 SAT 8PM
🎫 자세한 예매 정보는 @senggistudio Profile Linktree를 참고해주세요
            """,
            "profile_url": "https://linktr.ee/senggistudio",
            "expected": "https://linktr.ee/senggistudio"
        },
        {
            "name": "케이스 5: Google Forms 직접 링크",
            "caption": """
📝 예매 신청: https://forms.gle/abc123xyz
선착순 마감됩니다!
            """,
            "profile_url": None,
            "expected": "https://forms.gle/abc123xyz"
        },
        {
            "name": "케이스 6: 멜론티켓 직접 링크",
            "caption": """
티켓 예매: https://tickets.melon.com/performance/index.htm?prodId=209876
            """,
            "profile_url": "https://linktr.ee/someband",
            "expected": "https://tickets.melon.com/performance/index.htm?prodId=209876"
        },
        {
            "name": "케이스 7: 예매 정보 없음",
            "caption": """
오늘 공연 너무 재밌었어요!
다음에 또 만나요 🎸
            """,
            "profile_url": None,
            "expected": None
        },
        {
            "name": "케이스 8: 프로필 링크 참조했지만 profile_url 없음",
            "caption": """
예매는 프로필 링크를 확인해주세요
            """,
            "profile_url": None,
            "expected": None
        },
        {
            "name": "케이스 9: linktr.ee 있지만 프로필 참조 키워드 없음 + 직접 URL 있음",
            "caption": """
티켓 예매: https://booking.naver.com/booking/5/bizes/123456
            """,
            "profile_url": "https://linktr.ee/someband",
            "expected":  "https://booking.naver.com/booking/5/bizes/123456"
        },
        {
            "name": "케이스 10: 인터파크 티켓 링크",
            "caption": """
예매 오픈! 
https://ticket.interpark.com/ticket/goods/1234567
            """,
            "profile_url": None,
            "expected": "https://ticket.interpark.com/ticket/goods/1234567"
        },
    ]
    
    # 테스트 실행
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"테스트 {i}: {test['name']}")
        print(f"{'='*80}")
        print(f"📝 Caption:\n{test['caption'][:100]}...")
        print(f"🔗 Profile URL: {test['profile_url']}")
        print(f"✅ Expected: {test['expected']}")
        
        # 실행
        result = extractor.extract(test['caption'], test['profile_url'])
        print(f"📊 Result: {result}")
        
        # 검증
        if result == test['expected']:
            print("✅ PASS")
            passed += 1
        else:
            print("❌ FAIL")
            print(f"   Expected: {test['expected']}")
            print(f"   Got:      {result}")
            failed += 1
    
    # 결과 요약
    print(f"\n{'='*80}")
    print("테스트 결과 요약")
    print(f"{'='*80}")
    print(f"✅ Passed: {passed}/{len(test_cases)}")
    print(f"❌ Failed: {failed}/{len(test_cases)}")
    print(f"성공률: {passed/len(test_cases)*100:.1f}%")
    print("=" * 80)

if __name__ == "__main__":
    test_url_extractor()