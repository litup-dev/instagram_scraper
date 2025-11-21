"""
공연 정보 파서 (모듈화)
"""
from .date_extractor import DateExtractor
from .price_extractor import PriceExtractor
from .title_extractor import TitleExtractor
from .artist_extractor import ArtistExtractor
from typing import Dict
from utils.logger import setup_logger

logger = setup_logger('parser')

class PerformanceParseError(Exception):
    """공연 정보 파싱 실패 시 발생하는 예외"""
    pass
    
class Parser:
    """공연 정보 통합 파서"""
    
    def __init__(self):
        self.date_extractor = DateExtractor()
        self.price_extractor = PriceExtractor()
        self.title_extractor = TitleExtractor()
        self.artist_extractor = ArtistExtractor()
    
    def parse_performance_info(self, caption: str, post_url: str = '') -> Dict:
        """
        캡션에서 공연 정보 추출
        
        Args:
            caption: Instagram 캡션
            post_url: 게시물 URL
            
        Returns:
            공연 정보 딕셔너리
        """
        if not caption:
            raise PerformanceParseError("❌ 캡션 없음")
        
        result = {
            'title': self.title_extractor.extract(caption),
            'artists': self.artist_extractor.extract(caption),
            'perform_date': self.date_extractor.extract(caption),
            'booking_price': self.price_extractor.extract(caption).get('booking_price'),
            'onsite_price': self.price_extractor.extract(caption).get('onsite_price'),
            'description': caption,
            'sns_links': [{'sns': 'insta', 'link': post_url}] if post_url else []
        }

        if (not result['title'] and
            not result['artists'] and
            not result['perform_date'] and
            not result['booking_price'] and
            not result['onsite_price']):
            raise PerformanceParseError("공연 정보 없음 (제목/아티스트/날짜/가격 데이터 추출 불가)")
        
        
        logger.info(f"파싱 완료: 제목={result['title']}, "
                   f"아티스트={len(result['artists'])}명, "
                   f"날짜={result['perform_date']}, "
                   f"가격(예매/현매)={result['booking_price']} / {result['onsite_price']}")
        
        return result
    