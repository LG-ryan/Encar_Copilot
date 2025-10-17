"""
메타데이터 자동 생성 도구
MD 파일의 H2/H3/H4 구조를 분석하여 세분화된 메타데이터 생성
"""
import re
import json
from pathlib import Path
from typing import List, Dict

# 카테고리별 담당자 정보
CONTACT_INFO = {
    "근태 및 휴가": {
        "team": "P&C팀",
        "name": "이영희",
        "phone": "010-xxxx-xxxx",
        "email": "lee@encar.com"
    },
    "업무 환경 세팅": {
        "team": "IT팀",
        "name": "김철수",
        "phone": "010-yyyy-yyyy",
        "email": "kim@encar.com"
    },
    "사무실 이용": {
        "team": "총무팀",
        "name": "박민수",
        "phone": "010-zzzz-zzzz",
        "email": "park@encar.com"
    },
    "복리후생": {
        "team": "P&C팀",
        "name": "이영희",
        "phone": "010-xxxx-xxxx",
        "email": "lee@encar.com"
    },
    "엔카 소개": {
        "team": "P&C팀",
        "name": "이영희",
        "phone": "010-xxxx-xxxx",
        "email": "lee@encar.com"
    }
}

# 카테고리 매핑 (H2 → 디스플레이 이름)
CATEGORY_MAPPING = {
    "근태 및 휴가": "HR",
    "업무 환경 세팅": "IT",
    "사무실 이용": "총무",
    "복리후생": "복리후생",
    "엔카 소개": "기업 소개",
    "엔카닷컴 소개": "비즈니스"
}


def parse_markdown_structure(file_path: Path) -> List[Dict]:
    """MD 파일의 계층 구조 파싱"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    sections = []
    current_h2 = None
    current_h3 = None
    current_h4 = None
    section_content = []
    section_start_line = 0
    
    for line_num, line in enumerate(lines, 1):
        # H2 감지
        if line.startswith('## '):
            # 이전 섹션 저장
            if current_h2:
                sections.append({
                    "h2": current_h2,
                    "h3": current_h3,
                    "h4": current_h4,
                    "content": ''.join(section_content),
                    "start_line": section_start_line,
                    "end_line": line_num - 1
                })
            
            current_h2 = line.replace('## ', '').strip()
            current_h3 = None
            current_h4 = None
            section_content = []
            section_start_line = line_num
        
        # H3 감지
        elif line.startswith('### '):
            # 이전 H3 섹션 저장
            if current_h3 or current_h4:
                sections.append({
                    "h2": current_h2,
                    "h3": current_h3,
                    "h4": current_h4,
                    "content": ''.join(section_content),
                    "start_line": section_start_line,
                    "end_line": line_num - 1
                })
            
            current_h3 = line.replace('### ', '').strip()
            current_h4 = None
            section_content = []
            section_start_line = line_num
        
        # H4 감지
        elif line.startswith('#### '):
            # 이전 H4 섹션 저장
            if current_h4:
                sections.append({
                    "h2": current_h2,
                    "h3": current_h3,
                    "h4": current_h4,
                    "content": ''.join(section_content),
                    "start_line": section_start_line,
                    "end_line": line_num - 1
                })
            
            current_h4 = line.replace('#### ', '').strip()
            section_content = []
            section_start_line = line_num
        
        else:
            section_content.append(line)
    
    # 마지막 섹션 저장
    if current_h2:
        sections.append({
            "h2": current_h2,
            "h3": current_h3,
            "h4": current_h4,
            "content": ''.join(section_content),
            "start_line": section_start_line,
            "end_line": len(lines)
        })
    
    return sections


def extract_keywords(text: str, title: str) -> List[str]:
    """텍스트에서 핵심 키워드 추출"""
    keywords = []
    
    # 제목에서 키워드
    if title:
        keywords.extend(title.split())
    
    # 본문에서 자주 나오는 단어 (간단한 방식)
    words = re.findall(r'[가-힣a-zA-Z0-9]+', text)
    word_freq = {}
    for word in words:
        if len(word) >= 2:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # 빈도 상위 5개 추가
    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
    keywords.extend([word for word, _ in top_words])
    
    # 중복 제거
    return list(set(keywords))[:10]


def generate_metadata() -> Dict:
    """전체 메타데이터 생성"""
    metadata = {"categories": {}}
    
    # 엔카생활가이드.md 처리
    guide_path = Path("docs/엔카생활가이드.md")
    if guide_path.exists():
        print(f"📄 {guide_path} 분석 중...")
        sections = parse_markdown_structure(guide_path)
        
        for idx, section in enumerate(sections):
            h2 = section.get("h2", "")
            h3 = section.get("h3", "")
            h4 = section.get("h4", "")
            content = section.get("content", "")
            
            # 섹션 제목 결정 (H4 > H3 > H2 우선순위)
            title = h4 or h3 or h2
            if not title:
                continue
            
            # 카테고리 결정
            category_display = CATEGORY_MAPPING.get(h2, "일반")
            
            # 고유 ID 생성
            section_id = f"{category_display}_{idx}"
            
            # 키워드 추출
            keywords = extract_keywords(content, title)
            
            # 담당자 정보 (모두 P&C팀 Ryan으로 통일)
            contact = {
                "team": "P&C팀",
                "name": "Ryan",
                "phone": "연락처 미등록",
                "email": "ryan@encar.com"
            }
            
            # 메타데이터 추가
            metadata["categories"][section_id] = {
                "display_name": category_display,
                "filename": "엔카생활가이드.md",
                "h2_section": h2,
                "h3_section": h3,
                "h4_section": h4,
                "title": title,
                "start_line": section.get("start_line"),
                "end_line": section.get("end_line"),
                "keywords": keywords,
                "contact": contact
            }
        
        print(f"✅ {len(sections)}개 섹션 추출됨")
    
    # 비즈니스.md 처리
    business_path = Path("docs/비즈니스.md")
    if business_path.exists():
        print(f"📄 {business_path} 분석 중...")
        sections = parse_markdown_structure(business_path)
        
        for idx, section in enumerate(sections):
            h2 = section.get("h2", "")
            h3 = section.get("h3", "")
            h4 = section.get("h4", "")
            content = section.get("content", "")
            
            title = h4 or h3 or h2
            if not title:
                continue
            
            section_id = f"비즈니스_{idx}"
            keywords = extract_keywords(content, title)
            
            metadata["categories"][section_id] = {
                "display_name": "비즈니스",
                "filename": "비즈니스.md",
                "h2_section": h2,
                "h3_section": h3,
                "h4_section": h4,
                "title": title,
                "start_line": section.get("start_line"),
                "end_line": section.get("end_line"),
                "keywords": keywords,
                "contact": {
                    "team": "P&C팀",
                    "name": "Ryan",
                    "phone": "연락처 미등록",
                    "email": "ryan@encar.com"
                }
            }
        
        print(f"✅ {len(sections)}개 섹션 추출됨")
    
    return metadata


if __name__ == "__main__":
    print("="*80)
    print("🔧 메타데이터 자동 생성 시작")
    print("="*80)
    
    # 메타데이터 생성
    metadata = generate_metadata()
    
    # 저장
    output_path = Path("data/documents_metadata.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 메타데이터 저장 완료: {output_path}")
    print(f"📊 총 {len(metadata['categories'])}개 섹션 생성됨")
    
    # 카테고리별 통계
    category_stats = {}
    for cat_id, cat_data in metadata["categories"].items():
        display_name = cat_data["display_name"]
        category_stats[display_name] = category_stats.get(display_name, 0) + 1
    
    print("\n📈 카테고리별 섹션 수:")
    for cat, count in category_stats.items():
        print(f"  - {cat}: {count}개")
    
    print("\n" + "="*80)


