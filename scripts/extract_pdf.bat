@echo off
chcp 65001 > nul
echo PDF 텍스트 추출 중...
python tools\pdf_to_text_simple.py "엔카생활가이드.pdf" "docs\엔카생활가이드.txt"
pause


