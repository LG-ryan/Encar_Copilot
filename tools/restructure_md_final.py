"""
MD 파일 재구조화 스크립트 (최종 버전)
- "질문:", "답변:", "[요약]", "[상세]" 레이블 제거
- 내용은 보존하고 형식만 변경
- LLM이 읽기 좋은 깔끔한 마크다운 구조로 변환
"""
import re
from pathlib import Path


def restructure_md_content(content: str) -> str:
    """
    MD 내용 재구조화
    - 레이블 제거, 내용 보존
    - 깔끔한 마크다운 구조로 변환
    """
    
    # 1. **질문:** 레이블 제거 (질문 내용은 보존)
    # 패턴: **질문:** 질문내용\n\n → 질문내용\n\n
    content = re.sub(r'\*\*질문:\*\*\s*([^\n]+)', r'\1', content)
    
    # 2. **답변:** 레이블 제거 (답변 내용은 보존)
    # 패턴: **답변:**\n\n → (빈 줄)
    content = re.sub(r'\*\*답변:\*\*\s*\n', '', content)
    
    # 3. [요약] 레이블 제거 (내용은 보존)
    # 패턴: [요약]\n내용 → 내용
    content = re.sub(r'\[요약\]\s*\n', '', content)
    
    # 4. [상세] 레이블 제거 (내용은 보존)
    # 패턴: [상세]\n내용 → 내용
    content = re.sub(r'\[상세\]\s*\n', '', content)
    
    # 5. 연속된 빈 줄 정리 (3개 이상 → 2개)
    content = re.sub(r'\n{4,}', '\n\n\n', content)
    
    # 6. 섹션 제목 후 빈 줄 정리
    # 패턴: ## 제목\n\n\n내용 → ## 제목\n\n내용
    content = re.sub(r'(#{2,4}\s+[^\n]+)\n{3,}', r'\1\n\n', content)
    
    return content


def restructure_md_file(md_file_path: Path):
    """MD 파일 재구조화 실행"""
    print(f"\n{'='*60}")
    print(f"📄 처리 중: {md_file_path.name}")
    print(f"{'='*60}")
    
    # 원본 읽기
    with open(md_file_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    original_length = len(original_content)
    print(f"📊 원본 길이: {original_length:,}자")
    
    # 재구조화
    restructured_content = restructure_md_content(original_content)
    restructured_length = len(restructured_content)
    
    print(f"📊 재구조화 후 길이: {restructured_length:,}자")
    
    # 길이 변화 확인
    length_diff = original_length - restructured_length
    removed_chars = length_diff
    
    print(f"🔍 제거된 문자: {removed_chars:,}자 (레이블만 제거됨)")
    
    # 백업 생성
    backup_path = md_file_path.with_suffix('.md.backup2')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(original_content)
    print(f"💾 백업 생성: {backup_path.name}")
    
    # 재구조화된 내용 저장
    with open(md_file_path, 'w', encoding='utf-8') as f:
        f.write(restructured_content)
    print(f"✅ 재구조화 완료!")
    
    # 미리보기 (앞부분 200자)
    print(f"\n📝 미리보기 (앞 200자):")
    print("-" * 60)
    print(restructured_content[:200])
    print("-" * 60)


def main():
    """메인 실행"""
    print("="*60)
    print("🔧 MD 파일 재구조화 스크립트 (최종 버전)")
    print("="*60)
    
    docs_dir = Path("docs")
    md_files = [
        docs_dir / "엔카생활가이드.md",
        docs_dir / "비즈니스.md"
    ]
    
    for md_file in md_files:
        if md_file.exists():
            restructure_md_file(md_file)
        else:
            print(f"⚠️  파일 없음: {md_file}")
    
    print("\n" + "="*60)
    print("🎉 모든 파일 재구조화 완료!")
    print("="*60)
    print("\n📌 다음 단계:")
    print("1. docs/*.md 파일 내용 확인")
    print("2. py tools/generate_metadata.py (메타데이터 재생성)")
    print("3. 서버 재시작 및 테스트")


if __name__ == "__main__":
    main()

