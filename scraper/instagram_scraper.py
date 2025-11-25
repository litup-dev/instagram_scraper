"""
Instagram 스크래퍼 (instagrapi 사용 - Private API)
"""
from instagrapi import Client
from instagrapi.exceptions import (LoginRequired, PleaseWaitFewMinutes, ClientError, ChallengeRequired, UserNotFound)
from datetime import datetime, timedelta
from typing import List, Dict
import time, os, re, json
from utils.logger import setup_logger
from config.settings import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD

logger = setup_logger('instagram_scraper')

# 가져올 게시물 수
AMOUNT = 1

# 게시물 수집 시, 최근 CUTOFF_DAYS 일 이내 게시물만 수집
CUTOFF_DAYS = 0

class InstagramScraper:
    def __init__(self):
        self.client = Client()
        self.client.request_timeout = 10
        self.client.delay_range = [2, 5]
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
                    self.client.account_info()
                    logger.info("✅ 저장된 세션 로드 성공")
                    time.sleep(3)
                    return
                except Exception as e:
                    logger.warning(f"⚠️ 세션 로드 실패: {e}")
                    if os.path.exists(self.session_file):
                        os.remove(self.session_file)
            
            # 새로 로그인
            logger.info(f"🔐 Instagram 로그인 시도: {INSTAGRAM_USERNAME}")
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
    
    def extract_username_from_url(self, instagram_url: str) -> str:
        """
        Instagram URL에서 username 추출
        
        Args:
            instagram_url: Instagram 프로필 URL (예: https://www.instagram.com/username/)
            
        Returns:
            추출된 username
        """
        # URL에서 username 추출 (마지막 슬래시 제거)
        instagram_url = instagram_url.rstrip('/')
        username = instagram_url.split('/')[-1]
        
        logger.info(f"📝 URL에서 추출된 username: {username}")
        return username
    
    def scrape_channel_by_url(self, instagram_url: str, retry_count=0) -> List[Dict]:
        """
        Instagram URL로 채널 스크래핑
        
        Args:
            instagram_url: Instagram 프로필 URL
            retry_count: 재시도 횟수
            
        Returns:
            게시물 데이터 리스트
        """
        username = self.extract_username_from_url(instagram_url)
        return self.scrape_channel(username, retry_count)
    
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
                        
                    post_data = self._extract_post_data(media)
                    if post_data:
                        posts.append(post_data)
                        logger.info(f"✅ [{i}/{len(medias)}] 게시물 수집 완료")
                        
                        # 파싱 정보 로깅
                        logger.info("\n" + "✨ 게시글 정보 ✨".center(80, "="))
                        logger.info(json.dumps({
                            'post_url': post_data.get('post_url'),
                            '원본 데이터': media.caption_text or ''
                        }, ensure_ascii=False, indent=2))
                    
                    # Rate limit 방지
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
            
            # 최종 데이터
            post_data = {
                'post_id': str(media.code),
                'image_url': image_url,
                'caption': caption,
                'post_date': getattr(media.taken_at, 'strftime', lambda fmt: None)('%Y-%m-%d %H:%M:%S'),
                'post_url': post_url,
            }
            return post_data
        except Exception as e:
            logger.error(f"❌ 데이터 추출 오류: {e}")
            return None