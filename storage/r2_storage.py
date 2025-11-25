"""
R2 스토리지 어댑터
"""
import boto3
from botocore.exceptions import ClientError
import os
from typing import Optional
from utils.logger import setup_logger

logger = setup_logger('r2_storage')

class R2StorageAdapter:
    def __init__(self, config: dict):
        """
        R2 클라이언트 초기화
        
        Args:
            config: {
                'bucket_name': str,
                'access_key_id': str,
                'secret_access_key': str,
                'endpoint_url': str,
                'region': str (optional, default='auto')
            }
        """
        self.bucket_name = config['bucket_name']
        self.client = boto3.client(
            's3',
            region_name=config.get('region', 'auto'),
            endpoint_url=config['endpoint_url'],
            aws_access_key_id=config['access_key_id'],
            aws_secret_access_key=config['secret_access_key']
        )
        logger.info(f"✅ R2 클라이언트 초기화 완료: {self.bucket_name}")
    
    def upload(self, buffer: bytes, file_path: str) -> Optional[str]:
        """
        R2에 파일 업로드
        
        Args:
            buffer: 파일 바이너리 데이터
            file_path: R2에 저장될 경로 (예: 'performance/123/image.jpg')
            
        Returns:
            업로드된 파일 경로 또는 None
        """
        try:
            content_type = self._get_content_type(file_path)
            
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=file_path,
                Body=buffer,
                ContentType=content_type
            )
            
            logger.info(f"✅ R2 업로드 성공: {file_path}")
            return file_path
            
        except ClientError as e:
            logger.error(f"❌ R2 업로드 실패: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ R2 업로드 오류: {e}")
            return None
    
    def delete(self, file_path: str) -> bool:
        """
        R2에서 파일 삭제
        
        Args:
            file_path: 삭제할 파일 경로
            
        Returns:
            성공 여부
        """
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            logger.info(f"✅ R2 삭제 성공: {file_path}")
            return True
            
        except ClientError as e:
            logger.error(f"❌ R2 삭제 실패: {e}")
            return False
    
    def exists(self, file_path: str) -> bool:
        """
        파일 존재 여부 확인
        
        Args:
            file_path: 확인할 파일 경로
            
        Returns:
            존재 여부
        """
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"❌ R2 존재 확인 오류: {e}")
            return False
    
    def _get_content_type(self, file_path: str) -> str:
        """
        파일 확장자로 Content-Type 결정
        
        Args:
            file_path: 파일 경로
            
        Returns:
            Content-Type
        """
        ext = os.path.splitext(file_path)[1].lower()
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }
        return content_types.get(ext, 'application/octet-stream')