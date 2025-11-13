"""
가격 추출기
"""
import re
from typing import Optional
from utils.logger import setup_logger

logger = setup_logger('price_extractor')

class PriceExtractor:
    """공연 가격 추출"""
    
    def __init__(self):
        self.min_price = 1000
        self.max_price = 300000
    
    def extract(self, text: str) -> Optional[int]:
        """
        텍스트에서 공연 가격 추출
        
        Args:
            text: 캡션 텍스트
            
        Returns:
            가격 (정수) 또는 None
        """
        if not text:
            return None
        
        prices = []
        
        # 패턴 1: "예매 25,000원" 또는 "ADV 30,000₩"
        prices.extend(self._extract_standard_price(text))
        
        # 패턴 2: "3만원"
        prices.extend(self._extract_man_won(text))
                
        # ⚠️ 추가: 패턴 3: 이모지 뒤 가격 (🎫 25,000 KRW)
        prices.extend(self._extract_emoji_price(text))

        if prices:
            result = min(prices)
            return result
        
        logger.warning("⚠️ 가격 추출 실패")
        return None
    
    def _extract_standard_price(self, text: str) -> list:
        """표준 가격 형식 추출"""
        prices = []
        
        patterns = [
            r'(?:ADV|예매|Ticket|입장료|Cover)\s*[:：]?\s*(\d{1,3}(?:,\d{3})+)\s*(?:원|₩|won|KRW)',
            r'(?:ADV|예매)\s*(\d{1,3}(?:,\d{3})+)',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                price_str = match.group(1).replace(',', '')
                price = int(price_str)
                if self.min_price <= price <= self.max_price:
                    prices.append(price)
        
        return prices
    
    def _extract_man_won(self, text: str) -> list:
        """'만원' 형식 추출"""
        prices = []
        
        pattern = r'(\d{1,2})\s*만\s*원'
        for match in re.finditer(pattern, text):
            price = int(match.group(1)) * 10000
            if self.min_price <= price <= self.max_price:
                prices.append(price)
        
        return prices

    
    def _extract_emoji_price(self, text: str) -> list:
        """⚠️ 새로 추가: 이모지 뒤 가격 (🎫 25,000 KRW)"""
        prices = []
        
        # 이모지 뒤에 숫자가 오는 패턴
        pattern = r'[🎫💰]\s*(\d{1,3}(?:,\d{3})+)\s*(?:원|₩|won|KRW)?'
        
        for match in re.finditer(pattern, text, re.IGNORECASE):
            price_str = match.group(1).replace(',', '')
            price = int(price_str)
            if self.min_price <= price <= self.max_price:
                prices.append(price)
                logger.debug(f"이모지 가격: {price}원")
        
        return prices
