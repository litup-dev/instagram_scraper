# Instagram 공연 정보 수집 시스템

## 기능

- 지정된 인스타그램 채널에서 공연 정보 자동 수집

## 설치

### 의존성 설치:
```bash
pip install -r requirements.txt
```

## 사용법

### 채널 추가

\`config/settings.py\` 파일의 \`CHANNELS\` 리스트에 추가:

```python
CHANNELS = [
    {'username': 'ovantgarde', 'club_id': 1},
    {'username': 'clubbbang', 'club_id': 2},
    {'username': 'hongdaeff', 'club_id': 3},
    {'username': 'unplugged_stage', 'club_id': 4},
    {'username': 'new_channel', 'club_id': 5},  # 새 채널 추가
]
```


## 구조

```python
instagram-concert-scraper/
├── config/
│   └── settings.py              # 설정 파일
├── database/
│   ├── db_manager.py             # DB 연동
│   └── tmp_DDL.sql               # perfom_tmp/perform_img_tmp TABLE DDL
├── scraper/
│   └── instagram_scraper.py     # Instagram 스크래퍼
├── storage/
│   ├── image_manager.py                # 게시물 포스터 이미지 다운로드 및 업로드 
│   └── r2_storage.sql                  # R2 스토리지 연동
├── tests/                       # 테스트 폴더 
│   └── login.py
├── utils/
│   └── logger.py                # 로깅 유틸리티
├── .env
├── main.py                      # 메인 실행 파일
├── requirements.txt
└── README.md
```

## 주의사항

1. **Instagram 로그인**: .env 파일 인스타그램 계정정보 정보 필요

## 추가 구현해야할 사항

- [ ] 실제 이미지 파일 다운로드 및 저장
- [ ] 데이터베이스 연동