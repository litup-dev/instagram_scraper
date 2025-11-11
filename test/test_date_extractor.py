"""
날짜 추출기 테스트
"""
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.parser.date_extractor import DateExtractor

def test_date_extraction():
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
    ]
    
    for i, case in enumerate(test_cases, 1):
        result = extractor.extract(case['text'])
        expected = case['expected']
        
        if result == expected:
            print(f"✅ 테스트 {i} 성공: {result}")
        else:
            print(f"❌ 테스트 {i} 실패: 예상={expected}, 결과={result}")

if __name__ == "__main__":
    test_date_extraction()