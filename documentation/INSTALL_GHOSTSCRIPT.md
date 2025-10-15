# Ghostscript 설치 가이드

## Windows 설치

### 방법 1: 공식 웹사이트 (권장)

1. **다운로드**
   - https://ghostscript.com/releases/gsdnld.html
   - "Ghostscript 10.x for Windows (64 bit)" 다운로드

2. **설치**
   - 다운로드한 `.exe` 파일 실행
   - 기본 설정으로 설치 (보통 `C:\Program Files\gs\` 에 설치됨)

3. **환경 변수 설정**
   - 설치 경로의 `bin` 폴더를 PATH에 추가
   - 예: `C:\Program Files\gs\gs10.02.1\bin`
   
   **설정 방법:**
   - `Win + R` → `sysdm.cpl` 입력
   - "고급" 탭 → "환경 변수"
   - "시스템 변수"에서 `Path` 선택 → "편집"
   - "새로 만들기" → Ghostscript bin 경로 입력
   - 확인 → 터미널 재시작

4. **설치 확인**
   ```bash
   gswin64c --version
   ```

### 방법 2: Chocolatey (패키지 관리자 사용)

```powershell
# 관리자 권한 PowerShell에서:
choco install ghostscript
```

---

## 설치 후

터미널을 재시작하고 다시 실행:
```bash
python tools\pdf_to_markdown.py "엔카생활가이드.pdf" "docs\엔카생활가이드.md"
```


