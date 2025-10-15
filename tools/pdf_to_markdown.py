# tools/pdf_to_markdown.py
# 종합형 변환기: 텍스트 + 표 + 이미지까지 Markdown 변환
import fitz  # PyMuPDF
import pdfplumber
import base64, io, pathlib, ocrmypdf
from PIL import Image

def ensure_ocr(input_path, ocr_path):
    """OCR이 필요한 경우 자동 수행"""
    try:
        with open(input_path, 'rb') as f:
            content = f.read(2048)
        if b'/Font' in content:
            print("텍스트 PDF로 판단 → OCR 생략")
            return input_path
        print("스캔 PDF로 판단 → OCR 수행 중...")
        ocrmypdf.ocr(input_path, ocr_path, force_ocr=True, language="kor+eng")
        print("OCR 완료:", ocr_path)
        return ocr_path
    except Exception as e:
        print("OCR 판단 실패:", e)
        return input_path

def extract_tables(pdf_path):
    """표 추출"""
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            page_tables = page.extract_tables()
            if page_tables:
                for j, table in enumerate(page_tables):
                    if table:  # 빈 표가 아닌 경우만
                        try:
                            # None 값을 빈 문자열로 변환
                            rows = []
                            for row in table:
                                if row and any(cell for cell in row if cell):  # 빈 행 제외
                                    clean_row = [str(cell).strip() if cell else "" for cell in row]
                                    rows.append(" | ".join(clean_row))
                            
                            if rows:
                                md = "\n".join(rows)
                                tables.append(f"\n\n### [Page {i} - 표 {j+1}]\n\n| " + md.replace("\n", " |\n| ") + " |\n")
                        except Exception as e:
                            print(f"⚠️ Page {i} 표 추출 오류 (무시): {e}")
    return "\n".join(tables)

def extract_images(pdf_path, img_dir):
    """이미지를 base64로 Markdown에 포함"""
    md_blocks = []
    pathlib.Path(img_dir).mkdir(parents=True, exist_ok=True)
    with fitz.open(pdf_path) as pdf:
        for i, page in enumerate(pdf, 1):
            for j, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                pix = fitz.Pixmap(pdf, xref)
                if pix.n > 4:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                img_data = pix.tobytes("png")
                img_path = f"{img_dir}/page{i}_img{j}.png"
                with open(img_path, "wb") as f:
                    f.write(img_data)
                b64 = base64.b64encode(img_data).decode()
                md_blocks.append(f"\n\n### [Page {i} 이미지 {j}]\n![이미지](data:image/png;base64,{b64})\n")
    return "\n".join(md_blocks)

def extract_text(pdf_path):
    """텍스트 추출"""
    text_blocks = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            text_blocks.append(f"\n\n## [Page {i}]\n{text}")
    return "\n".join(text_blocks)

def pdf_to_markdown(input_pdf, output_md, skip_ocr=False):
    """
    PDF를 Markdown으로 변환
    skip_ocr=True면 OCR 단계를 건너뜀 (이미 텍스트가 있는 PDF인 경우)
    """
    if skip_ocr:
        print("⚡ OCR 건너뛰기 - 직접 변환")
        ocr_pdf = input_pdf
    else:
        ocr_pdf = ensure_ocr(input_pdf, "temp_ocr.pdf")
    
    print("📊 표 추출 중...")
    tables_md = extract_tables(ocr_pdf)
    
    print("📝 텍스트 추출 중...")
    text_md = extract_text(ocr_pdf)
    
    print("🖼️ 이미지 추출 중...")
    images_md = extract_images(ocr_pdf, "docs/images")
    
    full_md = f"# 엔카생활가이드\n\n{text_md}\n\n{tables_md}\n\n{images_md}"
    pathlib.Path(output_md).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(output_md).write_text(full_md, encoding="utf-8")
    print(f"✅ Markdown 변환 완료 → {output_md}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("사용법: python tools/pdf_to_markdown.py <입력.pdf> <출력.md> [--skip-ocr]")
        print("예시: python tools/pdf_to_markdown.py 엔카생활가이드.pdf docs/guide.md --skip-ocr")
        sys.exit(1)
    
    skip_ocr = "--skip-ocr" in sys.argv
    pdf_to_markdown(sys.argv[1], sys.argv[2], skip_ocr=skip_ocr)
