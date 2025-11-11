"""
날짜 추출기
"""
import re
from datetime import datetime
from typing import Optional
from utils.logger import setup_logger

logger = setup_logger('date_extractor')

class DateExtractor:
    """공연 날짜 추출"""
    
    def __init__(self):
        self.patterns = [
            self._pattern_full_datetime,      # 패턴 1: 완전한 날짜+시간
            self._pattern_date_with_pm,       # 패턴 2: PM/AM 포함
            self._pattern_date_with_time,     # 패턴 3: 날짜 + 공연시간
            self._pattern_nov_format,         # 패턴 4: NOV 형식
            self._pattern_simple_datetime,    # 패턴 5: 간단한 날짜+시간
        ]
    
    def extract(self, text: str) -> Optional[str]:
        """
        텍스트에서 공연 날짜 추출
        
        Args:
            text: 캡션 텍스트
            
        Returns:
            'YYYY-MM-DD HH:MM' 형식의 날짜 또는 None
        """
        if not text:
            return None
        
        # 모든 패턴 시도
        for pattern_func in self.patterns:
            result = pattern_func(text)
            if result:
                logger.info(f"✅ 날짜 추출 성공: {result}")
                return result
        
        logger.warning("⚠️ 날짜 추출 실패")
        return None
    
    def _pattern_full_datetime(self, text: str) -> Optional[str]:
        """
        패턴 1: "일시 Date : 2025. 11. 23 일Sun 공연시간 Gig Time : 19:00"
        """
        pattern = r'(?:일시|Date)\s*[:：]?\s*(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2}).*?(?:공연시간|Gig\s*Time|START)\s*[:：]?\s*(\d{1,2}):(\d{2})'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            y, m, d, h, min = match.groups()
            return f"{y}-{m.zfill(2)}-{d.zfill(2)} {h.zfill(2)}:{min}"
        return None
    
    def _pattern_date_with_pm(self, text: str) -> Optional[str]:
        """
        패턴 2: "2025.11.14 (FRI) 7:30 PM" 또는 "2025/11/16 (Sun) 10pm"
        """
        # HH:MM PM 형식
        p1 = r'(\d{4})[./](\d{1,2})[./](\d{1,2})\s*\([A-Za-z]+\)\s*(\d{1,2}):(\d{2})\s*(PM|AM)'
        match = re.search(p1, text, re.IGNORECASE)
        if match:
            y, m, d, h, min, mer = match.groups()
            h = int(h)
            if mer.upper() == 'PM' and h < 12:
                h += 12
            elif mer.upper() == 'AM' and h == 12:
                h = 0
            return f"{y}-{m.zfill(2)}-{d.zfill(2)} {str(h).zfill(2)}:{min}"
        
        # HHpm 형식
        p2 = r'(\d{4})[./](\d{1,2})[./](\d{1,2})\s*\([A-Za-z]+\)\s*(\d{1,2})\s*(pm|am)'
        match = re.search(p2, text, re.IGNORECASE)
        if match:
            y, m, d, h, mer = match.groups()
            h = int(h)
            if mer.lower() == 'pm' and h < 12:
                h += 12
            elif mer.lower() == 'am' and h == 12:
                h = 0
            return f"{y}-{m.zfill(2)}-{d.zfill(2)} {str(h).zfill(2)}:00"
        
        return None
    
    def _pattern_date_with_time(self, text: str) -> Optional[str]:
        """
        패턴 3: "2025. 11. 7 금Fri 20:00 입장 / 20:30 공연 시작"
        """
        pattern = r'(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2}).*?(\d{1,2}):(\d{2})\s*공연'
        match = re.search(pattern, text)
        if match:
            y, m, d, h, min = match.groups()
            return f"{y}-{m.zfill(2)}-{d.zfill(2)} {h.zfill(2)}:{min}"
        return None
    
    def _pattern_nov_format(self, text: str) -> Optional[str]:
        """
        패턴 4: "공연날짜 : 28.NOV.2025 공연시간 : 8PM"
        """
        pattern = r'(\d{1,2})\.\s*([A-Z]{3})\.\s*(\d{4}).*?(\d{1,2})\s*PM'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            d, month_str, y, h = match.groups()
            months = {'JAN':1,'FEB':2,'MAR':3,'APR':4,'MAY':5,'JUN':6,
                     'JUL':7,'AUG':8,'SEP':9,'OCT':10,'NOV':11,'DEC':12}
            m = months.get(month_str.upper(), 1)
            h = int(h) + 12 if int(h) < 12 else int(h)
            return f"{y}-{str(m).zfill(2)}-{d.zfill(2)} {str(h).zfill(2)}:00"
        return None
    
    def _pattern_simple_datetime(self, text: str) -> Optional[str]:
        """
        패턴 5: "2025. 10. 24 20:00" 또는 "2025/11/14 (FRI) 7:00pm"
        """
        # YYYY.MM.DD HH:MM
        p1 = r'(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2}).*?(\d{1,2}):(\d{2})'
        match = re.search(p1, text)
        if match:
            y, m, d, h, min = match.groups()
            return f"{y}-{m.zfill(2)}-{d.zfill(2)} {h.zfill(2)}:{min}"
        
        # YYYY/MM/DD HH:MMpm
        p2 = r'(\d{4})[/](\d{1,2})[/](\d{1,2}).*?(\d{1,2}):(\d{2})\s*(pm|am)'
        match = re.search(p2, text, re.IGNORECASE)
        if match:
            y, m, d, h, min, mer = match.groups()
            h = int(h)
            if mer.lower() == 'pm' and h < 12:
                h += 12
            return f"{y}-{m.zfill(2)}-{d.zfill(2)} {str(h).zfill(2)}:{min}"
        
        return None

        # YYYY.MM.DD 다음 줄에 OPEN/START 시간
        p3 = r'(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\s*\n.*?START\s*(\d{1,2}):(\d{2})'
        match = re.search(p3, text, re.IGNORECASE | re.DOTALL)
        if match:
            y, m, d, h, min = match.groups()
            return f"{y}-{m.zfill(2)}-{d.zfill(2)} {h.zfill(2)}:{min}"
        
        return None