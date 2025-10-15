"""
엔카생활가이드.md FAQ 스타일 재구조화
- H3 제목에 키워드 명시
- 질문/답변 형식으로 변환
- 중복 제거 및 청크 크기 최적화
"""
import re

def restructure_to_faq_style(content):
    """
    FAQ 스타일로 재구조화
    """
    
    # H3 제목 개선 (키워드 명시)
    title_improvements = [
        # 근태 및 휴가
        (r'### 휴가 신청/취소', '### 연차/휴가 신청 방법'),
        (r'### 휴가 신청 방법', ''),  # 중복 제거
        (r'### 휴가 취소 방법', '### 연차/휴가 취소 방법'),
        (r'### 근태 확인', '### 근태 확인 방법'),
        (r'### 연장근무 신청', '### 연장근무 신청 방법'),
        (r'### 근무시간 조정', '### 근무시간 조정 방법'),
        (r'### 유연근무 신청', '### 유연근무 신청 방법'),
        
        # 복리후생
        (r'### 웰컴 키트$', '### 웰컴 키트 안내'),
        (r'### 자기계발비$', '### 자기계발비 신청 방법'),
        (r'### 경조사 관련 안내', '### 경조사 지원 안내'),
        (r'### 경조사 세부 안내', ''),  # 중복 제거, 위에 합치기
        (r'### 엔카상품권', '### 엔카상품권(BBL) 정산 방법'),
        (r'### 리조트', '### 리조트 신청 및 이용'),
        
        # 급여 및 경비
        (r'### 급여/경비계좌 변경', '### 급여/경비 계좌 변경 방법'),
        (r'### 급여명세서 확인', '### 급여명세서 확인 방법'),
        (r'### 경비 신청', '### 경비 신청 방법'),
        
        # 사무실 이용
        (r'### 명함 신청', '### 명함 신청 방법'),
        (r'### 퀵 신청', '### 퀵 서비스 신청 방법'),
        (r'### 주차권 신청', '### 주차권 신청 방법'),
        (r'### 사무용품 신청', '### 사무용품 신청 방법'),
        (r'### 유니폼 신청', '### 유니폼 신청 방법'),
        (r'### AIA타워', '### AIA타워 외부인 방문 관리'),
        
        # 인사 서비스
        (r'### 재직증명서 신청', '### 재직증명서 신청 방법'),
        (r'### 교육 신청', '### 교육 신청 방법'),
        
        # 업무 환경
        (r'### 와이파이 연결', '### 와이파이 연결 방법'),
        (r'### 인터넷 사용\(에이전트 설치\)', '### 인터넷 에이전트 설치 방법'),
        (r'### 문서 보안 로그인', '### 문서 보안 로그인 방법'),
        (r'### 그룹웨어 로그인', '### 그룹웨어 로그인 방법'),
        (r'### JIRA$', '### JIRA 접속 방법'),
        (r'### VDI 접속', '### VDI 접속 방법'),
        (r'### 엘란$', '### 엘란 접속 방법'),
        (r'### 프린터 설정', '### 프린터 설정 방법'),
        
        # 업무 Tool
        (r'### 그룹웨어$', '### 그룹웨어 사용 방법'),
        (r'### VDI$', '### VDI 사용 방법'),
        (r'### FTC 프로그램', '### FTC 프로그램 사용 방법'),
        (r'### JIRA, Confluence', '### JIRA, Confluence 사용 방법'),
        (r'### 슬랙\(Slack\)', '### 슬랙(Slack) 사용 방법'),
        (r'### 포티\(Forty\)', '### PC-OFF 프로그램(Forty) 사용 방법'),
        (r'### MIRO$', '### MIRO 사용 방법'),
    ]
    
    for pattern, replacement in title_improvements:
        if replacement:  # 빈 문자열이 아니면 교체
            content = re.sub(pattern, replacement, content)
        else:  # 빈 문자열이면 제거 (중복 H3)
            content = re.sub(pattern + r'\n', '', content)
    
    return content

def add_faq_format(content):
    """
    특정 섹션에 질문/답변 형식 추가
    """
    
    # 연차/휴가 신청 섹션
    content = re.sub(
        r'(### 연차/휴가 신청 방법\n)(-.*안내\n)',
        r'\1\n**질문:** 연차는 어떻게 신청하나요?\n\n**답변:**\n',
        content
    )
    
    # 근태 확인 섹션
    content = re.sub(
        r'(### 근태 확인 방법\n)(-.*안내\n)',
        r'\1\n**질문:** 근태는 어디서 확인하나요?\n\n**답변:**\n',
        content
    )
    
    return content

def main():
    print("=" * 60)
    print("📄 엔카생활가이드.md FAQ 스타일 재구조화")
    print("=" * 60)
    
    input_file = 'docs/엔카생활가이드.md'
    backup_file = 'archives/엔카생활가이드_backup3.md'
    
    # 원본 읽기
    print(f"\n1️⃣  원본 파일 읽기: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_h3 = content.count('\n### ')
    print(f"   현재 H3 헤더: {original_h3}개")
    
    # 백업
    print(f"\n2️⃣  백업 생성: {backup_file}")
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 재구조화
    print(f"\n3️⃣  H3 제목 개선 (키워드 명시)...")
    content = restructure_to_faq_style(content)
    
    print(f"\n4️⃣  FAQ 형식 적용...")
    content = add_faq_format(content)
    
    final_h3 = content.count('\n### ')
    print(f"   H3 헤더: {original_h3}개 → {final_h3}개")
    
    # 저장
    print(f"\n5️⃣  저장: {input_file}")
    with open(input_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n" + "=" * 60)
    print("✅ 재구조화 완료!")
    print("=" * 60)
    print(f"\n📊 개선 내용:")
    print(f"   - H3 제목에 키워드 명시 (예: '휴가 신청' → '연차/휴가 신청 방법')")
    print(f"   - 중복 H3 제거")
    print(f"   - 일부 섹션에 질문/답변 형식 적용")
    print(f"\n⚠️  시맨틱 인덱스 재생성 필요!")

if __name__ == "__main__":
    main()

