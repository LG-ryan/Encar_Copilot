"""
간단한 PDF to Text 변환기
OCR 없이 PyMuPDF로 텍스트만 추출
"""
import fitz  # PyMuPDF
import sys
import pathlib

def pdf_to_text(input_pdf, output_file):
    """PDF를 텍스트로 변환"""
    print(f"📄 PDF 읽는 중: {input_pdf}")
    
    try:
        # PDF 열기
        doc = fitz.open(input_pdf)
        total_pages = len(doc)
        print(f"📖 총 {total_pages}페이지 발견")
        
        # 모든 페이지의 텍스트 추출
        all_text = []
        for i, page in enumerate(doc, 1):
            print(f"⏳ {i}/{total_pages} 페이지 처리 중...", end="\r")
            text = page.get_text()
            if text.strip():
                all_text.append(f"\n\n{'='*60}\n페이지 {i}\n{'='*60}\n\n{text}")
        
        doc.close()
        
        # 파일로 저장
        full_text = "\n".join(all_text)
        pathlib.Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(output_file).write_text(full_text, encoding="utf-8")
        
        print(f"\n✅ 변환 완료!")
        print(f"📁 저장 위치: {output_file}")
        print(f"📊 추출된 문자 수: {len(full_text):,}자")
        
        return full_text
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("사용법: python tools/pdf_to_text_simple.py <입력.pdf> <출력.txt>")
        print("예시: python tools/pdf_to_text_simple.py 엔카생활가이드.pdf docs/guide.txt")
        sys.exit(1)
    
    input_pdf = sys.argv[1]
    output_file = sys.argv[2]
    
    pdf_to_text(input_pdf, output_file)


