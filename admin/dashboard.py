"""
Streamlit 기반 공연 데이터 관리 대시보드
"""
import streamlit as st
import sys
import os
from datetime import datetime

# 프로젝트 루트를 path에 추가 (admin 폴더에서 실행 시 대비)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from database.db_manager import DatabaseManager
from admin.processor import PerformanceProcessor

# 페이지 설정
st.set_page_config(
    page_title="LITUP공연관리",
    page_icon="🎵",
    layout="wide"
)

# 세션 초기화
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager()
    st.session_state.processor = PerformanceProcessor(st.session_state.db_manager)

db = st.session_state.db_manager
processor = st.session_state.processor

# 사이드바
st.sidebar.title("🎵 공연 데이터 관리")
st.sidebar.markdown("---")

# 필터
status_filter = st.sidebar.selectbox(
    "상태",
    ["전체", "미처리", "완료"]
)

club_filter = st.sidebar.selectbox(
    "클럽",
    ["전체"] + processor.get_club_list()
)

date_range = st.sidebar.slider(
    "수집 날짜",
    min_value=30,
    max_value=1,
    value=60,
    step=1,
    format="%d일 전"
)

# 메인 화면
st.title("🎵 Instagram 공연 데이터 관리")
st.markdown("---")

# 통계
col1, col2, col3 = st.columns(3)

stats = processor.get_statistics()

with col1:
    st.metric("전체", stats['total'])
with col2:
    st.metric("미처리", stats['pending'], delta=f"{stats['pending_rate']:.1f}%")
with col3:
    st.metric("완료", stats['completed'], delta=f"{stats['completed_rate']:.1f}%")

st.markdown("---")

# 데이터 로드
posts = processor.get_posts(
    status=status_filter,
    club=club_filter if club_filter != "전체" else None,
    days=date_range
)

st.subheader(f"📋 게시물 목록 ({len(posts)}개)")

if not posts:
    st.info("표시할 게시물이 없습니다.")
else:
    # 게시물 표시
    for post in posts:
        with st.expander(
            f"🎪 {post['club_name']} | {post['created_at']} | {post['status_text']}",
            expanded=False
        ):
            # 2단 레이아웃
            col_left, col_right = st.columns([1, 2])
            
            with col_left:
                st.markdown("### 📸 이미지")
                
                # 이미지 표시
                images = processor.get_post_images(post['id'])
                if images:
                    for img in images:
                        st.image(
                            img['url'],
                            caption=f"이미지 {img['index'] + 1}",
                            use_column_width=True
                        )
                else:
                    st.warning("이미지 없음")
                
                st.markdown("### 📝 원본 데이터")
                st.text_area(
                    "캡션",
                    value=post['description'] or '',
                    height=150,
                    disabled=True,
                    key=f"caption_{post['id']}"
                )
                
                st.markdown(f"**Instagram URL:**")
                st.markdown(f"[게시물 보기]({post['post_url']})")
            
            with col_right:
                st.markdown("### ✏️ 데이터 입력")
                
                with st.form(key=f"form_{post['id']}"):
                    # 제목
                    title = st.text_input(
                        "공연 제목 *",
                        value=post.get('title', ''),
                        placeholder="예: 힙합 파티 나이트",
                        key=f"title_{post['id']}"
                    )
                    
                    # 날짜/시간
                    col_date, col_time = st.columns(2)
                    with col_date:
                        perform_date = st.date_input(
                            "공연 날짜 *",
                            value=post.get('perform_date') or datetime.now().date(),
                            key=f"date_{post['id']}"
                        )
                    
                    with col_time:
                        perform_time = st.time_input(
                            "공연 시간",
                            value=post.get('perform_time') or None,
                            key=f"time_{post['id']}"
                        )
                    
                    # 가격
                    col_booking, col_onsite = st.columns(2)
                    with col_booking:
                        booking_price = st.number_input(
                            "예매 가격 (원)",
                            min_value=0,
                            value=post.get('booking_price', 0),
                            step=1000,
                            key=f"booking_{post['id']}"
                        )
                    
                    with col_onsite:
                        onsite_price = st.number_input(
                            "현장 가격 (원)",
                            min_value=0,
                            value=post.get('onsite_price', 0),
                            step=1000,
                            key=f"onsite_{post['id']}"
                        )
                    
                    # 예매 URL
                    booking_url = st.text_input(
                        "예매 링크",
                        value=post.get('booking_url', ''),
                        placeholder="https://...",
                        key=f"booking_url_{post['id']}"
                    )
                    
                    # 아티스트
                    artists = st.text_area(
                        "아티스트 (쉼표로 구분)",
                        value=', '.join(post.get('artists', [])) if post.get('artists') else '',
                        placeholder="DJ A, MC B, 밴드 C",
                        height=80,
                        key=f"artists_{post['id']}"
                    )
                    
                    # 취소 여부
                    is_cancelled = st.checkbox(
                        "공연 취소됨",
                        value=post.get('is_cancelled', False),
                        key=f"cancelled_{post['id']}"
                    )
                    
                    # 버튼
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        submitted = st.form_submit_button(
                            "✅ 저장",
                            type="primary",
                            use_container_width=True
                        )
                    
                    with col_btn2:
                        deleted = st.form_submit_button(
                            "🗑️ 삭제",
                            use_container_width=True
                        )
                    
                    # 처리
                    if submitted:
                        if not title or not perform_date:
                            st.error("제목과 날짜는 필수입니다!")
                        else:
                            # 날짜/시간 결합
                            perform_datetime = datetime.combine(
                                perform_date,
                                perform_time if perform_time else datetime.min.time()
                            )
                            
                            # 아티스트 파싱
                            artist_list = [a.strip() for a in artists.split(',') if a.strip()]
                            
                            # 데이터 저장
                            data = {
                                'perform_id': post['id'],
                                'title': title,
                                'perform_date': perform_datetime,
                                'booking_price': booking_price,
                                'onsite_price': onsite_price,
                                'booking_url': booking_url if booking_url else None,
                                'artists': artist_list,
                                'is_cancelled': is_cancelled
                            }
                            
                            if processor.save_performance(data):
                                st.success("✅ 저장되었습니다!")
                                st.rerun()
                            else:
                                st.error("❌ 저장 실패")
                    
                    if deleted:
                        if processor.delete_performance(post['id']):
                            st.warning("🗑️ 삭제되었습니다.")
                            st.rerun()
                        else:
                            st.error("삭제 실패")

# 하단 정보
st.markdown("---")
st.caption("💡 Tip: 이미지를 보고 제목, 날짜, 가격을 입력하세요. 제목을 입력하면 '완료' 상태가 됩니다.")