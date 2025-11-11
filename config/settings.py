import os
from dotenv import load_dotenv

load_dotenv()

# 인스타그램 계정 정보 (선택사항)
INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME', '')
INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD', '')

# 수집 대상 채널
CHANNELS = [
    {'username': 'ovantgarde', 'club_id': 1},
    {'username': 'clubbbang', 'club_id': 2},
    {'username': 'hongdaeff', 'club_id': 3},
    {'username': 'unplugged_stage', 'club_id': 4},
]

# 로그 설정
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = 'logs/scraper.log'
