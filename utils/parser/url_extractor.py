"""
예매 URL 추출기
"""
import re
from typing import Optional, Dict
from utils.logger import setup_logger

logger = setup_logger('booking_url_extractor')

class UrlExtractor:
    # 예매 관련 URL 패턴들
    BOOKING_URL_PATTERNS = [
        r'https?://booking\.naver\.com/[^\s\)]+',
        r'https?://ticket\.interpark\.com/[^\s\)]+',
        r'https?://www\.melon\.com/[^\s\)]+',
        r'https?://tickets\.melon\.com/[^\s\)]+',
        r'https?://ticketlink\.co\.kr/[^\s\)]+',
        r'https?://www\.yes24\.com/[^\s\)]+',
        r'https?://ticket\.yes24\.com/[^\s\)]+',
        r'https?://forms\.gle/[^\s\)]+',
        r'https?://docs\.google\.com/forms/[^\s\)]+',
        r'https?://[^\s]*ticket[^\s]*',  # ticket 포함된 URL
        r'https?://[^\s]*booking[^\s]*',  # booking 포함된 URL
    ]
    
    # 프로필 링크 참조 키워드
    PROFILE_LINK_KEYWORDS = [
        '프로필 링크',
        '프로필상 링크',
        'profile link',
        'linktree',
        'link tree',
        '프로필을 참고',
        '프로필 참고',
        '프로필에서',
        '상단 Link',
        'Link'
    ]
    
    def __init__(self):
        pass
    
    def extract(self, caption: str, profile_url: Optional[str] = None) -> Dict[str, Optional[str]]:
        """
        예매 URL 추출
        
        로직 순서:
        1. 프로필에 linktr.ee가 있으면 → 게시글에서 프로필 링크 참조 확인
        2. 프로필 링크 참조 없으면 → 게시글에서 직접 URL 찾기
        3. 둘 다 없으면 → None
        
        Args:
            caption: Instagram 게시글 본문
            profile_url: 프로필 링크 (linktr.ee 등)
            
        Returns: 추출된 URL 또는 None,
        """
        if not caption:
            return None

        # 1. 프로필에 linktr.ee가 있으면 먼저 프로필 링크 참조 확인
        if profile_url and self._is_linktree_url(profile_url):
            if self._has_profile_link_reference(caption):
                logger.info(f"✅ 예매 URL 추출 (프로필 링크 참조 - linktr.ee): {profile_url}")
                return profile_url
        
        # 2. 게시글 내에서 직접 URL 찾기
        direct_url = self._extract_direct_url(caption)
        if direct_url:
            logger.info(f"✅ 예매 URL 추출 (직접): {direct_url}")
            return  direct_url
        
        # 3. 프로필 링크 참조 확인 (linktr.ee 아닌 경우에도)
        if self._has_profile_link_reference(caption):
            logger.info(f"✅ 예매 URL 추출 (프로필 링크 참조)")
            if profile_url:
                logger.info(f"   프로필 URL: {profile_url}")
                return profile_url
            else:
                logger.warning(f"⚠️ 프로필 링크 참조되었으나 프로필 URL 없음")
                return None
        
        logger.info("ℹ️ 예매 URL 정보 없음")
        return None
    
    def _extract_direct_url(self, text: str) -> Optional[str]:
        """게시글에서 직접 예매 URL 추출"""
        for pattern in self.BOOKING_URL_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                url = match.group(0)
                # URL 끝의 괄호나 마침표 제거
                url = re.sub(r'[)\].,;]+$', '', url)
                return url
        return None
    
    def _has_profile_link_reference(self, text: str) -> bool:
        """프로필 링크 참조 여부 확인"""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in self.PROFILE_LINK_KEYWORDS)
    
    def _is_linktree_url(self, url: str) -> bool:
        """linktr.ee URL인지 확인"""
        return 'linktr.ee' in url.lower()
    
    def extract_profile_url_from_bio(self, bio: str) -> Optional[str]:
        """
        프로필 바이오에서 링크 추출 (linktr.ee 등)
        
        Args:
            bio: Instagram 프로필 바이오
            
        Returns:
            추출된 URL 또는 None
        """
        if not bio:
            return None
        
        # linktr.ee 및 일반 URL 패턴
        url_patterns = [
            r'https?://linktr\.ee/[^\s]+',
            r'https?://[^\s]+',
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, bio, re.IGNORECASE)
            if match:
                url = match.group(0)
                url = re.sub(r'[)\].,;]+$', '', url)
                return url
        
        return None