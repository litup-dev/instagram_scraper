# Instagram 공연 정보 수집 시스템

## 기능

- 지정된 인스타그램 채널에서 공연 정보 자동 수집

## 설치

### 의존성 설치:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

## 사용법

### 채널 추가

\`config/settings.py\` 파일의 \`CHANNELS\` 리스트에 추가:

\`\`\`python
CHANNELS = [
    {'username': 'ovantgarde', 'club_id': 1},
    {'username': 'clubbbang', 'club_id': 2},
    {'username': 'hongdaeff', 'club_id': 3},
    {'username': 'unplugged_stage', 'club_id': 4},
    {'username': 'new_channel', 'club_id': 5},  # 새 채널 추가
]
\`\`\`

## 구조

\`\`\`
instagram-concert-scraper/
├── config/
│   └── settings.py              # 설정 파일
├── scraper/
│   └── instagram_scraper.py     # Instagram 스크래퍼
├── tests/                         # 테스트 폴더 
│   ├── test_date_extractor.py
│   ├── test_price_extractor.py
│   ├── test_title_extractor.py
│   └── test_artist_extractor.py
├── utils/
│   ├── logger.py                # 로깅 유틸리티
│   └── parser/                    # 파서 모듈화
│       ├── __init__.py           # Parser 클래스 
│       ├── date_extractor.py    # 날짜 추출
│       ├── price_extractor.py   # 가격 추출
│       ├── title_extractor.py   # 제목 추출
│       └── artist_extractor.py  # 아티스트 추출
├── .env
├── main.py                      # 메인 실행 파일
├── requirements.txt
└── README.md
\`\`\`

## 주의사항

1. **Instagram 로그인**: .env 파일 인스타그램 계정정보 정보 필요

## 추가 구현해야할 사항

- [ ] 실제 이미지 파일 다운로드 및 저장
- [ ] 정교한 공연 정보 추출 로직
- [ ] 데이터베이스 연동