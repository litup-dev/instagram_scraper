"""
PostgreSQL 데이터베이스 관리자
"""
import psycopg2
from psycopg2.extras import Json, RealDictCursor
from psycopg2 import pool
from datetime import datetime
from typing import List, Dict, Optional
import json
from utils.logger import setup_logger
from config.settings import DB_CONFIG
import dateparser

logger = setup_logger('db_manager')


class DatabaseManager:
    def __init__(self):
        """데이터베이스 연결 풀 초기화"""
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                database=DB_CONFIG['database'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password']
            )
            logger.info("✅ 데이터베이스 연결 완료")
        except Exception as e:
            logger.error(f"❌ 데이터베이스 연결 실패: {e}")
            raise

    def get_connection(self):
        """연결 풀에서 연결 가져오기"""
        return self.connection_pool.getconn()

    def return_connection(self, conn):
        """연결을 풀에 반환"""
        self.connection_pool.putconn(conn)

    def close_all_connections(self):
        """모든 연결 종료"""
        self.connection_pool.closeall()
        logger.info("✅ 모든 데이터베이스 연결 종료")

    def insert_performance(self, post_data: Dict) -> Optional[int]:
        """
        공연 정보 삽입
        
        Args:
            post_data: 스크래핑된 게시물 데이터
            
        Returns:
            삽입된 레코드의 ID, 실패 시 None
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # artists 데이터 
            artists_json = json.dumps(post_data.get('artists', []), ensure_ascii=False)
            
            # sns_links 데이터 준비
            sns_links = {
                'instagram': post_data.get('post_url', ''),
            }
            sns_links_json = json.dumps(sns_links, ensure_ascii=False)

            # perform_date 파싱
            perform_date = None
            if post_data.get('perform_date'):
                try:
                    perform_date = dateparser.parse(post_data['perform_date'])
                except ValueError:
                    logger.warning(f"⚠️ 날짜 형식 오류: {post_data.get('perform_date')}")
            
            # price
            booking_price = None
            onsite_price = None
            if post_data.get("booking_price") is not None:
                try:
                    booking_price = int(post_data["booking_price"])
                except Exception:
                    logger.warning(f"⚠️ booking_price 형식 오류: {post_data.get('booking_price')}")
            if post_data.get("onsite_price") is not None:
                try:
                    onsite_price = int(post_data["onsite_price"])
                except Exception:
                    logger.warning(f"⚠️ onsite_price 형식 오류: {post_data.get('onsite_price')}")
            
            # INSERT 쿼리
            insert_query = """
                INSERT INTO perform_tb (
                    club_id, 
                    user_id, 
                    artists, 
                    sns_links, 
                    onsite_price, 
                    perform_date, 
                    booking_price, 
                    is_cancelled, 
                    title, 
                    description, 
                    booking_url
                ) VALUES (
                    %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING id;
            """

            cursor.execute(insert_query, (
                post_data.get('club_id'),
                1,  # user_id는 임시로 1로 고정
                artists_json,
                sns_links_json,
                onsite_price,
                perform_date,
                booking_price,
                False,  # is_cancelled
                post_data.get('title', ''),
                post_data.get('caption', ''),
                None  # booking_url (추후 추가)
            ))

            # 삽입된 ID 가져오기
            inserted_id = cursor.fetchone()[0]
            conn.commit()

            logger.info(f"✅ 공연 정보 저장 완료 (ID: {inserted_id})")
            logger.info(f"   제목: {post_data.get('title', '')}")
            logger.info(f"   클럽: {post_data.get('club_id')}")
            
            return inserted_id

        except psycopg2.IntegrityError as e:
            if conn:
                conn.rollback()
            logger.warning(f"⚠️ 중복 데이터 또는 제약조건 위반: {e}")
            return None

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ 데이터베이스 삽입 오류: {e}")
            logger.error(f"   문제 데이터: {post_data.get('post_url', 'N/A')}")
            return None

        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def check_duplicate_post(self, instagram_url: str, club_id: int) -> bool:
        """
        중복 게시물 확인
        
        Args:
            post_id: Instagram 게시물 ID
            club_id: 클럽 ID
            
        Returns:
            중복이면 True, 아니면 False
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT COUNT(*) 
                FROM perform_tb 
                WHERE sns_links->>'instagram' = %s
                AND club_id = %s;
            """

            cursor.execute(query, (instagram_url, club_id))
            count = cursor.fetchone()[0]

            return count > 0

        except Exception as e:
            logger.error(f"❌ 중복 확인 오류: {e}")
            return False

        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def bulk_insert_performances(self, posts_data: List[Dict]) -> Dict[str, int]:
        """
        여러 공연 정보 일괄 삽입
        
        Args:
            posts_data: 게시물 데이터 리스트
            
        Returns:
            삽입 결과 통계 {'success': 성공 수, 'skipped': 중복 수, 'failed': 실패 수}
        """
        results = {'success': 0, 'skipped': 0, 'failed': 0}

        for post in posts_data:
            try:
                # 중복 확인
                if self.check_duplicate_post(post.get('post_url'), post.get('club_id')):
                    logger.info(f"⚠️ 중복 게시물 건너뛰기: {post.get('post_url')}")
                    results['skipped'] += 1
                    continue

                # 삽입
                inserted_id = self.insert_performance(post)
                if inserted_id:
                    results['success'] += 1
                else:
                    results['failed'] += 1

            except Exception as e:
                logger.error(f"❌ 일괄 삽입 중 오류: {e}")
                results['failed'] += 1

        return results