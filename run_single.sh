#!/bin/bash
# run_single.sh - 단건 수집 스크립트

if [ -z "$1" ]; then
    echo "사용법: ./run_single.sh <클럽명 또는 Instagram URL> [일수]"
    echo ""
    echo "예시:"
    echo "  ./run_single.sh \"홍대앞FF\" 3"
    echo "  ./run_single.sh \"https://www.instagram.com/hongdaeff/\" 7"
    exit 1
fi

CLUB=$1
DAYS=${2:-1}

echo "=========================================="
echo "Instagram 단건 수집 시작"
echo "=========================================="
echo "클럽: ${CLUB}"
echo "수집 기간: 최근 ${DAYS}일"
echo ""

python3 main.py --mode single --club "${CLUB}" --days ${DAYS}

echo ""
echo "=========================================="
echo "수집 완료"
echo "=========================================="