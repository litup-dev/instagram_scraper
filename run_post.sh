#!/bin/bash
# run_post.sh - 게시물 URL 직접 수집 스크립트

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "사용법: ./run_post.sh <게시물 URL> <클럽명 또는 Instagram URL>"
    echo ""
    echo "예시:"
    echo "  ./run_post.sh \"https://www.instagram.com/p/ABC123/\" \"홍대앞FF\""
    echo "  ./run_post.sh \"https://www.instagram.com/p/ABC123/\" \"https://www.instagram.com/hongdaeff/\""
    exit 1
fi

POST_URL=$1
CLUB=$2

echo "=========================================="
echo "Instagram 게시물 직접 수집 시작"
echo "=========================================="
echo "게시물 URL: ${POST_URL}"
echo "클럽: ${CLUB}"
echo ""

python3 main.py --mode post --post-url "${POST_URL}" --club "${CLUB}"

echo ""
echo "=========================================="
echo "수집 완료"
echo "=========================================="