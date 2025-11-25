"""
Instagram 공연 정보 수집 메인 스크립트
"""
import time
import argparse
from datetime import datetime
from scraper.instagram_scraper import InstagramScraper
from database.db_manager import DatabaseManager
from storage.r2_storage import R2StorageAdapter
from storage.image_manager import ImageManager
from config.settings import R2_CONFIG
from utils.logger import setup_logger

logger = setup_logger('main')


def process_single_post(post, db_manager, image_manager, club_id):
    """
    단일 게시물 처리 (DB 저장 + 이미지 업로드)
    
    Returns:
        처리 결과 딕셔너리
    """
    result = {
        'success': False,
        'skipped': False,
        'image_uploaded': False,
        'error': None
    }
    
    try:
        # 중복 확인
        if db_manager.check_duplicate_post(post.get('post_url'), club_id):
            logger.info(f"⚠️ 중복 게시물 건너뛰기: {post.get('post_url')}")
            result['skipped'] = True
            return result
        
        # 공연 정보 저장
        perform_id = db_manager.insert_performance(post)
        
        if perform_id:
            result['success'] = True
            
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
                        result['image_uploaded'] = True
                    else:
                        logger.warning(f"⚠️ 이미지 DB 저장 실패")
                else:
                    logger.warning(f"⚠️ 이미지 업로드 실패")
            else:
                logger.info("ℹ️ 이미지 URL 없음")
        else:
            result['error'] = "공연 정보 저장 실패"
            logger.warning(f"⚠️ 공연 정보 저장 실패")
    
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"❌ 게시물 처리 오류: {e}")
    
    return result


def run_bulk_scraping(db_manager, scraper, image_manager):
    """일괄 스크래핑 모드"""
    logger.info(f"{'='*60}")
    logger.info("🔄 일괄 스크래핑 모드")
    logger.info(f"{'='*60}\n")
    
    # DB에서 Instagram 연동 클럽 목록 가져오기
    clubs = db_manager.get_clubs_with_instagram()
    
    if not clubs:
        logger.error("❌ Instagram 연동 클럽이 없습니다")
        return [], {'success': 0, 'skipped': 0, 'failed': 0, 'images_uploaded': 0, 'images_failed': 0}
    
    logger.info(f"📊 총 {len(clubs)}개 클럽 발견")
    for club in clubs:
        logger.info(f"   - {club['name']} (ID: {club['club_id']}): {club['instagram_url']}")
    
    all_posts = []
    total_stats = {
        'success': 0,
        'skipped': 0,
        'failed': 0,
        'images_uploaded': 0,
        'images_failed': 0
    }
    
    for i, club in enumerate(clubs, 1):
        try:
            logger.info(f"\n[{i}/{len(clubs)}] 📱 클럽: {club['name']}")
            logger.info(f"   Instagram: {club['instagram_url']}")
            logger.info("-" * 60)
            
            # 게시물 수집
            posts = scraper.scrape_channel_by_url(club['instagram_url'])
            
            # club_id 추가
            for post in posts:
                post['club_id'] = club['club_id']
            
            logger.info(f"📊 {club['name']} 수집 완료: {len(posts)}개 게시물")
            
            # 게시물 처리
            if posts:
                for post in posts:
                    result = process_single_post(post, db_manager, image_manager, club['club_id'])
                    
                    if result['skipped']:
                        total_stats['skipped'] += 1
                    elif result['success']:
                        total_stats['success'] += 1
                        if result['image_uploaded']:
                            total_stats['images_uploaded'] += 1
                        else:
                            total_stats['images_failed'] += 1
                    else:
                        total_stats['failed'] += 1
            
            all_posts.extend(posts)
            
            # 클럽 간 딜레이
            if i < len(clubs):
                logger.info("⏸️  다음 클럽까지 5초 대기...")
                time.sleep(5)
        
        except Exception as e:
            logger.error(f"❌ 클럽 {club['name']} 처리 중 오류: {str(e)}")
            continue
    
    return all_posts, total_stats


def run_single_scraping(db_manager, scraper, image_manager, target):
    """단건 스크래핑 모드"""
    logger.info(f"{'='*60}")
    logger.info("🎯 단건 스크래핑 모드")
    logger.info(f"{'='*60}\n")
    
    club = None
    
    # URL인지 클럽명인지 판단
    if target.startswith('http'):
        logger.info(f"📝 Instagram URL로 조회: {target}")
        club = db_manager.get_club_by_instagram_url(target)
    else:
        logger.info(f"📝 클럽명으로 조회: {target}")
        club = db_manager.get_club_by_name(target)
    
    if not club:
        logger.error(f"❌ 클럽을 찾을 수 없습니다: {target}")
        return [], {'success': 0, 'skipped': 0, 'failed': 0, 'images_uploaded': 0, 'images_failed': 0}
    
    logger.info(f"✅ 클럽 발견: {club['name']} (ID: {club['club_id']})")
    logger.info(f"   Instagram: {club['instagram_url']}\n")
    
    # 게시물 수집
    posts = scraper.scrape_channel_by_url(club['instagram_url'])
    
    # club_id 추가
    for post in posts:
        post['club_id'] = club['club_id']
    
    logger.info(f"📊 수집 완료: {len(posts)}개 게시물")
    
    total_stats = {
        'success': 0,
        'skipped': 0,
        'failed': 0,
        'images_uploaded': 0,
        'images_failed': 0
    }
    
    # 게시물 처리
    if posts:
        for post in posts:
            result = process_single_post(post, db_manager, image_manager, club['club_id'])
            
            if result['skipped']:
                total_stats['skipped'] += 1
            elif result['success']:
                total_stats['success'] += 1
                if result['image_uploaded']:
                    total_stats['images_uploaded'] += 1
                else:
                    total_stats['images_failed'] += 1
            else:
                total_stats['failed'] += 1
    
    return posts, total_stats


def print_summary(posts, stats):
    """최종 결과 출력"""
    logger.info(f"{'='*60}")
    logger.info(f"🎉 스크래핑 작업 완료")
    logger.info(f"📊 총 수집: {len(posts)}개")
    logger.info(f"✅ 공연 정보 저장 성공: {stats['success']}개")
    logger.info(f"🖼️ 이미지 업로드 성공: {stats['images_uploaded']}개")
    logger.info(f"⏭️  중복 건너뛰기: {stats['skipped']}개")
    logger.info(f"❌ 공연 정보 저장 실패: {stats['failed']}개")
    logger.info(f"❌ 이미지 업로드 실패: {stats['images_failed']}개")
    logger.info(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Instagram 공연 정보 수집 시스템',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 일괄 수집 (DB의 모든 클럽)
  python main.py --mode bulk
  
  # 단건 수집 (클럽명)
  python main.py --mode single --target "홍대앞FF"
  
  # 단건 수집 (Instagram URL)
  python main.py --mode single --target "https://www.instagram.com/hongdaeff/"
        """
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        choices=['bulk', 'single'],
        default='bulk',
        help='스크래핑 모드 (bulk: 일괄 수집, single: 단건 수집)'
    )
    
    parser.add_argument(
        '--target',
        type=str,
        help='단건 수집 시 대상 (클럽명 또는 Instagram URL)'
    )
    
    args = parser.parse_args()
    
    # 단건 모드인데 target이 없으면 에러
    if args.mode == 'single' and not args.target:
        parser.error("--mode single 사용 시 --target 필수")
    
    logger.info("🚀 Instagram 공연 정보 수집 시스템 시작\n")
    logger.info(f"실행 시간: {datetime.now()}")
    
    db_manager = None
    
    try:
        # DB 연결
        logger.info("데이터베이스 연결 중...")
        db_manager = DatabaseManager()
        
        # R2 스토리지 초기화
        logger.info("R2 스토리지 연결 중...")
        r2_storage = R2StorageAdapter(R2_CONFIG)
        
        # 이미지 매니저 초기화
        image_manager = ImageManager(r2_storage)
        
        # 스크래퍼 초기화
        scraper = InstagramScraper()
        
        # 모드에 따라 실행
        if args.mode == 'bulk':
            posts, stats = run_bulk_scraping(db_manager, scraper, image_manager)
        else:
            posts, stats = run_single_scraping(db_manager, scraper, image_manager, args.target)
        
        # 결과 출력
        print_summary(posts, stats)
        
    except Exception as e:
        logger.error(f"❌ 실행 중 오류: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    finally:
        # DB 연결 종료
        if db_manager:
            db_manager.close_all_connections()
            logger.info("🔌 데이터베이스 연결 종료")
    
    logger.info("👋 프로그램 종료")


if __name__ == "__main__":
    main()