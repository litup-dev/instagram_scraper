"""
PostgreSQL 데이터베이스 관리자
"""
import psycopg2
from typing import List, Dict, Optional
import json
from psycopg2 import pool
from utils.logger import setup_logger
from config.settings import DB_CONFIG

logger = setup_logger('db_manager')


class DatabaseManager:
    def __init__(self):
        """데이터베이스 연결 풀 초기화"""
        try:
            # 연결 풀 설정 개선
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=DB_CONFIG['host'],
                port=int(DB_CONFIG['port']),  # 포트를 정수로 변환
                database=DB_CONFIG['database'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                connect_timeout=10,  # 연결 타임아웃 10초
                keepalives=1,  # TCP keepalive 활성화
                keepalives_idle=30,  # 30초마다 keepalive 패킷 전송
                keepalives_interval=10,  # keepalive 재시도 간격
                keepalives_count=5  # keepalive 재시도 횟수
            )
            logger.info("✅ 데이터베이스 연결 풀 초기화 완료")
            logger.info(f"   연결 정보: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
            
            # 연결 테스트
            self._test_connection()
            
        except psycopg2.OperationalError as e:
            logger.error(f"❌ 데이터베이스 연결 실패 (연결 불가)")
            logger.error(f"   Host: {DB_CONFIG['host']}")
            logger.error(f"   Port: {DB_CONFIG['port']}")
            logger.error(f"   Database: {DB_CONFIG['database']}")
            logger.error(f"   User: {DB_CONFIG['user']}")
            logger.error(f"   Error: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ 데이터베이스 연결 실패: {e}")
            raise

    def _test_connection(self):
        """연결 테스트"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            cursor.fetchone()
            cursor.close()
            logger.info("✅ 데이터베이스 연결 테스트 성공")
        except Exception as e:
            logger.error(f"❌ 데이터베이스 연결 테스트 실패: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)

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

    def get_clubs_with_instagram(self) -> List[Dict]:
        """
        Instagram SNS 링크가 있는 클럽 정보 조회
        
        Returns:
            클럽 정보 리스트 [{'club_id': int, 'name': str, 'instagram_url': str, 'last_post_url': str or None}, ...]
        """
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    c.id,
                    c.name,
                    c.sns_links,
                    (
                        SELECT 
                            CASE 
                                WHEN jsonb_typeof(p.sns_links) = 'array' THEN p.sns_links->0->>'instagram'
                                ELSE p.sns_links->>'instagram'
                            END
                        FROM perform_tmp p
                        WHERE p.club_id = c.id
                        AND (
                            (jsonb_typeof(p.sns_links) = 'array' AND p.sns_links->0->>'instagram' IS NOT NULL)
                            OR (jsonb_typeof(p.sns_links) = 'object' AND p.sns_links->>'instagram' IS NOT NULL)
                        )
                        ORDER BY p.created_at DESC
                        LIMIT 1
                    ) as last_post_url
                FROM club_tb c
                WHERE c.sns_links IS NOT NULL
                AND c.sns_links::text LIKE '%instagram%';
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            clubs = []
            for row in rows:
                club_id, name, sns_links, last_post_url = row
                
                # sns_links에서 Instagram URL 추출
                if sns_links:
                    for link in sns_links:
                        if 'instagram' in link:
                            instagram_url = link.get('instagram', '')
                            if instagram_url:
                                clubs.append({
                                    'club_id': club_id,
                                    'name': name,
                                    'instagram_url': instagram_url,
                                    'last_post_url': last_post_url
                                })
                                break
            
            logger.info(f"✅ Instagram 연동 클럽 {len(clubs)}개 조회 완료")
            
            # 각 클럽의 마지막 게시물 로깅
            for club in clubs:
                if club['last_post_url']:
                    logger.info(f"   [{club['name']}] 마지막 저장: {club['last_post_url']}")
                else:
                    logger.info(f"   [{club['name']}] 신규 클럽 (저장된 게시물 없음)")
            
            return clubs
            
        except psycopg2.OperationalError as e:
            logger.error(f"❌ 데이터베이스 연결 오류: {e}")
            logger.error(f"   DB 설정 확인: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
            return []
        except Exception as e:
            logger.error(f"❌ 클럽 정보 조회 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.return_connection(conn)

    def get_club_by_name(self, name: str) -> Optional[Dict]:
        """
        클럽명으로 클럽 정보 조회
        
        Args:
            name: 클럽명
            
        Returns:
            클럽 정보 또는 None
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    c.id,
                    c.name,
                    c.sns_links,
                    (
                        SELECT 
                            CASE 
                                WHEN jsonb_typeof(p.sns_links) = 'array' THEN p.sns_links->0->>'instagram'
                                ELSE p.sns_links->>'instagram'
                            END
                        FROM perform_tmp p
                        WHERE p.club_id = c.id
                        AND (
                            (jsonb_typeof(p.sns_links) = 'array' AND p.sns_links->0->>'instagram' IS NOT NULL)
                            OR (jsonb_typeof(p.sns_links) = 'object' AND p.sns_links->>'instagram' IS NOT NULL)
                        )
                        ORDER BY p.created_at DESC
                        LIMIT 1
                    ) as last_post_url
                FROM club_tb c
                WHERE c.name = %s
                AND c.sns_links IS NOT NULL;
            """
            
            cursor.execute(query, (name,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            club_id, name, sns_links, last_post_url = row
            
            # Instagram URL 추출
            instagram_url = ''
            if sns_links:
                for link in sns_links:
                    if 'instagram' in link:
                        instagram_url = link.get('instagram', '')
                        break
            
            if not instagram_url:
                return None
            
            return {
                'club_id': club_id,
                'name': name,
                'instagram_url': instagram_url,
                'last_post_url': last_post_url
            }
            
        except Exception as e:
            logger.error(f"❌ 클럽 조회 오류: {e}")
            return None
            
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def get_club_by_instagram_url(self, instagram_url: str) -> Optional[Dict]:
        """
        Instagram URL로 클럽 정보 조회
        
        Args:
            instagram_url: Instagram URL
            
        Returns:
            클럽 정보 또는 None
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    c.id,
                    c.name,
                    c.sns_links,
                    (
                        SELECT 
                            CASE 
                                WHEN jsonb_typeof(p.sns_links) = 'array' THEN p.sns_links->0->>'instagram'
                                ELSE p.sns_links->>'instagram'
                            END
                        FROM perform_tmp p
                        WHERE p.club_id = c.id
                        AND (
                            (jsonb_typeof(p.sns_links) = 'array' AND p.sns_links->0->>'instagram' IS NOT NULL)
                            OR (jsonb_typeof(p.sns_links) = 'object' AND p.sns_links->>'instagram' IS NOT NULL)
                        )
                        ORDER BY p.created_at DESC
                        LIMIT 1
                    ) as last_post_url
                FROM club_tb c
                WHERE c.sns_links::text LIKE %s;
            """
            
            cursor.execute(query, (f'%{instagram_url}%',))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            club_id, name, sns_links, last_post_url = row
            
            return {
                'club_id': club_id,
                'name': name,
                'instagram_url': instagram_url,
                'last_post_url': last_post_url
            }
            
        except Exception as e:
            logger.error(f"❌ 클럽 조회 오류: {e}")
            return None
            
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

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
            
            # sns_links 데이터 준비
            post_url = post_data.get('post_url', '')
            sns_links = {
                'instagram': post_url
            }
            sns_links_json = json.dumps(sns_links, ensure_ascii=False)

            # INSERT 쿼리
            insert_query = """
                INSERT INTO perform_tmp (
                    club_id, 
                    user_id, 
                    sns_links, 
                    is_cancelled, 
                    description
                ) VALUES (
                    %s, %s, %s::jsonb, %s, %s
                )
                RETURNING id;
            """

            cursor.execute(insert_query, (
                post_data.get('club_id'),
                1,  # user_id는 임시로 1로 고정
                sns_links_json,
                False,
                post_data.get('caption', '')
            ))

            # 삽입된 ID 가져오기
            inserted_id = cursor.fetchone()[0]
            conn.commit()

            logger.info(f"✅ 공연 정보 저장 완료 (ID: {inserted_id})")
            
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
            logger.error(f"   문제 데이터 Instagram URL : {post_url}")
            return None

        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def check_duplicate_post(self, instagram_url: str, club_id: int) -> bool:
        """
        중복 게시물 확인
        
        Args:
            instagram_url: Instagram 게시물 URL
            club_id: 클럽 ID
            
        Returns:
            중복이면 True, 아니면 False
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # sns_links가 배열 또는 객체 형식 모두 지원
            query = """
                SELECT COUNT(*) 
                FROM perform_tmp
                WHERE club_id = %s
                AND (
                    (jsonb_typeof(sns_links) = 'array' AND sns_links->0->>'instagram' = %s)
                    OR (jsonb_typeof(sns_links) = 'object' AND sns_links->>'instagram' = %s)
                );
            """

            cursor.execute(query, (club_id, instagram_url, instagram_url))
            count = cursor.fetchone()[0]

            if count > 0:
                logger.info(f"   🔍 중복 확인: 이미 존재함 ({instagram_url})")
            
            return count > 0

        except Exception as e:
            logger.error(f"❌ 중복 확인 오류: {e}")
            return False

        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)

    def insert_performance_image(self, image_data: Dict) -> Optional[int]:
        """
        공연 이미지 정보 삽입
        
        Args:
            image_data: 이미지 데이터
            
        Returns:
            삽입된 이미지 ID 또는 None
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            insert_query = """
                INSERT INTO perform_img_tmp (
                    perform_id,
                    file_path,
                    file_size,
                    original_name,
                    is_main,
                    created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, NOW()
                )
                RETURNING id;
            """

            cursor.execute(insert_query, (
                image_data['perform_id'],
                image_data['file_path'],
                image_data['file_size'],
                image_data['original_name'],
                image_data.get('is_main', True)
            ))

            image_id = cursor.fetchone()[0]
            conn.commit()

            logger.info(f"✅ 이미지 정보 저장 완료 (ID: {image_id})")
            
            return image_id

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ 이미지 정보 저장 오류: {e}")
            return None

        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)