"""
이미지 다운로드 및 업로드 
"""
import requests
import uuid, os
from io import BytesIO
from PIL import Image
from typing import Optional, Dict, List
from datetime import datetime
from utils.logger import setup_logger
from storage.r2_storage import R2StorageAdapter

logger = setup_logger('image_manager')

class ImageManager:
    def __init__(self, storage_adapter: R2StorageAdapter):
        """
        이미지 관리자 초기화
        
        Args:
            storage_adapter: R2StorageAdapter 인스턴스
        """
        self.storage = storage_adapter
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_and_upload_image(
        self, 
        image_url: str, 
        perform_id: int,
        is_main: bool = True
    ) -> Optional[Dict]:
        """
        이미지 다운로드 후 R2에 업로드
        
        Args:
            image_url: 이미지 URL
            perform_id: 공연 ID
            is_main: 메인 이미지 여부
            
        Returns:
            업로드 결과 딕셔너리 또는 None
            {
                'file_path': str,
                'file_size': int,
                'original_name': str
            }
        """
        if not image_url:
            logger.warning("⚠️ 이미지 URL이 없습니다")
            return None
        
        try:
            # 1. 이미지 다운로드
            logger.info(f"📥 이미지 다운로드 시작: {image_url[:100]}...")
            response = self.session.get(image_url, timeout=30)
            response.raise_for_status()
            
            image_data = response.content
            file_size = len(image_data)
            
            logger.info(f"✅ 다운로드 완료: {file_size / 1024:.2f} KB")
            
            # 2. 이미지 검증 (PIL로 열어서 유효성 확인)
            try:
                img = Image.open(BytesIO(image_data))
                img.verify()
                logger.info(f"✅ 이미지 검증 완료: {img.format}, {img.size}")
            except Exception as e:
                logger.error(f"❌ 이미지 검증 실패: {e}")
                return None
            
            # 3. 파일명 생성
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            extension = self._get_extension(image_url, img.format)
            uuid_str = str(uuid.uuid4())
            file_name = f"{uuid_str}{extension}"

            # R2 경로: performance/{perform_id}/{filename}
            file_path = f"performance/{perform_id}/{file_name}"
            
            # 4. R2 업로드
            logger.info(f"📤 R2 업로드 시작: {file_path}")
            uploaded_path = self.storage.upload(image_data, file_path)
            
            original_name = os.path.basename(image_url.split("?")[0])  
            if not original_name:
                original_name = "unknown"
            
            if uploaded_path:
                return {
                    'file_path': uploaded_path,
                    'file_size': file_size,
                    'original_name': original_name,
                    'is_main': is_main,
                    'perform_id': perform_id
                }
            else:
                logger.error("❌ R2 업로드 실패")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 이미지 다운로드 실패: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ 이미지 처리 오류: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def download_and_upload_multiple_images(
        self,
        image_urls: List[str],
        perform_id: int
    ) -> List[Dict]:
        """
        여러 이미지 다운로드 및 업로드
        
        Args:
            image_urls: 이미지 URL 리스트
            perform_id: 공연 ID
            
        Returns:
            업로드 결과 리스트
        """
        results = []
        
        for i, url in enumerate(image_urls):
            is_main = (i == 0)  # 첫 번째 이미지를 메인으로
            
            logger.info(f"\n[{i+1}/{len(image_urls)}] 이미지 처리 중...")
            result = self.download_and_upload_image(url, perform_id, is_main)
            
            if result:
                results.append(result)
                logger.info(f"✅ 이미지 {i+1} 처리 완료")
            else:
                logger.warning(f"⚠️ 이미지 {i+1} 처리 실패")
        
        logger.info(f"\n총 {len(results)}/{len(image_urls)}개 이미지 업로드 완료")
        return results
    
    def _get_extension(self, url: str, image_format: Optional[str]) -> str:
        """
        이미지 확장자 결정
        
        Args:
            url: 이미지 URL
            image_format: PIL 이미지 포맷
            
        Returns:
            확장자 (.jpg, .png 등)
        """
        # PIL 포맷 기반
        if image_format:
            format_map = {
                'JPEG': '.jpg',
                'PNG': '.png',
                'WEBP': '.webp',
                'GIF': '.gif'
            }
            if image_format.upper() in format_map:
                return format_map[image_format.upper()]
        
        # URL 기반 (백업)
        if '.jpg' in url.lower() or '.jpeg' in url.lower():
            return '.jpg'
        elif '.png' in url.lower():
            return '.png'
        elif '.webp' in url.lower():
            return '.webp'
        
        # 기본값
        return '.jpg'