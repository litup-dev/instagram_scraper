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
    단일 게시물 처리 (DB 저장 + 여러 이미지 업로드)
    
    Returns:
        처리 결과 딕셔너리
    """
    result = {
        'success': False,
        'skipped': False,
        'images_uploaded': 0,
        'images_failed': 0,
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
            
            # 여러 이미지 다운로드 및 업로드
            image_urls = post.get('image_urls', [])  # 복수형으로 변경
            
            if image_urls:
                logger.info(f"\n🖼️ 이미지 처리 시작 (총 {len(image_urls)}개)...")
                
                # download_and_upload_multiple_images 사용
                image_results = image_manager.download_and_upload_multiple_images(
                    image_urls=image_urls,
                    perform_id=perform_id
                )
                
                # 각 이미지 결과를 DB에 저장
                for img_result in image_results:
                    image_id = db_manager.insert_performance_image(img_result)
                    
                    if image_id:
                        result['images_uploaded'] += 1
                    else:
                        result['images_failed'] += 1
                
                # 실패한 이미지 수 계산
                result['images_failed'] += (len(image_urls) - len(image_results))
                
                logger.info(f"✅ 이미지 업로드 완료: {result['images_uploaded']}/{len(image_urls)}개")
                
                if result['images_failed'] > 0:
                    logger.warning(f"⚠️ 이미지 업로드 실패: {result['images_failed']}개")
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
        last_post_info = f" (마지막 저장: {club['last_post_url']})" if club['last_post_url'] else " (신규 클럽)"
        logger.info(f"   - {club['name']} (ID: {club['club_id']}){last_post_info}")
    
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
            
            if club['last_post_url']:
                logger.info(f"   📌 마지막 저장 게시물 이후만 수집")
            else:
                logger.info(f"   🆕 신규 클럽 - 전체 게시물 수집")
            
            logger.info("-" * 60)
            
            # 게시물 수집 (마지막 저장 게시물 이후 + 날짜 범위 내)
            posts = scraper.scrape_channel_by_url(
                instagram_url=club['instagram_url'],
                last_post_url=club['last_post_url']
            )
            
            # club_id 추가
            for post in posts:
                post['club_id'] = club['club_id']
            
            logger.info(f"📊 {club['name']} 수집 완료: {len(posts)}개 새 게시물")
            
            # 게시물 처리
            if posts:
                for post in posts:
                    result = process_single_post(post, db_manager, image_manager, club['club_id'])
                    
                    if result['skipped']:
                        total_stats['skipped'] += 1
                    elif result['success']:
                        total_stats['success'] += 1
                        total_stats['images_uploaded'] += result['images_uploaded']
                        total_stats['images_failed'] += result['images_failed']
                    else:
                        total_stats['failed'] += 1
            else:
                logger.info(f"ℹ️ {club['name']}: 새로운 게시물 없음")
            
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
    logger.info(f"   Instagram: {club['instagram_url']}")
    
    if club['last_post_url']:
        logger.info(f"   📌 마지막 저장 게시물: {club['last_post_url']}")
        logger.info(f"   → 이후의 최신 게시물만 수집합니다\n")
    else:
        logger.info(f"   🆕 신규 클럽 - 전체 게시물 수집\n")
    
    # 게시물 수집
    posts = scraper.scrape_channel_by_url(
        instagram_url=club['instagram_url'],
        last_post_url=club['last_post_url']
    )
    
    # club_id 추가
    for post in posts:
        post['club_id'] = club['club_id']
    
    logger.info(f"📊 수집 완료: {len(posts)}개 새 게시물")
    
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
                total_stats['images_uploaded'] += result['images_uploaded']
                total_stats['images_failed'] += result['images_failed']
            else:
                total_stats['failed'] += 1
    else:
        logger.info(f"ℹ️ 새로운 게시물이 없습니다")
    
    return posts, total_stats


def run_post_url_scraping(db_manager, scraper, image_manager, post_url, club_target):
    """게시물 URL로 직접 스크래핑 모드"""
    logger.info(f"{'='*60}")
    logger.info("🔗 게시물 URL 스크래핑 모드")
    logger.info(f"{'='*60}\n")
    
    # 클럽 정보 조회
    club = None
    if club_target:
        if club_target.startswith('http'):
            logger.info(f"📝 Instagram URL로 클럽 조회: {club_target}")
            club = db_manager.get_club_by_instagram_url(club_target)
        else:
            logger.info(f"📝 클럽명으로 조회: {club_target}")
            club = db_manager.get_club_by_name(club_target)
    
    if not club:
        logger.error(f"❌ 클럽을 찾을 수 없습니다: {club_target}")
        return [], {'success': 0, 'skipped': 0, 'failed': 0, 'images_uploaded': 0, 'images_failed': 0}
    
    logger.info(f"✅ 클럽 발견: {club['name']} (ID: {club['club_id']})")
    logger.info(f"📌 게시물 URL: {post_url}\n")
    
    # 게시물 스크래핑
    try:
        post_data = scraper.scrape_post_by_url(post_url)
        
        if not post_data:
            logger.error("❌ 게시물 정보를 가져올 수 없습니다")
            return [], {'success': 0, 'skipped': 0, 'failed': 0, 'images_uploaded': 0, 'images_failed': 0}
        
        # club_id 추가
        post_data['club_id'] = club['club_id']
        
        logger.info(f"✅ 게시물 정보 수집 완료")
        
        total_stats = {
            'success': 0,
            'skipped': 0,
            'failed': 0,
            'images_uploaded': 0,
            'images_failed': 0
        }
        
        # 게시물 처리
        result = process_single_post(post_data, db_manager, image_manager, club['club_id'])
        
        if result['skipped']:
            total_stats['skipped'] += 1
        elif result['success']:
            total_stats['success'] += 1
            total_stats['images_uploaded'] += result['images_uploaded']
            total_stats['images_failed'] += result['images_failed']
        else:
            total_stats['failed'] += 1
        
        return [post_data], total_stats
        
    except Exception as e:
        logger.error(f"❌ 게시물 처리 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return [], {'success': 0, 'skipped': 0, 'failed': 0, 'images_uploaded': 0, 'images_failed': 0}


def print_summary(posts, stats, days=None):
    """최종 결과 출력"""
    logger.info(f"{'='*60}")
    logger.info(f"🎉 스크래핑 작업 완료")
    if days:
        logger.info(f"📅 수집 기간: 최근 {days}일")
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
  # 일괄 수집 (DB의 모든 클럽, 최근 7일)
  python main.py --mode bulk --days 7
  
  # 단건 수집 (클럽명, 최근 3일)
  python main.py --mode single --club "홍대앞FF" --days 3
  
  # 단건 수집 (Instagram URL, 최근 30일)
  python main.py --mode single --club "https://www.instagram.com/hongdaeff/" --days 30
  
  # 게시물 URL로 직접 수집 (클럽명 지정)
  python main.py --mode post --post-url "https://www.instagram.com/p/ABC123/" --club "홍대앞FF"
  
  # 게시물 URL로 직접 수집 (클럽 Instagram URL 지정)
  python main.py --mode post --post-url "https://www.instagram.com/p/ABC123/" --club "https://www.instagram.com/hongdaeff/"
        """
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        choices=['bulk', 'single', 'post'],
        default='bulk',
        help='스크래핑 모드 (bulk: 일괄 수집, single: 단건 수집, post: 게시물 URL 직접 수집)'
    )
    
    parser.add_argument(
        '--club',
        type=str,
        help='클럽 지정 (클럽명 또는 Instagram URL) - single/post 모드에서 필수'
    )
    
    parser.add_argument(
        '--post-url',
        type=str,
        help='게시물 URL (post 모드 전용, 예: https://www.instagram.com/p/ABC123/)'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=1,
        help='수집 기간: 최근 며칠 이내 게시물 (기본값: 1일, post 모드에서는 무시됨)'
    )
    
    args = parser.parse_args()
    
    # 유효성 검증
    if args.mode == 'single' and not args.club:
        parser.error("--mode single 사용 시 --club 필수")
    
    if args.mode == 'post':
        if not args.post_url:
            parser.error("--mode post 사용 시 --post-url 필수")
        if not args.club:
            parser.error("--mode post 사용 시 --club 필수")
    
    if args.days < 1 and args.mode != 'post':
        parser.error("--days는 1 이상이어야 합니다")
    
    logger.info("🚀 Instagram 공연 정보 수집 시스템 시작\n")
    logger.info(f"실행 시간: {datetime.now()}")
    logger.info(f"수집 모드: {args.mode}")
    
    if args.mode == 'post':
        logger.info(f"게시물 URL: {args.post_url}")
        logger.info(f"클럽: {args.club}")
    else:
        logger.info(f"수집 기간: 최근 {args.days}일")
        if args.mode == 'single':
            logger.info(f"클럽: {args.club}")
    
    db_manager = None
    
    try:
        # DB 연결
        logger.info("\n데이터베이스 연결 중...")
        db_manager = DatabaseManager()
        
        # R2 스토리지 초기화
        logger.info("R2 스토리지 연결 중...")
        r2_storage = R2StorageAdapter(R2_CONFIG)
        
        # 이미지 매니저 초기화
        image_manager = ImageManager(r2_storage)
        
        # 스크래퍼 초기화 (일수 전달, post 모드는 무시됨)
        scraper = InstagramScraper(days=args.days if args.mode != 'post' else 1)
        
        # 모드에 따라 실행
        if args.mode == 'bulk':
            posts, stats = run_bulk_scraping(db_manager, scraper, image_manager)
            print_summary(posts, stats, args.days)
        elif args.mode == 'single':
            posts, stats = run_single_scraping(db_manager, scraper, image_manager, args.club)
            print_summary(posts, stats, args.days)
        elif args.mode == 'post':
            posts, stats = run_post_url_scraping(db_manager, scraper, image_manager, args.post_url, args.club)
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