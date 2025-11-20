"""
Instagram 로그인 테스트 스크립트
"""
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from instagrapi import Client
from config.settings import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD
import os

def test_login():
    print("=" * 60)
    print("Instagram 로그인 테스트")
    print("=" * 60)
    
    # 기존 세션 삭제
    session_file = 'instagram_session.json'
    if os.path.exists(session_file):
        os.remove(session_file)
        print("✅ 기존 세션 삭제")
    
    client = Client()
    
    # 디바이스 설정
    client.set_device({
        "app_version": "269.0.0.18.75",
        "android_version": 28,
        "android_release": "9.0",
        "dpi": "480dpi",
        "resolution": "1080x2340",
        "manufacturer": "Samsung",
        "device": "SM-G973F",
        "model": "Galaxy S10",
        "cpu": "exynos9820",
        "version_code": "314665256"
    })
    
    print(f"\n🔐 로그인 시도: {INSTAGRAM_USERNAME}")
    
    try:
        # 로그인 시도
        result = client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        
        if result:
            print("✅ 로그인 성공!")
            
            # 계정 정보 확인
            account = client.account_info()
            print(f"\n📊 계정 정보:")
            print(f"   사용자명: {account.username}")
            print(f"   이름: {account.full_name}")
            print(f"   비공개: {account.is_private}")
            
            # 세션 저장
            client.dump_settings(session_file)
            print(f"\n💾 세션 저장: {session_file}")
            
        else:
            print("❌ 로그인 실패")
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print("\n💡 해결 방법:")
        print("1. Instagram 앱/웹에서 로그인")
        print("2. '의심스러운 로그인 시도' 알림 확인 및 승인")
        print("3. 2단계 인증이 활성화되어 있다면 비활성화")
        print("4. 비밀번호 확인")
        print("5. 계정이 차단되지 않았는지 확인")
        
        import traceback
        print(f"\n상세 오류:\n{traceback.format_exc()}")

if __name__ == "__main__":
    test_login()