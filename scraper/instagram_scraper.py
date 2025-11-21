"""
Instagram 스크래퍼 (instagrapi 사용 - Private API)
"""
from instagrapi import Client
from instagrapi.exceptions import (LoginRequired, PleaseWaitFewMinutes, ClientError, ChallengeRequired, UserNotFound)
from datetime import datetime, timedelta
from typing import List, Dict
import time, os, re, json
from utils.logger import setup_logger
from utils.parser import Parser, PerformanceParseError
from config.settings import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD

logger = setup_logger('instagram_scraper')

# 공연 관련 게시물인지 체크하는 키워드 (전역 상수)
PERFORMANCE_KEYWORDS = [
    '공연', '라이브', 'live', '티켓', 'ticket', '예매',
    'show', 'gig', '입장료', 'lineup', '라인업',
    'concert', '콘서트', 'performance'
]
# 공연 후기 게시물인지 체크하는 키워드 (전역 상수)
NOT_PERFORMANCE_KEYWORDS = [
    '공연사진', '후기', 'concertphotography'
]

# 가져올 게시물 수
AMOUNT = 5

# 게시물 수집 시, 최근 CUTOFF_DAYS 일 이내 게시물만 수집
CUTOFF_DAYS = 0

class InstagramScraper:
    def __init__(self):
        self.client = Client()
        self.client.request_timeout = 10 #10초 안에 응답이 없으면 TimeoutError로 실패 처리
        self.client.delay_range = [2, 5] # 봇 차단 방지용 지연요청 → API 요청 사이의 대기 시간 2초~5초 랜덤
        self.parser = Parser()
        self.session_file = 'instagram_session.json'
        self._login()
    
    def _login(self):
        """Instagram 로그인"""
        if not INSTAGRAM_USERNAME or not INSTAGRAM_PASSWORD:
            logger.error("❌ Instagram 계정 정보가 없습니다")
            raise ValueError("Instagram 계정 정보 필요")
        
        try:
            # 저장된 세션 로드 시도
            if os.path.exists(self.session_file):
                try:
                    self.client.load_settings(self.session_file)
                    # 세션 로드 후 로그인 (중요!)
                    # self.client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
                    
                    # 세션 유효성 검증
                    self.client.account_info()
                    logger.info("✅ 저장된 세션 로드 성공")
                    
                    # 로그인 직후 대기 (중요!)
                    time.sleep(3)
                    return
                    
                except Exception as e:
                    logger.warning(f"⚠️ 세션 로드 실패: {e}")
                    if os.path.exists(self.session_file):
                        os.remove(self.session_file)
            
            # 새로 로그인
            logger.info(f"🔐 Instagram 로그인 시도: {INSTAGRAM_USERNAME}")
            
            # 로그인 시도
            login_result = self.client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
            
            if not login_result:
                raise Exception("로그인 실패")
            
            # 세션 저장
            self.client.dump_settings(self.session_file)
            logger.info("✅ Instagram 로그인 성공 및 세션 저장")
            
        except ChallengeRequired:
            logger.error("❌ Instagram 보안 인증 필요")
            raise
            
        except Exception as e:
            logger.error(f"❌ 로그인 실패: {e}")
            raise
    
    def scrape_channel(self, username: str, retry_count=0) -> List[Dict]:
        """특정 채널의 최근 게시물 수집"""
        MAX_RETRIES = 2
        
        try:
            logger.info(f"📥 {username} 채널 스크래핑 시작...")
            
            # 사용자 정보 가져오기
            try:
                logger.info("👤 채널 사용자 정보 조회 중...")
                user_info = self.client.user_info_by_username_v1(username)
                user_id = user_info.pk
            except UserNotFound:
                logger.error(f"❌ {username}: 존재하지 않는 사용자")
                return []
            except Exception as e:
                logger.error(f"❌ 사용자 정보 조회 실패: {e}")
                raise
            
            # 게시물 가져오기
            logger.info("📋 게시물 가져오는 중...")
            medias = self.client.user_medias_v1(user_id, AMOUNT)
            logger.info(f"✅ 가져온 게시물 수: {len(medias)}개")
            
            if not medias:
                logger.warning("⚠️ 게시물이 없습니다")
                return []

            posts = []

            if CUTOFF_DAYS > 0:
                medias = sorted(medias, key=lambda x: x.taken_at, reverse=True)
                cutoff_date = datetime.now(medias[0].taken_at.tzinfo) - timedelta(days=CUTOFF_DAYS)
                logger.info(f"📅 최근 {CUTOFF_DAYS}일 이내 게시물만 수집")
            else:
                cutoff_date = None
                logger.info(f"📅 전체 {AMOUNT}개 게시물 수집 (기간 제한 없음)")

            for i, media in enumerate(medias, 1):
                try:
                    # 날짜 제한 있을 때만 비교
                    if cutoff_date and media.taken_at < cutoff_date:
                        logger.info(f"⏰ {CUTOFF_DAYS} 일 이전 게시물 도달, 중단")
                        break
                                        
                    # 공연 관련 게시물인지 확인
                    if self._is_performance_post(media):
                        
                        post_data = self._extract_post_data(media)
                        if post_data:
                            posts.append(post_data)
                            logger.info(f"✅ [{i}/{len(medias)}] 공연: {post_data.get('title', '')}")
                            
                            # 파싱 후
                            logger.info("\n" + "✨ 파싱 후 결과".center(80, "="))
                            logger.info(json.dumps({
                                'post_url': post_data.get('post_url'),
                                'title': post_data.get('title', 'N/A'),
                                'perform_date': post_data.get('perform_date', 'N/A'),
                                'onsite_price': post_data.get('onsite_price', 'N/A'),
                                'booking_price': post_data.get('booking_price', 'N/A'),
                                'artists_count': len(post_data.get('artists', [])),
                                'artists': post_data.get('artists', []),
                                '원본 데이터': media.caption_text or ''
                            }, ensure_ascii=False, indent=2))
                            logger.info("=" * 80 + "\n")
                    else: 

                        logger.info(f"⚠️ [{i}/{len(medias)}] 공연 게시물 아님")
                        logger.info(json.dumps({
                            'post_url': f"https://www.instagram.com/p/{media.code}/",
                            '원본 데이터': media.caption_text or ''
                        }, ensure_ascii=False, indent=2))
                        logger.info("=" * 80 + "\n")
                        
                    # Rate limit 방지 - 매 요청마다 대기
                    time.sleep(5)
                except Exception as e:
                    logger.error(f"❌ 게시물 {i} 처리 오류: {e}")
                    continue
            return posts
            
        except LoginRequired as e:
            logger.error(f"❌ {username}: 로그인 필요")
            
            # 재시도
            if retry_count < MAX_RETRIES:
                logger.info("🔄 세션 재설정 후 재시도...")
                if os.path.exists(self.session_file):
                    os.remove(self.session_file)
                
                # 재로그인
                self._login()
                time.sleep(3)
                
                return self.scrape_channel(username, retry_count + 1)
            else:
                logger.error("❌ 최대 재시도 초과")
                return []
        
        except PleaseWaitFewMinutes:
            logger.error(f"❌ Rate limit 도달")
            if retry_count < MAX_RETRIES:
                logger.info("⏸️  5분 대기...")
                time.sleep(300)
                return self.scrape_channel(username, retry_count + 1)
            return []
        
        except Exception as e:
            logger.error(f"❌ {username} 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _is_performance_post(self, media) -> bool:
        # 1. 게시글에 동영상이면 False
        # if getattr(media, 'media_type', 1) == 2 or getattr(media, 'video_url', None):
        #     logger.info(f"⛔ 동영상 게시물 제외: {media.code}")
        #     return False

        """공연 관련 게시물인지 판단"""
        caption = media.caption_text
        if not caption:
            return False
        
        caption_lower = caption.lower()
        
        # 키워드 체크
        if any(k in caption_lower for k in PERFORMANCE_KEYWORDS):
            return True

        if any(k in caption_lower for k in NOT_PERFORMANCE_KEYWORDS):
            return False
        
        return True


    def _extract_post_data(self, media) -> Dict:
        """게시물에서 데이터 추출"""
        try:
            
            image_url = ''
            if hasattr(media, 'thumbnail_url') and media.thumbnail_url:
                image_url = str(media.thumbnail_url)
            elif hasattr(media, 'resources') and media.resources:
                image_url = str(media.resources[0].thumbnail_url)
            
            caption = media.caption_text or ''
            post_url = f"https://www.instagram.com/p/{media.code}/"
            
            # 파싱 (post_url 전달)
            try:
                performance_info = self.parser.parse_performance_info(caption, post_url)
            except PerformanceParseError as e:
                logger.warning(f"⚠️ [code:{media.code}] 공연 게시물 아님 \n 이유 : {e}")
                logger.info(json.dumps({
                    'post_url': f"https://www.instagram.com/p/{media.code}/",
                    '원본 데이터': media.caption_text or ''
                }, ensure_ascii=False, indent=2))
                logger.info("=" * 80 + "\n")
                return None 
           
            # 최종 데이터
            post_data = {
                'post_id': str(media.code),
                'image_url': image_url,
                'caption': caption,
                'post_date': getattr(media.taken_at, 'strftime', lambda fmt: None)('%Y-%m-%d %H:%M:%S'),
                'post_url': post_url,
            }
            post_data.update(performance_info)
            
            return post_data
        except PerformanceParseError as e:
            return None
        except Exception as e:
            logger.error(f"❌ 데이터 추출 오류: {e}")
            return None
            
        