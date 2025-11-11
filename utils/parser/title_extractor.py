"""
제목 추출기
"""
import re
from typing import Optional
from utils.logger import setup_logger

logger = setup_logger('title_extractor')

class TitleExtractor:
    """공연 제목 추출"""
    
    def __init__(self):
        self.exclude_tags = [
            'live', 'concert', 'show', 'gig', 'liveishere', 
            'concertphotography', 'livemusic'
        ]
    
    def extract(self, text: str) -> Optional[str]:
        """
        텍스트에서 공연 제목 추출
        
        Args:
            text: 캡션 텍스트
            
        Returns:
            제목 또는 None
        """
        if not text:
            return None
        
        # 패턴 1: 첫 줄에서 제목
        title = self._extract_from_first_line(text)
        if title:
            logger.info(f"✅ 제목 추출 (첫줄): {title}")
            return title
        
        # 패턴 2: <제목> 또는 "제목"
        title = self._extract_from_brackets(text)
        if title:
            logger.info(f"✅ 제목 추출 (괄호): {title}")
            return title
        
        # 패턴 3: 해시태그
        title = self._extract_from_hashtag(text)
        if title:
            logger.info(f"✅ 제목 추출 (해시태그): {title}")
            return title
        
        logger.warning("⚠️ 제목 추출 실패")
        return None
    
    def _extract_from_first_line(self, text: str) -> Optional[str]:
        """첫 줄에서 제목 추출"""
        first_line = text.split('\n')[0].strip()
        
        # 이모지와 특수문자 제거
        clean = re.sub(r'[⚠️💫🚨🎸\[\]<>"""\(\).]', '', first_line).strip()
        
        # 유효성 검사
        if (2 < len(clean) < 50 and 
            not clean.isdigit() and 
            not re.match(r'^\d{4}[./]', clean)):
            return clean
        
        return None
    
    def _extract_from_brackets(self, text: str) -> Optional[str]:
        """<제목> 또는 "제목" 형식"""
        match = re.search(r'[<"]([^>"]+)[>"]', text)
        if match:
            title = match.group(1).strip()
            if 2 < len(title) < 50:
                return title
        return None
    
    def _extract_from_hashtag(self, text: str) -> Optional[str]:
        """해시태그에서 제목 추출"""
        match = re.search(r'#([가-힣a-zA-Z0-9]+)', text)
        if match:
            tag = match.group(1)
            if tag.lower() not in self.exclude_tags:
                return tag
        return None