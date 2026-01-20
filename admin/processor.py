"""
공연 데이터 처리 로직
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from utils.logger import setup_logger
from config.settings import R2_CONFIG

logger = setup_logger('processor')

class PerformanceProcessor:
    def __init__(self, db_manager):
        self.db = db_manager
        self.r2_base_url = f"{R2_CONFIG['endpoint_url']}/{R2_CONFIG['bucket_name']}"
    
    def get_statistics(self) -> Dict:
        """통계 정보 조회 (title 유무로 완료/미완료 판단)"""
        conn = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN title IS NULL OR title = '' THEN 1 END) as pending,
                    COUNT(CASE WHEN title IS NOT NULL AND title != '' THEN 1 END) as completed
                FROM perform_tmp;
            """
            
            cursor.execute(query)
            row = cursor.fetchone()
            
            total, pending, completed = row
            
            return {
                'total': total,
                'pending': pending,
                'completed': completed,
                'rejected': 0,  # 거부 기능은 삭제로 대체
                'pending_rate': (pending / total * 100) if total > 0 else 0,
                'completed_rate': (completed / total * 100) if total > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"통계 조회 오류: {e}")
            return {
                'total': 0,
                'pending': 0,
                'completed': 0,
                'rejected': 0,
                'pending_rate': 0,
                'completed_rate': 0
            }
        finally:
            if conn:
                cursor.close()
                self.db.return_connection(conn)
    
    def get_club_list(self) -> List[str]:
        """클럽 목록 조회"""
        conn = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT DISTINCT c.name
                FROM club_tb c
                INNER JOIN perform_tmp p ON p.club_id = c.id
                ORDER BY c.name;
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            return [row[0] for row in rows]
            
        except Exception as e:
            logger.error(f"클럽 목록 조회 오류: {e}")
            return []
        finally:
            if conn:
                cursor.close()
                self.db.return_connection(conn)
    
    def get_posts(
        self,
        status: str = "전체",
        club: Optional[str] = None,
        days: int = 7
    ) -> List[Dict]:
        """게시물 목록 조회 (title 유무로 완료/미완료 판단)"""
        conn = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # 쿼리 구성
            query = """
                SELECT 
                    p.id,
                    p.club_id,
                    c.name as club_name,
                    p.title,
                    p.description,
                    p.perform_date,
                    p.booking_price,
                    p.onsite_price,
                    p.booking_url,
                    p.artists,
                    p.is_cancelled,
                    p.sns_links,
                    p.created_at,
                    p.updated_at
                FROM perform_tmp p
                INNER JOIN club_tb c ON c.id = p.club_id
                WHERE p.created_at >= NOW() - INTERVAL '%s days'
            """
            params = [days]
            
            # 상태 필터 (title 유무로 판단)
            if status == "미처리":
                query += " AND (p.title IS NULL OR p.title = '')"
            elif status == "완료":
                query += " AND p.title IS NOT NULL AND p.title != ''"
            # "전체"는 조건 추가 안 함
            
            if club:
                query += " AND c.name = %s"
                params.append(club)
            
            query += " ORDER BY p.created_at DESC;"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            posts = []
            for row in rows:
                # Instagram URL 추출
                sns_links = row[11]
                post_url = ''
                if sns_links:
                    if isinstance(sns_links, list) and len(sns_links) > 0:
                        post_url = sns_links[0].get('instagram', '')
                    elif isinstance(sns_links, dict):
                        post_url = sns_links.get('instagram', '')
                
                # 상태 판단 (title 유무)
                has_title = row[3] and row[3].strip()
                status_value = 'completed' if has_title else 'pending'
                status_text = '✅ 완료' if has_title else '⏳ 미처리'
                
                # 아티스트 파싱
                artists = row[9]
                if isinstance(artists, str):
                    artists = json.loads(artists) if artists else []
                
                posts.append({
                    'id': row[0],
                    'club_id': row[1],
                    'club_name': row[2],
                    'title': row[3],
                    'description': row[4],
                    'perform_date': row[5],
                    'perform_time': row[5].time() if row[5] else None,
                    'booking_price': row[6] or 0,
                    'onsite_price': row[7] or 0,
                    'booking_url': row[8],
                    'artists': artists,
                    'is_cancelled': row[10],
                    'post_url': post_url,
                    'status': status_value,
                    'status_text': status_text,
                    'created_at': row[12].strftime('%Y-%m-%d %H:%M'),
                    'updated_at': row[13].strftime('%Y-%m-%d %H:%M') if row[13] else ''
                })
            
            return posts
            
        except Exception as e:
            logger.error(f"게시물 조회 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
        finally:
            if conn:
                cursor.close()
                self.db.return_connection(conn)
    
    def get_post_images(self, perform_id: int) -> List[Dict]:
        """게시물 이미지 조회 (Signed URL 생성)"""
        conn = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    id,
                    file_path,
                    is_main,
                    original_name
                FROM perform_img_tmp
                WHERE perform_id = %s
                ORDER BY is_main DESC, id ASC;
            """
            
            cursor.execute(query, (perform_id,))
            rows = cursor.fetchall()
            
            images = []
            for i, row in enumerate(rows):
                file_path = row[1]
                
                # Signed URL 생성 (1시간 유효)
                try:
                    from storage.r2_storage import R2StorageAdapter
                    r2_storage = R2StorageAdapter(R2_CONFIG)
                    image_url = r2_storage.generate_presigned_url(file_path, expires_in=3600)
                except Exception as e:
                    logger.error(f"Signed URL 생성 실패: {e}")
                    # 실패 시 기본 URL (작동 안 할 수 있음)
                    image_url = f"{self.r2_base_url}/{file_path}"
                
                images.append({
                    'id': row[0],
                    'url': image_url,
                    'is_main': row[2],
                    'original_name': row[3],
                    'index': i
                })
            
            return images
            
        except Exception as e:
            logger.error(f"이미지 조회 오류: {e}")
            return []
        finally:
            if conn:
                cursor.close()
                self.db.return_connection(conn)
    
    def save_performance(self, data: Dict) -> bool:
        """공연 데이터 저장 (perform_tmp 업데이트만)"""
        conn = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # artists를 JSON으로 변환
            artists_json = json.dumps(data['artists'], ensure_ascii=False) if data['artists'] else None
            
            query = """
                UPDATE perform_tmp
                SET 
                    title = %s,
                    perform_date = %s,
                    booking_price = %s,
                    onsite_price = %s,
                    booking_url = %s,
                    artists = %s::jsonb,
                    is_cancelled = %s,
                    updated_at = NOW()
                WHERE id = %s;
            """
            
            cursor.execute(query, (
                data['title'],
                data['perform_date'],
                data['booking_price'],
                data['onsite_price'],
                data['booking_url'],
                artists_json,
                data['is_cancelled'],
                data['perform_id']
            ))
            
            conn.commit()
            logger.info(f"공연 데이터 저장 완료: {data['perform_id']}")
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"공연 데이터 저장 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        finally:
            if conn:
                cursor.close()
                self.db.return_connection(conn)
    
    def reject_performance(self, perform_id: int) -> bool:
        """공연 거부 처리 (삭제로 대체)"""
        return self.delete_performance(perform_id)
    
    def delete_performance(self, perform_id: int) -> bool:
        """공연 삭제"""
        conn = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # 이미지 먼저 삭제 (FK 제약)
            cursor.execute("DELETE FROM perform_img_tmp WHERE perform_id = %s;", (perform_id,))
            
            # 공연 삭제
            cursor.execute("DELETE FROM perform_tmp WHERE id = %s;", (perform_id,))
            
            conn.commit()
            
            logger.info(f"공연 삭제: {perform_id}")
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"공연 삭제 오류: {e}")
            return False
        finally:
            if conn:
                cursor.close()
                self.db.return_connection(conn)