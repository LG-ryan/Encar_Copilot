"""
엔카생활가이드 기반 FAQ만 적용 (기존 FAQ 삭제)
"""
import json

# 엔카생활가이드 기반 FAQ 로드
with open('data/faq_data_expanded.json', 'r', encoding='utf-8') as f:
    expanded_faq = json.load(f)

# 추가 FAQ (리조트, BBL, 쏘카, 교육, 명함, 퀵, 유니폼 등)
additional_faqs = [
    {
        "id": 121,
        "category": "복리후생",
        "question": "리조트는 어떻게 이용하나요?",
        "main_answer": "회사 법인 회원권으로 리조트를 이용할 수 있습니다!\n\n**이용 가능 리조트**:\n- 아난티 펜트하우스\n- 리솜리조트 (제천/덕산/안면도)\n- 소노 전국\n\n**신청 방법 (아난티/리솜)**:\n1. 리조트 추첨 안내 메일 확인\n2. 이용 가능 일자에 신청\n3. 추첨 진행\n4. 당첨 시 리조트 안내 메일 확인\n5. 예약 당일 방문\n6. 다음달 10일 회사 지원금 경비 계좌 지급\n\n**소노호텔앤리조트**:\n1. 소노리조트 사이트에서 개인회원 가입\n2. 원하는 날짜/객실/지역 조회\n3. 그룹웨어 → 엔카닷컴 복리후생 → 소노리조트 신청 게시판에 글 작성",
        "keywords": ["리조트", "아난티", "리솜", "소노", "휴가", "여행"],
        "department": "P&C팀",
        "link": "http://gwa.encar.com/welfare/resort"
    },
    {
        "id": 122,
        "category": "복리후생",
        "question": "엔카상품권(BBL)은 뭔가요?",
        "main_answer": "BBL은 직책자가 발행하는 지류 상품권입니다.\n\n**용도**: 프로젝트, 협업, 행사 TF 등에 대한 감사 표현\n\n**정산 방법**:\n1. 수령한 BBL 모아두기\n2. 매월 공지메일의 BBL 구글취합폼에 직접 입력\n3. 실물 BBL을 P&C팀 담당자에게 제출\n4. 익월 10일 경비계좌로 입금\n\n💡 BBL은 현금으로 교환되는 상품권입니다!",
        "keywords": ["BBL", "상품권", "엔카상품권", "정산", "감사"],
        "department": "P&C팀",
        "link": "http://gwa.encar.com/bbl"
    },
    {
        "id": 123,
        "category": "복리후생",
        "question": "쏘카 비즈니스는 어떻게 이용하나요?",
        "main_answer": "엔카 임직원은 쏘카 비즈니스 제휴 혜택을 받을 수 있습니다!\n\n**혜택 내용**:\n- 상시 대여료 할인: 주중 60%, 주말 40%\n- 퇴출근용 16시간 대여요금 8,000원 (만 26세 이상)\n\n**신청 방법**:\n1. 전자결재 → [인사]쏘카 비즈니스 개인정보 제3자 제공동의서 작성\n2. 이름, 회사 이메일주소, 전화번호 기입\n3. P&C팀 담당자가 쏘카에 사용자 등록\n4. SNS로 전송된 URL로 로그인\n\n⚠️ 개인적인 용도로만 사용, 반드시 개인카드로 결제",
        "keywords": ["쏘카", "비즈니스", "차량", "대여", "할인"],
        "department": "P&C팀",
        "link": "https://socar.kr/business"
    },
    {
        "id": 124,
        "category": "복리후생",
        "question": "단체보험은 어떻게 되나요?",
        "main_answer": "엔카닷컴은 DB손해보험 단체보험에 가입되어 있습니다.\n\n**플랜 종류**:\n- A플랜: 실비보험 포함\n- B플랜: 실비 미포함, 수술비 및 입원일당 보장\n\n**기본 가입**: A플랜, 무자녀 (매년 2월 변경 가능)\n\n**문의**: Marsh 이윤정 (02-2095-8254)",
        "keywords": ["단체보험", "보험", "실비", "DB손해보험"],
        "department": "P&C팀",
        "link": "http://gwa.encar.com/insurance"
    },
    {
        "id": 125,
        "category": "복리후생",
        "question": "EAP 프로그램이 뭔가요?",
        "main_answer": "EAP는 임직원 전문 상담 서비스입니다.\n\n**상담 분야**: 직무 스트레스, 대인관계, 개인 정서, 부부/자녀, 재무/법률\n\n**신청 방법**:\n- 전화: 080-822-1376\n- 카카오톡: '넛지eap' 플러스친구 등록\n\n비밀 보장, 무료 상담!",
        "keywords": ["EAP", "상담", "심리", "스트레스"],
        "department": "P&C팀",
        "link": "https://wiki.encar.com/eap"
    },
    {
        "id": 126,
        "category": "복리후생",
        "question": "동호회는 어떤 게 있나요?",
        "main_answer": "엔카에는 5개 동호회가 활동 중입니다!\n\n**동호회**: 농구, 볼링, 자전거, 카트, 핸드메이드\n**참여**: 140여 명\n**가입**: 재직 중인 누구나\n**신규 동호회**: 5인 이상 모집 후 P&C팀 신청",
        "keywords": ["동호회", "동아리", "취미", "모임"],
        "department": "P&C팀",
        "link": "http://gwa.encar.com/club"
    },
    {
        "id": 127,
        "category": "HR",
        "question": "교육은 어떻게 신청하나요?",
        "main_answer": "외부 교육 신청 프로세스입니다.\n\n**[교육 전]**\n1. 원하는 교육 선정 (상위 결재권자와 상의)\n2. 교육신청서 작성: 전자결재 → [인사] 교육신청서\n3. 교육비 결제 (10만원 미만: 법인카드 / 10만원 이상: 지출결의서)\n\n**[교육 후]**\n1. 교육결과보고서 작성\n2. 정산결의서 작성",
        "keywords": ["교육", "신청", "외부교육", "교육비"],
        "department": "P&C팀",
        "link": "http://gwa.encar.com/education"
    },
    {
        "id": 128,
        "category": "총무",
        "question": "명함은 어떻게 신청하나요?",
        "main_answer": "명함 신청은 온라인으로 간편하게!\n\n**신청 방법**:\n1. http://encar.onehp.co.kr 접속\n2. ID: encarcom / PW: encarcom\n3. 주문하기 버튼 클릭\n4. 앞면과 뒷면 작성\n5. 미리보기 후 주문\n\n배송 기간: 5-7일",
        "keywords": ["명함", "신청", "제작", "비즈니스카드"],
        "department": "총무팀",
        "link": "http://encar.onehp.co.kr"
    },
    {
        "id": 129,
        "category": "총무",
        "question": "퀵 서비스는 어떻게 이용하나요?",
        "main_answer": "업무상 퀵 배송이 필요한 경우:\n\n**연락처**: 1588-0025\n**회원번호**: 87750\n\n**본사 주소**: 서울시 중구 통일로 2길 16 AIA 타워 18,19,22층",
        "keywords": ["퀵", "배송", "택배", "빠른배송"],
        "department": "총무팀",
        "link": "https://wiki.encar.com/quick"
    },
    {
        "id": 130,
        "category": "복리후생",
        "question": "웰컴 키트는 뭐가 들어있나요?",
        "main_answer": "신규 입사자를 위한 웰컴 키트를 제공합니다!\n\n**포함 내용**:\n- 엔카 굿즈\n- 업무 필수 아이템\n- 웰컴 가이드\n\n💡 엔카 가족이 되신 것을 환영합니다! 🎉",
        "keywords": ["웰컴키트", "신규입사", "굿즈", "입사"],
        "department": "P&C팀",
        "link": "http://gwa.encar.com/welcome"
    }
]

# 엔카생활가이드 기반 FAQ만 사용
new_faqs = expanded_faq['faqs'] + additional_faqs

# ID 순으로 정렬
new_faqs.sort(key=lambda x: x['id'])

# 최종 데이터
final_data = {
    "faqs": new_faqs,
    "metadata": {
        "total_count": len(new_faqs),
        "source": "엔카생활가이드 전용",
        "version": "3.0",
        "last_updated": "2025-10-14",
        "note": "기존 FAQ 제거, 엔카생활가이드 기반만 사용"
    }
}

# 저장
with open('data/faq_data.json', 'w', encoding='utf-8') as f:
    json.dump(final_data, f, ensure_ascii=False, indent=2)

print("="*60)
print("✅ 엔카생활가이드 기반 FAQ 적용 완료!")
print("="*60)
print(f"📊 총 {len(new_faqs)}개의 FAQ (기존 FAQ 제거됨)")
print(f"📁 저장 위치: data/faq_data.json")

# 카테고리별 통계
from collections import Counter
category_count = Counter([faq['category'] for faq in new_faqs])
print(f"\n📋 카테고리별 통계:")
for cat, count in sorted(category_count.items()):
    print(f"  - {cat}: {count}개")

print("\n🎉 서버를 재시작하면 새 FAQ가 적용됩니다!")
print("   python run.py")


