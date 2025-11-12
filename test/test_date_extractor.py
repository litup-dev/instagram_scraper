"""
날짜 추출기 테스트
"""
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.parser.date_extractor import DateExtractor

# ========== 테스트 코드 ==========

def test_date_extractor():
    """날짜 추출기 테스트"""
    extractor = DateExtractor()
    
    test_cases = [
        {
            'text': '일시 Date : 2025. 11. 23 일Sun\n공연시간 Gig Time : 19:00',
            'expected': '2025-11-23 19:00'
        },
        {
            'text': '2025.11.14 (FRI) 7:30 PM',
            'expected': '2025-11-14 19:30'
        },
        {
            'text': '2025/11/16 (Sun) 10pm',
            'expected': '2025-11-16 22:00'
        },
        {
            'text': '공연날짜 : 28.NOV.2025 공연시간 : 8PM',
            'expected': '2025-11-28 20:00'
        },
        {
            'text': '2025.11.15 (SAT)\nat CLUB FF',
            'expected': '2025-11-15 19:00'
        },
        {
            'text': '일시: 2025.10.24\n장소: 클럽빵\n시간: 20:00',
            'expected': '2025-10-24 20:00'
        },
        {
            'text': '2025. 11. 7 금Fri 저녁 7시',
            'expected': '2025-11-07 19:00'
        },
        {
            'text': '2025.11.15 (SAT) \nOPEN 15:30',
            'expected': '2025-11-15 15:30'
        },
        {
            'text': '2025/11/14 (FRI) 7:00pm',
            'expected': '2025-11-14 19:00'
        },
        {
            'text': '공연날짜 : 28.NOV.2025\n공연시간 : 8PM',
            'expected': '2025-11-28 20:00'
        },
        {
            'text': '📅 11/29 (토) 19:00',
            'expected': '2025-11-29 19:00'
        },
        {
            'text': '2025. 11. 23 일Sun\n공연시간 Gig Time : 19:00',
            'expected': '2025-11-23 19:00'
        },
        {
            'text': '2025년 11월 14일(금) 저녁 7시',
            'expected': '2025-11-14 19:00'
        },
        {
            'text': '2025.12.14 SUN\nOPEN 17:00',
            'expected': '2025-12-14 17:00'
        },
        {
            'text': '2025년 11월 17일 월요일 저녁 8시',
            'expected': '2025-11-17 20:00'
        },
        {
            'text': '25.11.29 토요일 7시',
            'expected': '2025-11-29 19:00'
        },
        {
            'text': '2025년 11월 28일 금요일 오후 8시',
            'expected': '2025-11-28 20:00'
        },
    ]
    
    print("=" * 60)
    print("날짜 추출기 테스트")
    print("=" * 60)
    
    for i, case in enumerate(test_cases, 1):
        result = extractor.extract(case['text'])
        expected = case['expected']
        
        status = "✅ 성공" if result == expected else "❌ 실패"
        print(f"\n테스트 {i}: {status}")
        print(f"  입력: {case['text'][:50]}...")
        print(f"  예상: {expected}")
        print(f"  결과: {result}")


if __name__ == "__main__":
    test_date_extractor()