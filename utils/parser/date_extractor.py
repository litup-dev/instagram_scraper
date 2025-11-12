"""
날짜 추출기 - 날짜/시간 분리 파싱
"""
import re
from datetime import datetime
from typing import Optional, Tuple
from utils.logger import setup_logger

logger = setup_logger('date_extractor')

class DateExtractor:
    """공연 날짜 추출 - 날짜와 시간을 분리하여 파싱"""
    def __init__(self, default_time: str = "19:00"):
        """
        Args:
            default_time: 시간 정보가 없을 때 사용할 기본값 (HH:MM 형식)
        """
        self.default_time = default_time

    def extract(self, text: str) -> Optional[str]:
        """
        텍스트에서 날짜와 시간을 추출하여 결합
        
        Args:
            text: 추출할 텍스트
            
        Returns:
            "YYYY-MM-DD HH:MM" 형식의 문자열 또는 None
        """
        # 날짜 추출 
        date_str = self._extract_date(text)
        
        # 날짜가 없으면 None 반환
        if not date_str:
            logger.error("❌ 날짜 정보 없음 - None 반환")
            return None
        
        # 시간 추출
        time_str = self._extract_time(text)
        
        # 시간이 없으면 기본값 사용
        if not time_str:
            logger.warning(f"⚠️ 시간 정보 없음 - 기본값 사용: {self.default_time}")
            time_str = self.default_time
        
        result = f"{date_str} {time_str}"
        logger.info(f"✅ 날짜 추출 성공: {result}")
        return result    
    
    def _extract_date(self, text: str) -> Optional[str]:
        """날짜 추출 (라이브러리 우선 추출 실패시 정규식)"""
        # 1. 라이브러리로 시도
        date_str = self._extract_date_with_library(text)
        if date_str:
            return date_str
        
        # 2. 정규식으로 시도
        logger.info("⚠️ 라이브러리 실패 - 정규식 사용")
        date_str = self._extract_date_with_regex(text)
        if date_str:
            return date_str
        
        logger.warning("❌ 날짜 추출 실패")
        return None
    
    def _extract_date_with_library(self, text: str) -> Optional[str]:
        """dateparser 라이브러리로 날짜 추출"""
        try:
            # dateparser 설정
            settings = {
                'PREFER_DATES_FROM': 'future', # 날짜 문자열에 명시적인 연도가 없을 경우, 해당 날짜를 미래 기준으로 추정
                'PREFER_DAY_OF_MONTH': 'first', # 날짜 문자열에 일(day) 정보가 없을 경우, 해당 월의 첫째 날을 기본값으로 사용
                'RETURN_AS_TIMEZONE_AWARE': False,
            }
            
            parsed = dateparser.parse(text, languages=['ko', 'en'], settings=settings)
            if parsed:
                date_str = parsed.strftime('%Y-%m-%d')
                logger.info(f"📅 [dateparser] 날짜 추출: {date_str}")
                return date_str
            
            # 줄바꿈으로 분리해서 각 줄에서 시도
            for line in text.split('\n'):
                parsed = dateparser.parse(line, languages=['ko', 'en'], settings=settings)
                if parsed:
                    date_str = parsed.strftime('%Y-%m-%d')
                    logger.info(f"📅 [dateparser 줄바꿈] 날짜 추출: {date_str}")
                    return date_str
                    
        except Exception as e:
            logger.debug(f"dateparser 오류: {e}")
        
        return None
    
    def _extract_date_with_regex(self, text: str) -> Optional[str]:
        """정규식으로 날짜 추출 (라이브러리 실패시)"""
        date_patterns = [
            # YYYY.MM.DD, YYYY-MM-DD, YYYY/MM/DD
            (r'(\d{4})[.\-/]\s*(\d{1,2})[.\-/]\s*(\d{1,2})', 'ymd'),
            # YY.MM.DD (25.11.29)
            (r'(\d{2})[.\-/]\s*(\d{1,2})[.\-/]\s*(\d{1,2})', 'short_ymd'),
            # MM/DD or M/D
            (r'(\d{1,2})[./-](\d{1,2})(?!\d)', 'md'),
            # DD.MM.YYYY (28.NOV.2025)
            (r'(\d{1,2})\s*\.\s*([A-Z]{3})\s*\.\s*(\d{4})', 'dmy_month'),
            # YYYY년 MM월 DD일
            (r'(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일?', 'ymd_korean'),
            # MM월 DD일 (연도 없음 - 현재 연도 사용)
            (r'(\d{1,2})\s*월\s*(\d{1,2})\s*일?', 'md_korean'),
            
        ]
        
        month_map = {
            'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
            'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
        }
        
        for pattern, pattern_type in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                logger.info(f"📅 [정규식] 날짜 매칭: {match.group()}")
                
                try:
                    if pattern_type == 'ymd':
                        year, month, day = match.groups()
                        date_str = f"{year}-{int(month):02d}-{int(day):02d}"
                    elif pattern_type == 'short_ymd':
                        year, month, day = match.groups()
                        year = int(year)
                        year = 2000 + year if year < 50 else 1900 + year
                        date_str = f"{year}-{int(month):02d}-{int(day):02d}"
                    elif pattern_type == 'md':
                        month, day = match.groups()
                        year = datetime.now().year
                        date_str = f"{year}-{int(month):02d}-{int(day):02d}"
                    elif pattern_type == 'dmy_month':
                        day, month_str, year = match.groups()
                        month = month_map.get(month_str.upper())
                        if month:
                            date_str = f"{year}-{month:02d}-{int(day):02d}"
                        else:
                            continue
                    
                    elif pattern_type == 'ymd_korean':
                        year, month, day = match.groups()
                        date_str = f"{year}-{int(month):02d}-{int(day):02d}"
                    
                    elif pattern_type == 'md_korean':
                        month, day = match.groups()
                        year = datetime.now().year
                        date_str = f"{year}-{int(month):02d}-{int(day):02d}"
                    
                    logger.info(f"📅 [정규식] 날짜 추출: {date_str}")
                    return date_str
                
                except Exception as e:
                    logger.debug(f"날짜 파싱 오류: {e}")
                    continue
        
        return None
    
    def _extract_time(self, text: str) -> Optional[str]:
        """시간 추출 (라이브러리 우선, 실패시 정규식)"""
        # 1. 라이브러리로 시도
        time_str = self._extract_time_with_library(text)
        if time_str:
            return time_str
        
        # 2. 정규식으로 시도
        logger.info("⚠️ 라이브러리 실패 - 정규식 사용")
        time_str = self._extract_time_with_regex(text)
        if time_str:
            return time_str
        
        logger.warning("❌ 시간 추출 실패")
        return None

    def _extract_time_with_library(self, text: str) -> Optional[str]:
        """dateparser 라이브러리로 시간 추출"""
        try:
            # 시간만 있는 패턴 찾기
            time_keywords = ['시간', 'time', 'gig time', '공연시간']
            
            for keyword in time_keywords:
                if keyword in text.lower():
                    # 키워드 뒤의 내용 추출
                    idx = text.lower().find(keyword)
                    time_part = text[idx:idx+50]  # 키워드 이후 50자
                    
                    parsed = dateparser.parse(time_part, languages=['ko', 'en'])
                    if parsed:
                        time_str = parsed.strftime('%H:%M')
                        logger.info(f"🕐 [라이브러리] 키워드 뒤 시간 추출: {time_str}")
                        return time_str
            
            # 줄바꿈으로 분리해서 시간만 있는 줄 찾기
            for line in text.split('\n'):
                if ':' in line or 'pm' in line.lower() or 'am' in line.lower() or '시' in line:
                    parsed = dateparser.parse(line, languages=['ko', 'en'])
                    if parsed:
                        time_str = parsed.strftime('%H:%M')
                        logger.info(f"🕐 [라이브러리] 줄바꿈으로 시간 추출: {time_str}")
                        return time_str
                        
        except Exception as e:
            logger.debug(f"dateparser 시간 오류: {e}")
        
        return None
    
    def _extract_time_with_regex(self, text: str) -> Optional[str]:
        """정규식으로 시간 추출 (라이브러리 실패시)"""
        time_patterns = [
            # 7:30 PM, 10pm, 8PM
            (r'(\d{1,2})(?::(\d{2}))?\s*(PM|AM|pm|am)', 'ampm'),
            # 19:00, 7:30
            (r'(\d{1,2}):(\d{2})', 'colon'),
            # 오후 7시, 저녁 7시, 오전 11시
            (r'(오후|오전|저녁|아침)\s*(\d{1,2})\s*시', 'korean'),
            # 7시 30분
            (r'(\d{1,2})\s*시\s*(\d{1,2})?\s*분?', 'simple'),
        ]

        for pattern, pattern_type in time_patterns:
            logger.info(f"🕐 [정규식] 시간 매칭: {pattern}/{pattern_type}")
        
            
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                logger.info(f"🕐 [정규식] 시간 매칭: {match.group()}")
                
                try:
                    if pattern_type == 'ampm':
                        hour, minute, period = match.groups()
                        hour = int(hour)
                        minute = int(minute) if minute else 0
                        
                        if period.upper() == 'PM' and hour != 12:
                            hour += 12
                        elif period.upper() == 'AM' and hour == 12:
                            hour = 0
                        
                        time_str = f"{hour:02d}:{minute:02d}"
                    
                    elif pattern_type == 'colon':
                        hour, minute = match.groups()
                        time_str = f"{int(hour):02d}:{int(minute):02d}"
                    
                    elif pattern_type == 'korean':
                        period, hour = match.groups()
                        hour = int(hour)
                        
                        if period in ['오후', '저녁'] and hour != 12:
                            hour += 12
                        elif period in ['오전', '아침'] and hour == 12:
                            hour = 0
                        
                        time_str = f"{hour:02d}:00"
                    
                    elif pattern_type == 'simple':
                        hour, minute = match.groups()
                        hour = int(hour)
                        minute = int(minute) if minute else 0
                        time_str = f"{hour:02d}:{minute:02d}"
                    
                    logger.info(f"🕐 [정규식] 시간 추출: {time_str}")
                    return time_str
                
                except Exception as e:
                    logger.debug(f"시간 파싱 오류: {e}")
                    continue
        
        return None
    