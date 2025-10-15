"""
엔카생활가이드 PDF → Markdown 변환 스크립트
표 + 이미지 + 텍스트 완전 변환
"""
import sys
sys.path.insert(0, 'tools')

from pdf_to_markdown import pdf_to_markdown

if __name__ == "__main__":
    print("="*60)
    print("  엔카생활가이드 PDF → Markdown 변환")
    print("  표 + 이미지 + 텍스트 완전 변환")
    print("="*60)
    print()
    
    input_pdf = "엔카생활가이드.pdf"
    output_md = "docs/엔카생활가이드.md"
    
    # OCR 건너뛰기 (일반 PDF이므로)
    pdf_to_markdown(input_pdf, output_md, skip_ocr=True)
    
    print()
    print("="*60)
    print("  ✅ 변환 완료!")
    print(f"  📁 위치: {output_md}")
    print(f"  🖼️  이미지: docs/images/")
    print("="*60)


