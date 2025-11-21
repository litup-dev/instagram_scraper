# utils/parser/price_extractor.py
import re
from typing import Optional, Dict, List

class PriceExtractor:
    def __init__(self, min_price=500, max_price=1000000):
        self.min_price = min_price
        self.max_price = max_price
        # 키워드 (lowercase 비교용)
        self.booking_kw = [r'예매', r'adv', r'advance', r'booking', r'ticket', r'예매adv', r'pre', r'사전']
        self.onsite_kw  = [r'현매', r'door', r'at door', r'현장', r'onsite', r'현장구매']
        # 일반 숫자 (쉼표 허용)
        self.money_re = re.compile(r'(\d{1,3}(?:,\d{3})+|\d+)(?=\s*(?:원|₩|krw|won)?\b)', re.IGNORECASE)
        # 만원 단위 (예: 3만원, 3 만원)
        self.manwonn_re = re.compile(r'(\d{1,3}(?:,\d{3})?)\s*만\s*원|\b(\d{1,3}(?:,\d{3})?)만원\b', re.IGNORECASE)

        # 날짜 패턴들(우선 제거)
        self.date_patterns = [
            re.compile(r'\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}'),  # 2025.11.15, 2025-11-15
            re.compile(r'\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4}'), # 11.15.2025, 11/15/25
            re.compile(r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일')   # 2025년 11월 15일
        ]

    def _is_valid_price(self, price: int) -> bool:
        return self.min_price <= price <= self.max_price

    def _remove_dates(self, text: str) -> str:
        # 날짜 패턴을 공백으로 치환하여 숫자 매칭에 끼어들지 못하게 함
        out = text
        for pat in self.date_patterns:
            out = pat.sub(' ', out)
        return out

    def extract(self, text: str) -> Dict[str, Optional[int]]:
        if not text:
            return {'booking_price': None, 'onsite_price': None}

        # 0) 무료
        if re.search(r'무료|free', text, re.IGNORECASE):
            return {'booking_price': 0, 'onsite_price': 0}
        
        original_text = text
        lower = text.lower()

        # 1) 날짜를 제거한 텍스트로 작업 (날짜 숫자에 의해 가격이 잡히는 것을 방지)
        cleaned_text = self._remove_dates(text)

        booking_candidates: List[int] = []
        onsite_candidates: List[int] = []

        # 헬퍼: 키워드 존재 검사 (lowercase)
        def has_booking_kw(s: str) -> bool:
            return any(k in s for k in self.booking_kw)

        def has_onsite_kw(s: str) -> bool:
            return any(k in s for k in self.onsite_kw)

        # 2) '만원' 단위 먼저 찾아서 처리 (예: 3만원 -> 30000)
        for m in re.finditer(self.manwonn_re, cleaned_text):
            # 그룹이 두 형태 중 하나에 잡힘
            g = m.group(1) or m.group(2)
            if not g:
                continue
            try:
                num = int(g.replace(',', '')) * 10000
            except Exception:
                continue
            if not self._is_valid_price(num):
                continue
            window = cleaned_text[max(0, m.start()-40): m.end()+40].lower()
            if has_booking_kw(window) and has_onsite_kw(window):
                # 두 키워드가 모두 있으면 키워드 위치로 판단
                first_booking = min((window.find(k) for k in self.booking_kw if k in window), default=9999)
                first_onsite = min((window.find(k) for k in self.onsite_kw if k in window), default=9999)
                if first_booking < first_onsite:
                    booking_candidates.append(num)
                else:
                    onsite_candidates.append(num)
            elif has_booking_kw(window):
                booking_candidates.append(num)
            elif has_onsite_kw(window):
                onsite_candidates.append(num)
            else:
                # 키워드가 없으면 booking 기본 가정 (작은값이 booking 될 것)
                booking_candidates.append(num)

        # 3) (키워드 직접 매핑) 예: '예매 10,000원' 또는 'Ticket: 20,000'
        all_kw = self.booking_kw + self.onsite_kw
        for kw in all_kw:
            # 키워드 문맥 근처의 숫자 찾기
            for m in re.finditer(rf'({kw})[^\d]{{0,10}}(\d{{1,3}}(?:,\d{{3}}+)*)', cleaned_text, re.IGNORECASE):
                kw_found = m.group(1).lower()
                try:
                    price = int(m.group(2).replace(',', ''))
                except Exception:
                    continue
                if not self._is_valid_price(price):
                    continue
                # 어느 카테고리인지 판단
                if any(re.fullmatch(p, kw_found, re.IGNORECASE) for p in self.booking_kw):
                    booking_candidates.append(price)
                elif any(re.fullmatch(p, kw_found, re.IGNORECASE) for p in self.onsite_kw):
                    onsite_candidates.append(price)

        # 4) 슬래시 / 대시 쌍: '숫자 / 숫자' 형식
        for m in re.finditer(r'(\d{1,3}(?:,\d{3})+|\d+)\s*[\/\-]\s*(\d{1,3}(?:,\d{3})+|\d+)', cleaned_text):
            a = int(m.group(1).replace(',', ''))
            b = int(m.group(2).replace(',', ''))
            if not (self._is_valid_price(a) and self._is_valid_price(b)):
                continue
            window = cleaned_text[max(0, m.start()-40): m.end()+40].lower()
            if has_booking_kw(window) and has_onsite_kw(window):
                first_booking = min((window.find(k) for k in self.booking_kw if k in window), default=9999)
                first_onsite  = min((window.find(k) for k in self.onsite_kw if k in window), default=9999)
                if first_booking < first_onsite:
                    booking_candidates.append(a)
                    onsite_candidates.append(b)
                else:
                    booking_candidates.append(b)
                    onsite_candidates.append(a)
            else:
                if a <= b:
                    booking_candidates.append(a)
                    onsite_candidates.append(b)
                else:
                    booking_candidates.append(b)
                    onsite_candidates.append(a)

        # 5) 이모지 근처 가격 (🎫 등)
        for m in re.finditer(r'[🎫💳💰]\s*(\d{1,3}(?:,\d{3})+|\d+)', cleaned_text):
            try:
                price = int(m.group(1).replace(',', ''))
            except Exception:
                continue
            if not self._is_valid_price(price):
                continue
            ctx = cleaned_text[max(0, m.start()-30):m.end()+30].lower()
            if has_onsite_kw(ctx):
                onsite_candidates.append(price)
            else:
                booking_candidates.append(price)

        # 6) 마지막: 남아있는 단일 숫자(통화표시 없는 경우) — 단, 날짜는 이미 제거했음
        all_numbers = [int(p.replace(',', '')) for p in re.findall(r'(\d{1,3}(?:,\d{3})+|\d+)', cleaned_text)]
        # 숫자들 중 유효한 범위만
        all_numbers = [p for p in all_numbers if self._is_valid_price(p)]
        if not booking_candidates and not onsite_candidates and all_numbers:
            # 기본: 가장 작은 값을 booking으로
            booking_candidates.append(min(all_numbers))

        # 결과 선택: 후보 중 최소값 선택 (기존 로직 유지)
        booking_price = min(booking_candidates) if booking_candidates else None
        onsite_price  = min(onsite_candidates)  if onsite_candidates else None

        return {'booking_price': booking_price, 'onsite_price': onsite_price}
