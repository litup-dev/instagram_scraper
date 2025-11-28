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
        self.client.request_timeout = 30
        self.client.delay_range = [3, 7]
        self.session_file = 'instagram_session.json'
        
        # 디바이스 설정 추가
        self.client.set_device({
            "app_version": "269.0.0.18.75",
            "android_version": 28,
            "android_release": "9.0",
            "dpi": "480dpi",
            "resolution": "1080x2340",
            "manufacturer": "Samsung",
            "device": "SM-G973F",
            "model": "Galaxy S10",
            "cpu": "exynos9820",
            "version_code": "314665256"
        })
        
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
                    logger.info("🔄 저장된 세션 로드 시도...")
                    self.client.load_settings(self.session_file)
                    
                    # 세션 유효성 확인
                    self.client.account_info()
                    logger.info("✅ 저장된 세션 로드 성공\n")
                    time.sleep(2)
                    return
                except Exception as e:
                    logger.warning(f"⚠️ 세션 로드 실패: {e}")
                    logger.info("🔄 새로 로그인 시도...")
                    
                    # 실패한 세션 파일 삭제
                    if os.path.exists(self.session_file):
                        os.remove(self.session_file)
                        logger.info("🗑️  기존 세션 파일 삭제")
            
            # 새로 로그인 (디바이스 설정은 __init__에서 이미 완료)
            logger.info(f"🔐 Instagram 로그인 시도: {INSTAGRAM_USERNAME}")
            
            # 로그인 전 잠깐 대기 (Rate Limit 방지)
            time.sleep(3)
            
            login_result = self.client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
            
            if not login_result:
                raise Exception("로그인 실패")
            
            logger.info("✅ Instagram 로그인 성공!")
            
            # 계정 정보 확인
            try:
                account = self.client.account_info()
                logger.info(f"📊 계정 정보:")
                logger.info(f"   사용자명: {account.username}")
                logger.info(f"   이름: {account.full_name}")
            except Exception as e:
                logger.warning(f"⚠️ 계정 정보 조회 실패: {e}")
            
            # 세션 저장
            self.client.dump_settings(self.session_file)
            logger.info(f"💾 세션 저장: {self.session_file}\n")
            
            # 로그인 직후 대기
            time.sleep(5)
            
        except ChallengeRequired:
            logger.error("❌ Instagram 보안 인증 필요")
            logger.error("💡 해결 방법:")
            logger.error("   1. Instagram 앱/웹에서 로그인")
            logger.error("   2. '의심스러운 로그인 시도' 알림 확인 및 승인")
            logger.error("   3. 2단계 인증이 활성화되어 있다면 비활성화")
            raise
        except Exception as e:
            logger.error(f"❌ 로그인 실패: {e}")
            logger.error("💡 해결 방법:")
            logger.error("   1. 비밀번호 확인")
            logger.error("   2. 계정이 차단되지 않았는지 확인")
            logger.error("   3. test/login.py로 수동 로그인 테스트")
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
            
            # Rate Limit 방지를 위한 딜레이
            time.sleep(3)
            
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
                    time.sleep(7)
                    
                except Exception as e:
                    logger.error(f"❌ 게시물 {i} 처리 오류: {e}")
                    continue
            
            if last_post_code and not found_last_post:
                logger.warning(f"⚠️ 마지막 저장 게시물을 찾지 못했습니다. 날짜 기준으로 {len(posts)}개 수집")
            
            logger.info(f"\n📊 총 {len(posts)}개의 새로운 게시물 수집 완료 (최근 {self.days}일)")
            return posts
            
        except LoginRequired as e:
            logger.error(f"❌ {username}: 로그인 필요 - 세션이 만료되었습니다")
            
            # 재시도
            if retry_count < MAX_RETRIES:
                wait_time = 60 * (retry_count + 1)  # 1분, 2분씩 증가
                logger.info(f"🔄 세션 재설정 후 {wait_time}초 대기 후 재시도... ({retry_count + 1}/{MAX_RETRIES})")
                
                # 기존 세션 삭제
                if os.path.exists(self.session_file):
                    os.remove(self.session_file)
                    logger.info("🗑️  기존 세션 파일 삭제")
                
                # 대기 후 재로그인
                time.sleep(wait_time)
                
                try:
                    self._login()
                    logger.info("✅ 재로그인 성공, 수집 재개...")
                    time.sleep(5)
                    return self.scrape_channel(username, last_post_url, retry_count + 1)
                except Exception as login_error:
                    logger.error(f"❌ 재로그인 실패: {login_error}")
                    return []
            else:
                logger.error("❌ 최대 재시도 초과 - 나중에 다시 시도하세요")
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
    
    def scrape_post_by_url(self, post_url: str) -> Optional[Dict]:
        """
        게시물 URL로 직접 스크래핑
        
        Args:
            post_url: Instagram 게시물 URL (예: https://www.instagram.com/p/ABC123/)
            
        Returns:
            게시물 데이터 또는 None
        """
        try:
            logger.info(f"📥 게시물 URL 스크래핑 시작: {post_url}")
            
            # URL에서 shortcode 추출
            import re
            match = re.search(r'/p/([^/]+)/', post_url)
            if not match:
                logger.error(f"❌ 유효하지 않은 게시물 URL: {post_url}")
                return None
            
            shortcode = match.group(1)
            logger.info(f"📌 Shortcode: {shortcode}")
            
            # 게시물 정보 가져오기
            # shortcode를 media_pk로 변환
            media_pk = self.client.media_pk_from_code(shortcode)
            logger.info(f"📌 Media PK: {media_pk}")
            
            # media_pk로 정보 조회
            media = self.client.media_info(media_pk)
            
            if not media:
                logger.error(f"❌ 게시물을 찾을 수 없습니다: {shortcode}")
                return None
            
            logger.info(f"✅ 게시물 정보 조회 완료")
            
            # 데이터 추출
            post_data = self._extract_post_data(media)
            
            if post_data:
                logger.info(f"✅ 게시물 데이터 추출 완료")
                
                # 파싱 정보 로깅
                logger.info("\n" + "✨ 게시글 정보 ✨".center(80, "="))
                logger.info(json.dumps({
                    'post_url': post_data.get('post_url'),
                    'post_date': post_data.get('post_date'),
                    'image_count': len(post_data.get('image_urls', [])),
                    '원본 데이터': (media.caption_text or '')[:200] + '...' if len(media.caption_text or '') > 200 else (media.caption_text or '')
                }, ensure_ascii=False, indent=2))
                logger.info("=" * 80 + "\n")
            
            return post_data
            
        except Exception as e:
            logger.error(f"❌ 게시물 스크래핑 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _extract_post_data(self, media) -> Dict:
        """게시물에서 데이터 추출 - 이미지 게시물만 수집"""
        try:
            # media_type 확인 (1=Image, 2=Video, 8=Carousel)
            media_type = getattr(media, 'media_type', 0)
            
            # 단일 영상 게시물은 제외
            if media_type == 2:
                logger.info(f"🎬 영상 게시물 감지 → 건너뛰기")
                return None
            
            image_urls = []
        
            # 1. Carousel (다중 이미지/비디오)
            if hasattr(media, 'resources') and media.resources:
                logger.info(f"📸 Carousel 게시물 감지 (리소스 {len(media.resources)}개)")
                
                # Carousel 내 영상 개수 체크
                video_count = 0
                for resource in media.resources:
                    resource_type = getattr(resource, 'media_type', 0)
                    if resource_type == 2:
                        video_count += 1
                
                # 영상만 있는 Carousel은 제외
                if video_count == len(media.resources):
                    logger.info(f"🎬 영상만 있는 Carousel → 건너뛰기")
                    return None
                
                if video_count > 0:
                    logger.info(f"ℹ️  Carousel 내 영상 {video_count}개는 제외하고 이미지만 수집")
                
                for idx, resource in enumerate(media.resources):
                    resource_type = getattr(resource, 'media_type', 0)
                    
                    # 영상인 경우 건너뛰기
                    if resource_type == 2:
                        logger.info(f"   [{idx+1}] 🎬 영상 리소스 → 건너뛰기")
                        continue
                
                    # 고화질 이미지/썸네일 우선
                    if hasattr(resource, 'image_versions2') and resource.image_versions2:
                        candidates = resource.image_versions2.get('candidates', [])
                        if candidates and len(candidates) > 0:
                            img_url = candidates[0].get('url')
                            if img_url:
                                image_urls.append(str(img_url))
                                logger.info(f"   [{idx+1}] 고화질 이미지: {img_url[:80]}...")
                                continue
                    
                    # 대체: thumbnail_url
                    if hasattr(resource, 'thumbnail_url') and resource.thumbnail_url:
                        image_urls.append(str(resource.thumbnail_url))
                        logger.info(f"   [{idx+1}] 썸네일 이미지: {str(resource.thumbnail_url)[:80]}...")
            
            # 2. 단일 게시물
            else:
                logger.info(f"📷 단일 이미지 게시물 감지")
                
                # 고화질 이미지/썸네일 우선
                if hasattr(media, 'image_versions2') and media.image_versions2:
                    candidates = media.image_versions2.get('candidates', [])
                    if candidates and len(candidates) > 0:
                        img_url = candidates[0].get('url')
                        if img_url:
                            image_urls.append(str(img_url))
                            logger.info(f"   고화질 이미지: {img_url[:80]}...")
                
                # 대체 1: thumbnail_url
                elif hasattr(media, 'thumbnail_url') and media.thumbnail_url:
                    image_urls.append(str(media.thumbnail_url))
                    logger.info(f"   썸네일 이미지: {str(media.thumbnail_url)[:80]}...")
                
                # 대체 2: display_url (최후의 수단)
                elif hasattr(media, 'display_url') and media.display_url:
                    image_urls.append(str(media.display_url))
                    logger.info(f"   디스플레이 이미지: {str(media.display_url)[:80]}...")
            
            # 중복 제거 (순서 유지)
            seen = set()
            unique_urls = []
            for url in image_urls:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)
            
            image_urls = unique_urls
            
            if not image_urls:
                logger.warning(f"⚠️ 이미지 URL을 찾을 수 없습니다")
                logger.warning(f"   media 속성: {dir(media)}")
            else:
                logger.info(f"✅ 총 {len(image_urls)}개 이미지 URL 추출 완료")
            
            caption = media.caption_text or ''
            post_url = f"https://www.instagram.com/p/{media.code}/"
            
            # 최종 데이터
            post_data = {
                'post_id': str(media.code),
                'image_urls': image_urls,
                'caption': caption,
                'post_date': getattr(media.taken_at, 'strftime', lambda fmt: None)('%Y-%m-%d %H:%M:%S'),
                'post_url': post_url,
            }
            return post_data
            
        except Exception as e:
            logger.error(f"❌ 데이터 추출 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None