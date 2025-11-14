"""
아티스트 추출기 테스트
"""
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.parser.artist_extractor import ArtistExtractor

# ========== 테스트 코드 ==========

def test_artist_extractor():
    """아티스트 추출기 테스트"""
    extractor = ArtistExtractor()
    
    test_cases = [
        {
            'text': '''혁오 @hyukoh_official
잔나비 @thejannabiofficial
새소년 @se_so_neon''',
            'expected': [
                {'name': '혁오', 'insta': '@hyukoh_official'},
                {'name': '잔나비', 'insta': '@thejannabiofficial'},
                {'name': '새소년', 'insta': '@se_so_neon'}
            ]
        },
        {
            'text': '''🌀 SMOKING GOOSE @smokinggoose_official
🌀 The Poles @thepoles_official
🌀 Dabda @dabdaofficial''',
            'expected': [
                {'name': 'SMOKING GOOSE', 'insta': '@smokinggoose_official'},
                {'name': 'The Poles', 'insta': '@thepoles_official'},
                {'name': 'Dabda', 'insta': '@dabdaofficial'}
            ]
        },
        {
            'text': '''> Sindosi / 신도시 @band_sindosi
> Bandits / 밴디츠 @bandits_busan
> Daisy Gun / 데이지 건 @daisygunband''',
            'expected': [
                {'name': '신도시', 'insta': '@band_sindosi'},
                {'name': '밴디츠', 'insta': '@bandits_busan'},
                {'name': '데이지 건', 'insta': '@daisygunband'}
            ]
        },
        {
            'text': '''7:00pm #놀플라워 @nollflower_official
7:45pm #IRISMONDO @irismondogram
8:30pm #루아멜 @luamel_official''',
            'expected': [
                {'name': '놀플라워', 'insta': '@nollflower_official'},
                {'name': 'IRISMONDO', 'insta': '@irismondogram'},
                {'name': '루아멜', 'insta': '@luamel_official'}
            ]
        },
        {
            'text': '''실험하고 있는 기나이직 @guinneissik
해피 이조코 @imhappyizoko
받아 하드코어, 노이즈 사운드의 퍼포먼스를 선보이는 Balancequeen69 @balancequeen69
선보이는 게이 전용 특급모텔인 K특급모텔 @k_supermotel''',
            'expected': [
                {'name': '기나이직', 'insta': '@guinneissik'},
                {'name': '해피 이조코', 'insta': '@imhappyizoko'},
                {'name': 'Balancequeen69', 'insta': '@balancequeen69'},
                {'name': 'K특급모텔', 'insta': '@k_supermotel'}
            ]
        },
        {
            'text': '''K특급모텔 @k_supermotel
치치카포 @chichikafo
해피 이조코 @imhappyizoko
Saiki Toshio @saiki.toshio''',
            'expected': [
                {'name': 'K특급모텔', 'insta': '@k_supermotel'},
                {'name': '치치카포', 'insta': '@chichikafo'},
                {'name': '해피 이조코', 'insta': '@imhappyizoko'},
                {'name': 'Saiki Toshio', 'insta': '@saiki.toshio'}
            ]
        },
        {
            'text': '''> ADOY / 아도이 @adoyvvv
> The Black Skirts / 검정치마 @theblaackskirts
> Say Sue Me / 세이수미 @saysuemelive''',
            'expected': [
                {'name': '아도이', 'insta': '@adoyvvv'},
                {'name': '검정치마', 'insta': '@theblaackskirts'},
                {'name': '세이수미', 'insta': '@saysuemelive'}
            ]
        },
        {
            'text': '''혁오 @hyukoh_official
HYUKOH @hyukoh_official
혁오 @hyukoh_official''',
            'expected': [
                {'name': '혁오', 'insta': '@hyukoh_official'}
            ]
        },
        {
            'text': '''7:00pm #놀플라워 @nollflower_official
7:45pm #IRISMONDO (From Japan) @irismondogram
8:30pm #루아멜 @luamel_official''',
            'expected': [
                {'name': '놀플라워', 'insta': '@nollflower_official'},
                {'name': 'IRISMONDO', 'insta': '@irismondogram'},
                {'name': '루아멜', 'insta': '@luamel_official'}
            ]
        },
        {
            'text': '''Line up:
빈지노 @binjino_official
크러쉬 @crush9244
딘 @deantrbl

티켓: 30,000원''',
            'expected': [
                {'name': '빈지노', 'insta': '@binjino_official'},
                {'name': '크러쉬', 'insta': '@crush9244'},
                {'name': '딘', 'insta': '@deantrbl'}
            ]
        },
        {
            'text': '',
            'expected': []
        },
        {
            'text': '''혁오
잔나비
새소년''',
            'expected': []
        },
    ]
    
    print("=" * 70)
    print("아티스트 추출기 테스트")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for i, case in enumerate(test_cases, 1):
        result = extractor.extract(case['text'])
        expected = case['expected']
        
        # 핸들 기준으로 비교 (이름은 다를 수 있음)
        result_handles = {r['insta'].lower() for r in result}
        expected_handles = {e['insta'].lower() for e in expected}
        
        # 정확히 일치하는지 확인
        is_success = result_handles == expected_handles
        
        # 이름도 체크 (선택적)
        name_match = True
        if is_success and expected:
            result_dict = {r['insta'].lower(): r['name'] for r in result}
            for exp in expected:
                handle = exp['insta'].lower()
                if handle in result_dict:
                    # 이름이 정확히 일치하거나, 포함관계이면 OK
                    result_name = result_dict[handle].lower()
                    expected_name = exp['name'].lower()
                    if result_name != expected_name and expected_name not in result_name:
                        name_match = False
                        break
        
        status = "✅ 성공" if is_success and name_match else "❌ 실패"
        
        print(f"\n테스트 {i}: {status}")
        print(f"  입력: {case['text']}...")
        print(f"  예상: {len(expected)}명")
        
        if expected:
            for e in expected[:3]:
                print(f"    - {e['name']} ({e['insta']})")
            if len(expected) > 3:
                print(f"    ... 외 {len(expected)-3}명")
        
        print(f"  결과: {len(result)}명")
        if result:
            for r in result[:3]:
                print(f"    - {r['name']} ({r['insta']})")
            if len(result) > 3:
                print(f"    ... 외 {len(result)-3}명")
        
        if not is_success:
            missing = expected_handles - result_handles
            extra = result_handles - expected_handles
            if missing:
                print(f"  ⚠️ 누락: {missing}")
            if extra:
                print(f"  ⚠️ 추가: {extra}")
            failed += 1
        elif not name_match:
            print(f"  ⚠️ 핸들은 일치하나 이름이 다름")
            failed += 1
        else:
            passed += 1
    
    print("\n" + "=" * 70)
    print(f"테스트 결과: ✅ {passed}개 성공 / ❌ {failed}개 실패 (총 {len(test_cases)}개)")
    print("=" * 70)


if __name__ == "__main__":
    test_artist_extractor()