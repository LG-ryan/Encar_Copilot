@echo off
chcp 65001 > nul
echo ================================================
echo   엔카생활가이드 PDF → Markdown 변환
echo   (표 + 이미지 + 텍스트 포함)
echo ================================================
echo.
echo OCR 건너뛰기 모드로 실행 중...
echo (스캔 PDF가 아닌 경우 더 빠릅니다)
echo.
python tools\pdf_to_markdown.py "엔카생활가이드.pdf" "docs\엔카생활가이드.md" --skip-ocr
echo.
echo ================================================
echo 변환 완료! docs\엔카생활가이드.md 확인하세요.
echo ================================================
pause


