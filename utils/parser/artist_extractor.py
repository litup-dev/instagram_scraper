"""
아티스트 추출기
"""
import re
from typing import List, Dict
from typing import Optional
from utils.logger import setup_logger
from config.settings import CHANNELS

logger = setup_logger('artist_extractor')


class ArtistExtractor:
    """아티스트 정보 추출"""
    
    # 아티스트에서 제외할 키워드 목록
    EXCLUDED_NAME_KEYWORDS = ['문의']
    # 아티스트에서 제외할 키워드 목록
    EXCLUDED_AT_KEYWORDS = ['FF']
    
    def extract(self, text: str) -> List[Dict[str, str]]:
        """
        텍스트에서 아티스트 추출
        
        Args:
            text: 캡션 텍스트
            
        Returns:
            [{'name': '아티스트명', 'insta': '@handle'}, ...] 형식의 리스트
        """
        if not text:
            return []
        
        artists = []
        artists.extend(self._extract_basic_pattern(text))

        # 중복 제거
        return self._remove_duplicates(artists)
    
    def _extract_basic_pattern(self, text: str) -> List[Dict[str, str]]:
        """기본 패턴 (아티스트명 @handle)"""
        artists = []
        pattern = r'^[\s>🌀✨—]*(.+?)\s+(@[\w\.-]+)'
        
        for line in text.split('\n'):
            line = line.strip()

            if '@' not in line or len(line) < 3:
                continue
            
            match = re.match(pattern, line)
            if match:
                handle = match.group(2).strip()
                name = match.group(1).strip()
                
                # 규칙 1: #이 들어간 경우, # 다음의 단어만 name으로 지정
                if '#' in name:
                    hashtag_match = re.search(r'#(\S+)', name)
                    if hashtag_match:
                        name = hashtag_match.group(1)
                        logger.info(f"🏷️ 해시태그에서 추출: {name}")
                
                if len(name) < 1:
                    name = handle.replace('@', '').replace('_', ' ')
                
                # 규칙 2: 특정 키워드가 포함된 경우 제외 (name)
                if self._contains_excluded_keywords(name, self.EXCLUDED_NAME_KEYWORDS):
                    logger.warning(f"⚠️ 제외 키워드 포함 [name] (제외): {name}")
                    continue
                
                # 규칙 2-2: 특정 키워드가 포함된 경우 제외 (@handle)
                if self._contains_excluded_keywords(handle, self.EXCLUDED_AT_KEYWORDS):
                    logger.warning(f"⚠️ 제외 키워드 포함 [@handle] (제외): {handle}")
                    continue
                
                # 규칙 3: 설명 텍스트 제외 (너무 긴 텍스트나 특정 패턴)
                if self._is_description_text(name):
                    logger.warning(f"⚠️ 설명 텍스트로 판단 (제외): {name[:50]}...")
                    continue
                
                # 규칙 4: name에 한글 또는 영어가 최소 1글자 이상 있어야 함
                if not self._has_valid_characters(name):
                    logger.warning(f"⚠️ 유효한 문자 없음 (제외): {name}")
                    continue

                # 채널명이 포함되면 제외
                channel_usernames = {c['username'].lower() for c in CHANNELS}
                if any(channel in handle.lower() for channel in channel_usernames):
                    logger.info(f"🚫 채널명 제외: {handle}")
                    continue

                artists.append({'name': name, 'insta': handle})
        
        return artists

    def _has_valid_characters(self, name: str) -> bool:
        """
        규칙 4: name에 한글 또는 영어가 최소 1글자 이상 있는지 확인
        """
        # 한글: ㄱ-ㅎ, ㅏ-ㅣ, 가-힣
        # 영어: a-zA-Z
        return bool(re.search(r'[가-힣ㄱ-ㅎㅏ-ㅣa-zA-Z]', name))

    def _contains_excluded_keywords(self, text: str, keywords: List[str]) -> bool:
        """
        규칙 2: 제외할 키워드가 포함되어 있는지 확인
        
        Args:
            text: 검사할 텍스트 (name 또는 @handle)
            keywords: 제외할 키워드 목록
        """
        return any(keyword in text for keyword in keywords)

    def _is_description_text(self, name: str) -> bool:
        """
        규칙 3: 설명 텍스트인지 판단
        - 너무 긴 텍스트 (50자 이상)
        - 쉼표나 마침표가 2개 이상 포함
        - '으로', '하는' 등 설명문에 자주 나오는 조사/동사 포함
        """
        # 길이 체크
        if len(name) > 50:
            return True
        
        # 문장 부호 체크
        punctuation_count = name.count(',') + name.count('.') + name.count('、')
        if punctuation_count >= 2:
            return True
        
        # 조사 키워드
        description_keywords = [
            '하는', '으로', '에서', '통해', '함께', '대한'
        ]
        
        if any(keyword in name for keyword in description_keywords):
            return True
        
        return False
    
    
    def _remove_duplicates(self, artists: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """중복 제거 (인스타 핸들 기준)"""
        unique = []
        seen = set()
        
        for artist in artists:
            handle = artist['insta'].lower()
            if handle not in seen:
                seen.add(handle)
                unique.append(artist)
        
        return unique