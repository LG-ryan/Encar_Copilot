"""
엔카생활가이드.md 완전 재구조화
Phase 2 & 3: FAQ 형식 전체 적용 + 청크 최적화
"""
import re

def apply_faq_format_complete(content):
    """
    전체 섹션에 FAQ 형식 적용
    """
    
    # 섹션별 질문 매핑
    faq_mappings = [
        # 업무 환경 세팅
        (r'(### 와이파이 연결 방법\n)', r'\1\n**질문:** 와이파이 비밀번호가 뭐예요?\n\n**답변:**\n'),
        (r'(### 인터넷 에이전트 설치 방법\n)', r'\1\n**질문:** 네트워크 에이전트는 어떻게 설치하나요?\n\n**답변:**\n'),
        (r'(### 그룹웨어 로그인 방법\n)', r'\1\n**질문:** 그룹웨어는 어떻게 로그인하나요?\n\n**답변:**\n'),
        (r'(### VDI 접속 방법\n)', r'\1\n**질문:** VDI는 어떻게 접속하나요?\n\n**답변:**\n'),
        (r'(### 프린터 설정 방법\n)', r'\1\n**질문:** 프린터는 어떻게 설정하나요?\n\n**답변:**\n'),
        
        # 업무 Tool
        (r'(### 그룹웨어 사용 방법\n)', r'\1\n**질문:** 그룹웨어는 어떻게 사용하나요?\n\n**답변:**\n'),
        (r'(### VDI 사용 방법\n)', r'\1\n**질문:** VDI는 어떻게 사용하나요?\n\n**답변:**\n'),
        (r'(### FTC 프로그램 사용 방법\n)', r'\1\n**질문:** FTC 프로그램이 뭔가요?\n\n**답변:**\n'),
        
        # 복리후생
        (r'(### 웰컴 키트 안내\n)', r'\1\n**질문:** 웰컴 키트에는 뭐가 들어있나요?\n\n**답변:**\n'),
        (r'(### 자기계발비 신청 방법\n)', r'\1\n**질문:** 자기계발비는 어떻게 사용하나요?\n\n**답변:**\n'),
        (r'(### 경조사 지원 안내\n)', r'\1\n**질문:** 경조사 지원은 어떻게 받나요?\n\n**답변:**\n'),
        (r'(### 리조트 신청 및 이용\n)', r'\1\n**질문:** 리조트는 어떻게 신청하나요?\n\n**답변:**\n'),
        
        # 근태 및 휴가 (이미 적용됨, 유지)
        (r'(### 근태 확인 방법\n)', r'\1\n**질문:** 근태는 어디서 확인하나요?\n\n**답변:**\n'),
        (r'(### 연장근무 신청 방법\n)', r'\1\n**질문:** 연장근무는 어떻게 신청하나요?\n\n**답변:**\n'),
        
        # 급여 및 경비
        (r'(### 급여/경비 계좌 변경 방법\n)', r'\1\n**질문:** 급여 계좌는 어떻게 변경하나요?\n\n**답변:**\n'),
        (r'(### 급여명세서 확인 방법\n)', r'\1\n**질문:** 급여명세서는 어디서 확인하나요?\n\n**답변:**\n'),
        (r'(### 경비 신청 방법\n)', r'\1\n**질문:** 경비는 어떻게 신청하나요?\n\n**답변:**\n'),
        
        # 사무실 이용
        (r'(### 명함 신청 방법\n)', r'\1\n**질문:** 명함은 어떻게 신청하나요?\n\n**답변:**\n'),
        (r'(### 퀵 서비스 신청 방법\n)', r'\1\n**질문:** 퀵 서비스는 어떻게 이용하나요?\n\n**답변:**\n'),
        (r'(### 주차권 신청 방법\n)', r'\1\n**질문:** 주차권은 어떻게 신청하나요?\n\n**답변:**\n'),
        (r'(### AIA타워 외부인 방문 관리\n)', r'\1\n**질문:** 외부인 방문은 어떻게 관리하나요?\n\n**답변:**\n'),
        
        # 인사 서비스
        (r'(### 재직증명서 신청 방법\n)', r'\1\n**질문:** 재직증명서는 어떻게 발급받나요?\n\n**답변:**\n'),
        (r'(### 교육 신청 방법\n)', r'\1\n**질문:** 교육은 어떻게 신청하나요?\n\n**답변:**\n'),
    ]
    
    for pattern, replacement in faq_mappings:
        # 이미 "**질문:**"이 있는 경우 스킵
        if re.search(pattern + r'[^\n]*\n\*\*질문:\*\*', content):
            continue
        content = re.sub(pattern, replacement, content)
    
    return content

def add_helpful_notes(content):
    """
    주요 섹션에 참고사항 추가
    """
    
    # 연차/휴가 섹션에 참고사항 추가
    if '※ 연차와 보상(대체)휴가 중 연차 우선 소진 권장' in content:
        content = content.replace(
            '조직행사 특별휴가, 경조휴가 등은 신청일수가 0일로 나옵니다!',
            '조직행사 특별휴가, 경조휴가 등은 신청일수가 0일로 나옵니다!\n\n**참고사항:**\n• 반차는 연차 0.5개 차감\n• 하계휴가는 연차 차감 없음 (6/1~10/31)\n• 결재라인: 팀원→팀장, 팀장→차상위 직책자'
        )
    
    return content

def optimize_chunk_size(content):
    """
    청크 크기 최적화 - 너무 긴 섹션 분리 표시
    """
    
    lines = content.split('\n')
    result = []
    current_h3 = None
    current_h3_line_count = 0
    
    for line in lines:
        if line.startswith('### '):
            if current_h3 and current_h3_line_count > 150:
                # 너무 긴 섹션 경고 (검토 필요)
                print(f"   ⚠️  긴 섹션 발견: {current_h3} ({current_h3_line_count}줄)")
            current_h3 = line
            current_h3_line_count = 0
        else:
            current_h3_line_count += 1
        
        result.append(line)
    
    return '\n'.join(result)

def main():
    print("=" * 60)
    print("📄 엔카생활가이드.md 완전 재구조화 (Phase 2 & 3)")
    print("=" * 60)
    
    input_file = 'docs/엔카생활가이드.md'
    backup_file = 'archives/엔카생활가이드_backup_final.md'
    
    # 원본 읽기
    print(f"\n1️⃣  원본 파일 읽기: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 현재 FAQ 형식 개수
    current_faq_count = content.count('**질문:**')
    print(f"   현재 FAQ 형식: {current_faq_count}개")
    
    # 백업
    print(f"\n2️⃣  최종 백업 생성: {backup_file}")
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Phase 2: FAQ 형식 전체 적용
    print(f"\n3️⃣  Phase 2: 전체 섹션에 FAQ 형식 적용...")
    content = apply_faq_format_complete(content)
    
    # 참고사항 추가
    print(f"\n4️⃣  주요 섹션에 참고사항 추가...")
    content = add_helpful_notes(content)
    
    # Phase 3: 청크 크기 분석
    print(f"\n5️⃣  Phase 3: 청크 크기 최적화 분석...")
    content = optimize_chunk_size(content)
    
    final_faq_count = content.count('**질문:**')
    print(f"\n   FAQ 형식: {current_faq_count}개 → {final_faq_count}개 (+{final_faq_count - current_faq_count})")
    
    # 저장
    print(f"\n6️⃣  저장: {input_file}")
    with open(input_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n" + "=" * 60)
    print("✅ 완전 재구조화 완료!")
    print("=" * 60)
    print(f"\n📊 Phase 2 & 3 완료:")
    print(f"   - 전체 섹션에 FAQ 형식 적용 ({final_faq_count}개)")
    print(f"   - 참고사항 추가")
    print(f"   - 청크 크기 분석 완료")
    print(f"\n⚠️  시맨틱 인덱스 재생성 필요!")
    print(f"   → 서버 재시작 시 자동 재생성됩니다!")

if __name__ == "__main__":
    main()

