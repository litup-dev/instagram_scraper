#!/bin/bash
# start_cron.sh - 크론잡 간단 설정

# 현재 스크립트가 있는 디렉토리의 절대 경로 저장
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 시스템의 python3 실행 파일 경로 찾기
PYTHON_PATH=$(which python3)

echo "=========================================="
echo "Instagram 스크래퍼 크론잡 설정"
echo "=========================================="
echo ""
echo "경로 확인:"
echo "  프로젝트: ${SCRIPT_DIR}"
echo "  Python: ${PYTHON_PATH}"
echo ""

# logs 디렉토리 생성
mkdir -p "${SCRIPT_DIR}/logs"

# 기존 크론 백업
crontab -l > "${SCRIPT_DIR}/crontab_backup.txt" 2>/dev/null || true

# 임시 파일에 크론 작성
TEMP_CRON=$(mktemp)

# 기존 크론 가져오기 (이 스크립트 관련 제외)
crontab -l 2>/dev/null | grep -v "instagram.*main.py" > "$TEMP_CRON" || true

# 빈 줄이 있으면 마지막에 개행 추가
if [ -s "$TEMP_CRON" ]; then
    echo "" >> "$TEMP_CRON"
fi

# 새 크론 추가 (작은따옴표로 경로 감싸기)
cat >> "$TEMP_CRON" << EOF
# Instagram Scraper - Daily
0 14 * * * cd '${SCRIPT_DIR}' && '${PYTHON_PATH}' '${SCRIPT_DIR}/main.py' --mode bulk --days 1 >> '${SCRIPT_DIR}/logs/cron.log' 2>&1
EOF

echo "등록할 크론 내용:"
echo "----------------------------------------"
cat "$TEMP_CRON"
echo "----------------------------------------"
echo ""

# 크론 등록
if crontab "$TEMP_CRON" 2>/dev/null; then
    echo "✅ 크론잡 등록 완료!"
    echo ""
    echo "📋 등록된 크론:"
    crontab -l | grep -A 1 "Instagram"
    echo ""
    echo "💡 로그 확인: tail -f '${SCRIPT_DIR}/logs/cron.log'"
    echo "💡 크론 확인: crontab -l"
    echo "💡 크론 삭제: crontab -e (편집기에서 해당 라인 삭제)"
else
    echo "❌ 크론잡 등록 실패"
    echo ""
    echo "수동 등록 방법:"
    echo "1. crontab -e 실행"
    echo "2. 아래 내용 추가:"
    echo ""
    echo "0 9 * * * cd '${SCRIPT_DIR}' && '${PYTHON_PATH}' '${SCRIPT_DIR}/main.py' --mode bulk --days 1 >> '${SCRIPT_DIR}/logs/cron.log' 2>&1"
    echo ""
fi

# 임시 파일 삭제
rm -f "$TEMP_CRON"