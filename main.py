"""
Instagram 공연 정보 수집 메인 스크립트
"""
import time
from datetime import datetime
from scraper.instagram_scraper import InstagramScraper
from config.settings import CHANNELS
from utils.logger import setup_logger

logger = setup_logger('main')

def run_scraping_job():
    """스크래핑 작업 실행"""
    try:
        logger.info(f"{'='*60}")
        logger.info(f"스크래핑 작업 시작: {datetime.now()}")
        logger.info(f"{'='*60}")
        
        scraper = InstagramScraper()
        
        all_posts = []
        
        for i, channel in enumerate(CHANNELS, 1):
            try:
                logger.info(f"\n[{i}/{len(CHANNELS)}] 📱 채널: {channel['username']}")
                logger.info("-" * 60)
                
                posts = scraper.scrape_channel(channel['username'])
                
                # club_id 추가
                for post in posts:
                    post['club_id'] = channel['club_id']
                    all_posts.append(post)
                
                logger.info(f"✅ {channel['username']} 완료: {len(posts)}개 게시물")
                
                # 채널 간 딜레이 (Rate limit 방지)
                if i < len(CHANNELS):
                    logger.info("⏸️  다음 채널까지 5초 대기...")
                    time.sleep(5)
                
            except Exception as e:
                logger.error(f"❌ 채널 {channel['username']} 수집 중 오류: {str(e)}")
                continue
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🎉 모든 채널 수집 완료")
        logger.info(f"📊 총 {len(all_posts)}개의 공연 게시물 수집")
        logger.info(f"{'='*60}\n")
        
        return all_posts
        
    except Exception as e:
        logger.error(f"❌ 스크래핑 작업 실행 중 오류: {str(e)}")
        return []

def main():
    logger.info("Instagram 공연 정보 수집 시스템 시작\n")
    posts = run_scraping_job()

if __name__ == "__main__":
    main()