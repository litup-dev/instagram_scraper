"""
아티스트 추출기
"""
import re
from typing import List, Dict
from typing import Optional
from utils.logger import setup_logger

logger = setup_logger('artist_extractor')

class ArtistExtractor:
    """아티스트 정보 추출"""
    
    def __init__(self):
        self.max_artists = 15
        self.exclude_words = [
            '언플러그드', '정기공연', 'with', '자세한', '예매', '정보',
            'ticket', 'link', 'profile', '티켓', '프로필', '링크'
        ]
        self.exclude_hashtags = [
            'liveishere', 'liveclubday', 'lcd', '라이브클럽데이', '라클데',
            '카카오창작재단', 'concertphotography', 'livemusic', 'busan',
            '공연사진', '라이브음악', '부산', '홍대클럽', '클럽ff', '라이브클럽',
            '락클럽', '홍대인디밴드', 'rockband', '인디밴드', 'rockdj',
            '밴드공연', '인디공연', '홍대인디', '홍대공연', '홍대맛집',
            '홍대데이트코스', '음악맛집', '클럽공연', '케이락', '엪엪'
        ]
    
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
        
        # 1. 라인업 섹션 찾기
        search_area = self._find_lineup_section(text)
        
        # 2. 이모지 패턴 (🌀, 🎸 등)
        artists.extend(self._extract_emoji_pattern(search_area or text))
        
        # 3. 시간 + 아티스트 패턴 ("7:00pm #밴드명 @handle")
        if not artists:
            artists.extend(self._extract_time_artist_pattern(search_area or text))
        
        # 4. "> Artist / 한글 @handle" 형식
        if not artists:
            artists.extend(self._extract_arrow_pattern(search_area or text))
        
        # 5. 기본 패턴 ("아티스트명 @handle")
        if not artists:
            artists.extend(self._extract_basic_pattern(search_area or text))
        
        # 중복 제거
        unique = self._remove_duplicates(artists)
        
        logger.info(f"✅ 아티스트 추출: {len(unique)}명")
        return unique[:self.max_artists]
    
    def _find_lineup_section(self, text: str) -> Optional[str]:
        """라인업 섹션 찾기"""
        patterns = [
            r'(?:Live\s*Bands|Line\s*up|라인업|DJs)\s*[:：\n]+(.*?)(?=\n\n|<|Cover|ADV|DOOR|티켓|입장료|예매|^\.|^#)',
            r'with[\s\n]+(.*?)(?=\n\n\[|일시|Date|티켓)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_emoji_pattern(self, text: str) -> List[Dict[str, str]]:
        """이모지 패턴 (🌀 ARTIST @handle)"""
        artists = []
        pattern = r'[🌀🎸]\s*([^\n@]+?)\s*(@[\w.]+)'
        
        for match in re.finditer(pattern, text):
            name = match.group(1).strip()
            handle = match.group(2).strip()
            if 1 < len(name) < 50:
                artists.append({'name': name, 'insta': handle})
        
        return artists
    
    def _extract_time_artist_pattern(self, text: str) -> List[Dict[str, str]]:
        """시간 + 아티스트 패턴 (7:00pm #밴드명 @handle)"""
        artists = []
        pattern = r'\d{1,2}:\d{2}\s*(?:pm|am)?\s*#?([가-힣a-zA-Z0-9\s]+?)\s*(@[\w.]+)'
        
        for match in re.finditer(pattern, text, re.IGNORECASE):
            name = match.group(1).strip()
            handle = match.group(2).strip()
            if name.lower() not in ['from', 'japan', 'taiwan'] and len(name) > 1:
                artists.append({'name': name, 'insta': handle})
        
        return artists
    
    def _extract_arrow_pattern(self, text: str) -> List[Dict[str, str]]:
        """"> Artist / 한글 @handle" 형식"""
        artists = []
        pattern = r'>\s*([^/\n@]+?)\s*/\s*([^@\n]+?)\s*(@[\w.]+)'
        
        for match in re.finditer(pattern, text):
            name1, name2, handle = match.groups()
            
            # 한글명 우선
            if re.search(r'[가-힣]', name2):
                artist_name = name2.strip()
            else:
                artist_name = name1.strip()
            
            if 1 < len(artist_name) < 50:
                artists.append({'name': artist_name, 'insta': handle})
        
        return artists
    
    def _extract_basic_pattern(self, text: str) -> List[Dict[str, str]]:
        """기본 패턴 (아티스트명 @handle)"""
        artists = []
        pattern = r'^[\s>🌀✨—]*([가-힣a-zA-Z0-9\s&\(\)\'\.]+?)\s+(@[\w.]+)'
        
        for line in text.split('\n'):
            line = line.strip()
            if '@' not in line or len(line) < 3:
                continue
            
            # 날짜 패턴 제외
            if re.match(r'^\d{4}\.\s*\d{1,2}', line):
                continue
            
            match = re.match(pattern, line)
            if match:
                name = match.group(1).strip()
                handle = match.group(2).strip()
                
                # 필터링
                if any(word in name.lower() for word in self.exclude_words):
                    continue
                
                if len(name) < 2:
                    name = handle.replace('@', '').replace('_', ' ')
                
                if 1 < len(name) < 50:
                    artists.append({'name': name, 'insta': handle})
        
        return artists
    
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