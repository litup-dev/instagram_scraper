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
# 전체 클럽 일괄 수집
python main.py --mode bulk

# 특정 클럽만 수집 (클럽명)
python main.py --mode single --target "unplugged_stage"

# 특정 클럽만 수집 (URL)
python main.py --mode single --target "https://www.instagram.com/unplugged_stage/"

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