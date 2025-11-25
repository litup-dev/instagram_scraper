"""
Instagram 스크래퍼 (instagrapi 사용 - Private API)
"""
from instagrapi import Client
from instagrapi.exceptions import (LoginRequired, PleaseWaitFewMinutes, ClientError, ChallengeRequired, UserNotFound)
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time, os, re, json
from utils.logger import setup_logger
from config.settings import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD

logger = setup_logger('instagram_scraper')

class InstagramScraper:
    def __init__(self, days: int = 7):
        """
        Args:
            days: 최근 며칠 이내 게시물 수집 (기본값 7일)
        """
        self.days = days
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
                    logger.info("✅ 저장된 세션 로드 성공\n")
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
    
    def scrape_channel_by_url(
        self, 
        instagram_url: str, 
        last_post_url: Optional[str] = None,
        retry_count: int = 0
    ) -> List[Dict]:
        """
        Instagram URL로 채널 스크래핑
        
        Args:
            instagram_url: Instagram 프로필 URL
            last_post_url: 마지막으로 저장된 게시물 URL (이 이후 게시물만 수집)
            retry_count: 재시도 횟수
            
        Returns:
            게시물 데이터 리스트
        """
        username = self.extract_username_from_url(instagram_url)
        return self.scrape_channel(username, last_post_url, retry_count)
    
    def scrape_channel(
        self, 
        username: str, 
        last_post_url: Optional[str] = None,
        retry_count: int = 0
    ) -> List[Dict]:
        """
        특정 채널의 최근 게시물 수집
        
        Args:
            username: Instagram 사용자명
            last_post_url: 마지막으로 저장된 게시물 URL (이 이후 게시물만 수집)
            retry_count: 재시도 횟수
        """
        MAX_RETRIES = 2
        # 날짜 범위 내에서 충분한 게시물을 가져오기 위해 넉넉하게 설정
        # (대부분의 클럽은 하루에 1-2개 게시물 정도)
        FETCH_AMOUNT = self.days * 5  # 예: 7일이면 35개 가져오기
        
        try:
            logger.info(f"📥 {username} 채널 스크래핑 시작...")
            logger.info(f"📅 최근 {self.days}일 이내 게시물 수집")
            
            if last_post_url:
                logger.info(f"📌 마지막 저장 게시물: {last_post_url}")
                logger.info(f"   → 이후의 최신 게시물만 수집합니다")
            
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
            logger.info(f"📋 게시물 가져오는 중... (최대 {FETCH_AMOUNT}개)")
            medias = self.client.user_medias_v1(user_id, FETCH_AMOUNT)
            logger.info(f"✅ 가져온 게시물 수: {len(medias)}개")
            
            if not medias:
                logger.warning("⚠️ 게시물이 없습니다")
                return []

            posts = []
            
            # 최신순 정렬
            medias = sorted(medias, key=lambda x: x.taken_at, reverse=True)
            
            # 날짜 기준 계산
            cutoff_date = datetime.now(medias[0].taken_at.tzinfo) - timedelta(days=self.days)
            logger.info(f"📅 기준 날짜: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')} 이후")

            # 마지막 저장 게시물의 shortcode 추출
            last_post_code = None
            if last_post_url:
                # URL에서 shortcode 추출: https://www.instagram.com/p/SHORTCODE/
                match = re.search(r'/p/([^/]+)/', last_post_url)
                if match:
                    last_post_code = match.group(1)
                    logger.info(f"📌 마지막 게시물 코드: {last_post_code}")

            found_last_post = False if last_post_code else True
            collected_count = 0
            skipped_old = 0
            
            for i, media in enumerate(medias, 1):
                try:
                    current_post_code = str(media.code)
                    post_date = media.taken_at
                    
                    # 마지막 저장 게시물을 만나면 중단
                    if last_post_code and current_post_code == last_post_code:
                        logger.info(f"✋ 마지막 저장 게시물 도달, 수집 중단")
                        found_last_post = True
                        break
                    
                    # 날짜 범위 확인
                    if post_date < cutoff_date:
                        skipped_old += 1
                        logger.info(f"⏰ [{i}/{len(medias)}] 기준 날짜 이전 게시물, 건너뛰기 ({post_date.strftime('%Y-%m-%d')})")
                        
                        # 오래된 게시물이 연속으로 나오면 중단
                        if skipped_old >= 3:
                            logger.info(f"   → 오래된 게시물 연속 {skipped_old}개, 수집 중단")
                            break
                        continue
                    
                    # 게시물 데이터 추출
                    post_data = self._extract_post_data(media)
                    if post_data:
                        posts.append(post_data)
                        collected_count += 1
                        logger.info(f"✅ [{i}/{len(medias)}] 게시물 수집 완료 ({post_date.strftime('%Y-%m-%d %H:%M')})")
                        
                        # 파싱 정보 로깅
                        logger.info("\n" + "✨ 게시글 정보 ✨".center(80, "="))
                        logger.info(json.dumps({
                            'post_url': post_data.get('post_url'),
                            'post_date': post_data.get('post_date'),
                            '원본 데이터': (media.caption_text or '')[:200] + '...' if len(media.caption_text or '') > 200 else (media.caption_text or '')
                        }, ensure_ascii=False, indent=2))
                        logger.info("=" * 80 + "\n")
                    
                    # Rate limit 방지
                    time.sleep(5)
                    
                except Exception as e:
                    logger.error(f"❌ 게시물 {i} 처리 오류: {e}")
                    continue
            
            if last_post_code and not found_last_post:
                logger.warning(f"⚠️ 마지막 저장 게시물을 찾지 못했습니다. 날짜 기준으로 {len(posts)}개 수집")
            
            logger.info(f"\n📊 총 {len(posts)}개의 새로운 게시물 수집 완료 (최근 {self.days}일)")
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
                
                return self.scrape_channel(username, last_post_url, retry_count + 1)
            else:
                logger.error("❌ 최대 재시도 초과")
                return []
        
        except PleaseWaitFewMinutes:
            logger.error(f"❌ Rate limit 도달")
            if retry_count < MAX_RETRIES:
                logger.info("⏸️  5분 대기...")
                time.sleep(300)
                return self.scrape_channel(username, last_post_url, retry_count + 1)
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