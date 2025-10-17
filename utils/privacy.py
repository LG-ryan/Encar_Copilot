"""
개인정보 보호 유틸리티
로그 및 출력에서 민감 정보를 마스킹
"""
import re
from typing import Any, Dict


def mask_email(email: str) -> str:
    """
    이메일 주소 마스킹
    
    예:
        kim.cheolsu@encar.com → k***@encar.com
    """
    if not email or "@" not in email:
        return email
    
    local, domain = email.split("@", 1)
    if len(local) <= 1:
        return f"{local[0]}***@{domain}"
    return f"{local[0]}***@{domain}"


def mask_employee_id(employee_id: str) -> str:
    """
    사번 마스킹
    
    예:
        201234 → 20****
        EMP-1234 → EMP-****
    """
    if not employee_id or len(employee_id) <= 2:
        return "****"
    
    # 숫자만 있는 경우
    if employee_id.isdigit():
        return employee_id[:2] + "****"
    
    # 알파벳-숫자 조합
    prefix = "".join([c for c in employee_id if not c.isdigit()])
    return f"{prefix}****"


def mask_phone(phone: str) -> str:
    """
    전화번호 마스킹
    
    예:
        010-1234-5678 → 010-****-5678
        02-1234-5678 → 02-****-5678
    """
    if not phone:
        return phone
    
    # 하이픈으로 구분된 경우
    if "-" in phone:
        parts = phone.split("-")
        if len(parts) >= 3:
            parts[1] = "****"
        return "-".join(parts)
    
    # 하이픈 없이 연속된 숫자
    if len(phone) >= 8:
        return phone[:3] + "****" + phone[-4:]
    
    return "****"


def mask_name(name: str) -> str:
    """
    이름 마스킹
    
    예:
        김철수 → 김**
        John Doe → J*** D**
    """
    if not name or len(name) <= 1:
        return "*"
    
    # 한글 이름
    if all('\uac00' <= c <= '\ud7a3' or c.isspace() for c in name):
        if len(name) == 2:
            return name[0] + "*"
        return name[0] + "*" * (len(name) - 1)
    
    # 영문 이름 (공백으로 구분)
    if " " in name:
        parts = name.split()
        masked_parts = [p[0] + "***" for p in parts]
        return " ".join(masked_parts)
    
    # 단일 단어
    return name[0] + "***"


def mask_pii_in_text(text: str) -> str:
    """
    텍스트에서 모든 개인정보 자동 마스킹
    
    - 이메일: xxx@encar.com → ***@encar.com
    - 전화번호: 010-1234-5678 → 010-****-5678
    - 사번 패턴: 201234 → 20****
    
    Args:
        text: 원본 텍스트
        
    Returns:
        마스킹된 텍스트
    """
    if not text:
        return text
    
    # 이메일 마스킹
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    text = re.sub(
        email_pattern,
        lambda m: mask_email(m.group()),
        text
    )
    
    # 전화번호 마스킹 (010-1234-5678, 02-123-4567 등)
    phone_pattern = r'\b0\d{1,2}-\d{3,4}-\d{4}\b'
    text = re.sub(
        phone_pattern,
        lambda m: mask_phone(m.group()),
        text
    )
    
    # 6자리 숫자 (사번으로 추정)
    employee_id_pattern = r'\b\d{6}\b'
    text = re.sub(
        employee_id_pattern,
        lambda m: mask_employee_id(m.group()),
        text
    )
    
    return text


def safe_log_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    딕셔너리 데이터를 로그 안전한 형태로 변환
    
    - email, employee_id, phone 등의 키는 자동 마스킹
    - user_id, user_name 등도 마스킹
    
    Args:
        data: 원본 딕셔너리
        
    Returns:
        마스킹된 딕셔너리 (원본은 변경하지 않음)
    """
    sensitive_keys = {
        "email", "user_email", "employee_id", "user_id",
        "phone", "user_phone", "telephone",
        "name", "user_name", "username"
    }
    
    safe_data = {}
    for key, value in data.items():
        if key.lower() in sensitive_keys:
            if "email" in key.lower():
                safe_data[key] = mask_email(str(value))
            elif "phone" in key.lower() or "telephone" in key.lower():
                safe_data[key] = mask_phone(str(value))
            elif "name" in key.lower():
                safe_data[key] = mask_name(str(value))
            else:
                safe_data[key] = mask_employee_id(str(value))
        else:
            safe_data[key] = value
    
    return safe_data


def mask_question_for_log(question: str) -> str:
    """
    질문 로그 시 민감정보 자동 마스킹
    
    Args:
        question: 원본 질문
        
    Returns:
        마스킹된 질문
    """
    # 개인정보 패턴 마스킹
    masked = mask_pii_in_text(question)
    
    # 너무 긴 질문은 잘라냄 (DOS 방지)
    if len(masked) > 200:
        masked = masked[:200] + "..."
    
    return masked

