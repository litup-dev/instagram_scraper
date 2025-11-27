# Instagram 공연 정보 수집 시스템

## 기능

- 지정된 인스타그램 채널에서 공연 정보 자동 수집

## 설치

### 의존성 설치:
```bash
pip install -r requirements.txt
```

## 사용법
```bash

# 일괄 수집 (기본값 1일)
python main.py --mode bulk

# 일괄 수집 (DB의 모든 클럽, 최근 7일 이내 게시물)
python main.py --mode bulk --days 7

# 클럽별 수집 (클럽명, 최근 3일 이내 게시물)
python main.py --mode single --club "hongdaeff" --days 3

# 클럽별 수집 (Instagram URL, 최근 3일 이내 게시물)
python main.py --mode single --club "https://www.instagram.com/hongdaeff/" --days 3

# 특정 게시물 수집 (클럽명)
python main.py --mode post --post-url "https://www.instagram.com/p/DRgoKSxkYDI/" --club "strangefruit.seoul"

# 특정 게시물 수집 (Instagram URL)
python main.py --mode post --post-url "https://www.instagram.com/p/DRgoKSxkYDI/" --club "https://www.instagram.com/strangefruit.seoul/"


# 도움말 확인
python main.py --help
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