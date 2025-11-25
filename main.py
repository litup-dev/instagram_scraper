"""
Instagram 공연 정보 수집 메인 스크립트 (DB 연동 + 이미지 저장)
"""
import time
from datetime import datetime
from scraper.instagram_scraper import InstagramScraper
from database.db_manager import DatabaseManager
from storage.r2_storage import R2StorageAdapter
from storage.image_manager import ImageManager
from config.settings import CHANNELS, R2_CONFIG
from utils.logger import setup_logger

logger = setup_logger('main')

def run_scraping_job():
    """스크래핑 작업 실행 및 DB 저장"""
    db_manager = None
    
    try:
        logger.info(f"{'='*60}")
        logger.info(f"스크래핑 작업 시작: {datetime.now()}")
        logger.info(f"{'='*60}")
        
        # DB 연결
        logger.info("데이터베이스 연결 중...")
        db_manager = DatabaseManager()
        
        # R2 스토리지 초기화
        logger.info("R2 스토리지 연결 중...")
        r2_storage = R2StorageAdapter(R2_CONFIG)
        
        # # 이미지 매니저 초기화
        image_manager = ImageManager(r2_storage)
        
        # 스크래퍼 초기화
        scraper = InstagramScraper()
        
        all_posts = []
        total_stats = {
            'success': 0, 
            'skipped': 0, 
            'failed': 0,
            'images_uploaded': 0,
            'images_failed': 0
        }
        
        for i, channel in enumerate(CHANNELS, 1):
            try:
                logger.info(f"\n[{i}/{len(CHANNELS)}] 📱 채널: {channel['username']}")
                logger.info("-" * 60)
                
                # 게시물 수집
                posts = scraper.scrape_channel(channel['username'])
                
                # club_id 추가
                for post in posts:
                    post['club_id'] = channel['club_id']
                
                logger.info(f"📊 {channel['username']} 수집 완료: {len(posts)}개 게시물")
                
                # DB에 저장 및 이미지 처리
                if posts:
                    logger.info(f"💾 데이터베이스에 저장 중...")
                    
                    for post in posts:
                        try:
                            # 중복 확인
                            if db_manager.check_duplicate_post(post.get('post_url'), post.get('club_id')):
                                logger.info(f"⚠️ 중복 게시물 건너뛰기: {post.get('post_url')}")
                                total_stats['skipped'] += 1
                                continue
                            
                            # 공연 정보 저장
                            perform_id = db_manager.insert_performance(post)
                            
                            if perform_id:
                                total_stats['success'] += 1
                                logger.info(f"✅ 공연 정보 저장 완료 (ID: {perform_id})")
                                
                                # 이미지 다운로드 및 업로드
                                image_url = post.get('image_url')
                                if image_url:
                                    logger.info(f"\n🖼️ 이미지 처리 시작...")
                                    
                                    image_result = image_manager.download_and_upload_image(
                                        image_url=image_url,
                                        perform_id=perform_id,
                                        is_main=True
                                    )
                                    
                                    if image_result:
                                        # 이미지 정보 DB 저장
                                        image_id = db_manager.insert_performance_image(image_result)
                                        
                                        if image_id:
                                            total_stats['images_uploaded'] += 1
                                            logger.info(f"✅ 이미지 저장 완료 (Image ID: {image_id})")
                                        else:
                                            total_stats['images_failed'] += 1
                                            logger.warning(f"⚠️ 이미지 DB 저장 실패")
                                    else:
                                        total_stats['images_failed'] += 1
                                        logger.warning(f"⚠️ 이미지 업로드 실패")
                                else:
                                    logger.info("ℹ️ 이미지 URL 없음")
                                
                            else:
                                total_stats['failed'] += 1
                                logger.warning(f"⚠️ 공연 정보 저장 실패")
                        
                        except Exception as e:
                            logger.error(f"❌ 게시물 처리 오류: {e}")
                            total_stats['failed'] += 1
                            continue
                
                all_posts.extend(posts)
                
                # 채널 간 딜레이
                if i < len(CHANNELS):
                    logger.info("⏸️  다음 채널까지 5초 대기...")
                    time.sleep(5)
                
            except Exception as e:
                logger.error(f"❌ 채널 {channel['username']} 처리 중 오류: {str(e)}")
                continue
        
        # 최종 결과
        logger.info(f"\n{'='*60}")
        logger.info(f"🎉 모든 채널 수집 및 저장 완료")
        logger.info(f"📊 총 수집: {len(all_posts)}개")
        logger.info(f"✅ 공연 정보 저장 성공: {total_stats['success']}개")
        logger.info(f"🖼️ 이미지 업로드 성공: {total_stats['images_uploaded']}개")
        logger.info(f"⏭️  중복 건너뛰기: {total_stats['skipped']}개")
        logger.info(f"❌ 공연 정보 저장 실패: {total_stats['failed']}개")
        logger.info(f"❌ 이미지 업로드 실패: {total_stats['images_failed']}개")
        logger.info(f"{'='*60}\n")
        
        return all_posts, total_stats
        
    except Exception as e:
        logger.error(f"❌ 스크래핑 작업 실행 중 오류: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return [], {
            'success': 0, 
            'skipped': 0, 
            'failed': 0, 
            'images_uploaded': 0, 
            'images_failed': 0
        }
    
    finally:
        # DB 연결 종료
        if db_manager:
            db_manager.close_all_connections()
            logger.info("🔌 데이터베이스 연결 종료")

def main():
    logger.info("🚀 Instagram 공연 정보 수집 시스템 시작\n")
    posts, stats = run_scraping_job()
    logger.info("👋 프로그램 종료")

if __name__ == "__main__":
    main()