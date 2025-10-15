"""
엔카생활가이드 마크다운에서 완전한 FAQ 데이터 생성
"""
import json
import re

# 기존 FAQ 데이터 로드
with open('data/faq_data.json', 'r', encoding='utf-8') as f:
    original_faq = json.load(f)

# 확장 FAQ 데이터 로드
with open('data/faq_data_expanded.json', 'r', encoding='utf-8') as f:
    expanded_faq = json.load(f)

# 추가 FAQ (리조트, BBL, 쏘카, 교육, 명함, 퀵, 유니폼 등)
additional_faqs = [
    {
        "id": 121,
        "category": "복리후생",
        "question": "리조트는 어떻게 이용하나요?",
        "main_answer": "회사 법인 회원권으로 리조트를 이용할 수 있습니다!\n\n**이용 가능 리조트**:\n- 아난티 펜트하우스\n- 리솜리조트 (제천/덕산/안면도)\n- 소노 전국\n\n**신청 방법 (아난티/리솜)**:\n1. 리조트 추첨 안내 메일 확인\n2. 이용 가능 일자에 신청\n3. 추첨 진행\n4. 당첨 시 리조트 안내 메일 확인\n5. 예약 당일 방문\n6. 다음달 10일 회사 지원금 경비 계좌 지급\n\n**소노호텔앤리조트**:\n1. 소노리조트 사이트(www.sonohotelsresorts.com)에서 개인회원 가입\n2. 원하는 날짜/객실/지역 조회\n3. 그룹웨어 → 엔카닷컴 복리후생 → 소노리조트 신청 게시판에 글 작성\n\n생생한 후기: https://bit.ly/3GCgrxP",
        "keywords": ["리조트", "아난티", "리솜", "소노", "휴가", "여행"],
        "department": "P&C팀",
        "link": "http://gwa.encar.com/welfare/resort"
    },
    {
        "id": 122,
        "category": "복리후생",
        "question": "엔카상품권(BBL)은 뭔가요?",
        "main_answer": "BBL은 직책자가 발행하는 지류 상품권입니다.\n\n**용도**: 프로젝트, 협업, 행사 TF 등에 대한 감사 표현\n\n**정산 방법**:\n1. 수령한 BBL 모아두기\n2. 매월 공지메일의 BBL 구글취합폼에 직접 입력\n3. 실물 BBL을 P&C팀 담당자에게 제출\n4. 익월 10일 경비계좌로 입금 (10일이 공휴일/주말이면 가장 가까운 평일)\n\n💡 BBL은 현금으로 교환되는 상품권입니다!",
        "keywords": ["BBL", "상품권", "엔카상품권", "정산", "감사"],
        "department": "P&C팀",
        "link": "http://gwa.encar.com/bbl"
    },
    {
        "id": 123,
        "category": "복리후생",
        "question": "쏘카 비즈니스는 어떻게 이용하나요?",
        "main_answer": "엔카 임직원은 쏘카 비즈니스 제휴 혜택을 받을 수 있습니다!\n\n**혜택 내용**:\n- 상시 대여료 할인: 주중 60%, 주말 40% (만 21세 이상, 면허취득 1년 이상)\n- 퇴출근용 16시간 대여요금 8,000원 (만 26세 이상, 면허취득 1년 이상)\n\n**신청 방법**:\n1. 전자결재 → 양식 → [인사]쏘카 비즈니스 개인정보 제3자 제공동의서 작성\n2. 이름, 회사 이메일주소, 전화번호 기입\n3. P&C팀 담당자가 쏘카에 사용자 등록\n4. SNS로 전송된 URL을 통해 로그인 및 비즈니스 프로필 등록\n\n⚠️ **주의사항**:\n- 개인적인 용도로만 사용 가능\n- 반드시 개인카드로 결제 (법인카드 사용 금지)\n- 업무용 차량은 법인 차량 이용\n- 개인 이용 내역, 위치정보가 관리자 페이지에 노출됨\n\n상세 안내: https://bit.ly/3muDWly",
        "keywords": ["쏘카", "비즈니스", "차량", "대여", "할인"],
        "department": "P&C팀",
        "link": "https://socar.kr/business"
    },
    {
        "id": 124,
        "category": "복리후생",
        "question": "단체보험은 어떻게 되나요?",
        "main_answer": "엔카닷컴은 DB손해보험 단체보험에 가입되어 있습니다.\n\n**적용 기간**: 입사일 ~ 퇴사일\n\n**플랜 종류**:\n- A플랜: 실비보험 포함\n- B플랜: 실비 미포함, 수술비 및 입원일당 보장\n\n**기본 가입**: A플랜, 무자녀 (매년 2월 변경/갱신 가능)\n\n**확인 방법**:\n그룹웨어 → 게시판 → 엔카닷컴 복리후생 → '단체상해보험 지급 기준 및 신청방법 안내'\n\n**문의**:\nMarsh 이윤정\n- 이메일: Mcare.korea@marsh.com\n- 전화: 02-2095-8254 (부재 시: 1577-3739)\n\n💡 Marsh는 엔카닷컴의 단체보험 전문 에이전시입니다!",
        "keywords": ["단체보험", "보험", "실비", "DB손해보험", "보장"],
        "department": "P&C팀",
        "link": "http://gwa.encar.com/insurance"
    },
    {
        "id": 125,
        "category": "복리후생",
        "question": "EAP 프로그램이 뭔가요?",
        "main_answer": "EAP(Employee Assistance Program)는 임직원 전문 상담 서비스입니다.\n\n**상담 분야**:\n- 직무 스트레스\n- 대인관계\n- 개인 정서\n- 부부/자녀 관계\n- 재무/법률 상담 등\n\n**신청 방법**:\n1. 전화: 080-822-1376\n2. 카카오톡: '넛지eap' 플러스친구 등록 후 상담신청\n\n**특징**:\n- 비밀 보장\n- 무료 상담\n- 전문 상담사 배정\n\n💡 혼자 고민하지 마시고 전문가의 도움을 받아보세요!",
        "keywords": ["EAP", "상담", "심리", "스트레스", "고민"],
        "department": "P&C팀",
        "link": "https://wiki.encar.com/eap"
    },
    {
        "id": 126,
        "category": "복리후생",
        "question": "동호회는 어떤 게 있나요?",
        "main_answer": "엔카에는 다양한 동호회가 활동 중입니다!\n\n**현재 활동 중**:\n- 농구 동호회\n- 볼링 동호회\n- 자전거 동호회\n- 카트 동호회\n- 핸드메이드 동호회\n\n**참여 현황**: 총 5개 동호회, 140여 명 임직원 참여\n\n**가입 조건**: 엔카닷컴에 재직 중인 누구나!\n\n**활동 경비**: 기본적으로 자체 부담 원칙, 회사 지원금 일부 지급\n\n**새 동호회 만들기**:\n5인 이상 모집 후 P&C팀에 신청\n\n**활동 사진**: 그룹웨어 → 게시판 → 사내게시판 → 동호회",
        "keywords": ["동호회", "동아리", "취미", "모임", "활동"],
        "department": "P&C팀",
        "link": "http://gwa.encar.com/club"
    },
    {
        "id": 127,
        "category": "HR",
        "question": "교육은 어떻게 신청하나요?",
        "main_answer": "외부 교육 신청 프로세스입니다.\n\n**[교육 전]**\n1. 원하는 교육 선정 (상위 결재권자와 상의)\n2. 교육신청서 작성: 전자결재 → [인사] 교육신청서\n   - 결재라인: 소속 상위 직책자 → P&C팀 팀장 → 경영기획실 실장 → 직속 임원\n3. 교육비 결제\n   - 10만원 미만: 개인 법인카드 결제\n   - 10만원 이상: 지출결의서 작성\n\n**[교육 후]**\n1. 교육결과보고서 작성\n2. 정산결의서 작성 (계정: 교육훈련비-사외)\n\n⚠️ 법인카드 결제 시 법인카드 정산 품의에 교육신청서 추가 필요\n\n자세한 안내: 그룹웨어 복리후생 게시판",
        "keywords": ["교육", "신청", "외부교육", "교육비", "지출"],
        "department": "P&C팀",
        "link": "http://gwa.encar.com/education"
    },
    {
        "id": 128,
        "category": "총무",
        "question": "명함은 어떻게 신청하나요?",
        "main_answer": "명함 신청은 온라인으로 간편하게 하실 수 있습니다!\n\n**신청 방법**:\n1. 사이트 접속: http://encar.onehp.co.kr\n2. 로그인: ID: encarcom / PW: encarcom\n3. 주문하기 버튼 클릭\n4. 앞면과 뒷면 작성\n5. 미리보기 확인 후 주문하기\n\n**배송 기간**: 신청 후 약 5-7일 소요\n**배송 위치**: 사무실 우편함\n\n💡 영문 명함도 함께 제작 가능합니다!",
        "keywords": ["명함", "신청", "제작", "비즈니스카드", "디자인"],
        "department": "총무팀",
        "link": "http://encar.onehp.co.kr"
    },
    {
        "id": 129,
        "category": "총무",
        "question": "퀵 서비스는 어떻게 이용하나요?",
        "main_answer": "업무상 거래처 등에 퀵 배송이 필요한 경우 이용하실 수 있습니다.\n\n**연락처**: 1588-0025\n**고객사 회원번호**: 87750 (요청 시 알려주세요)\n\n**참고 정보**:\n- 본사 주소: 서울시 중구 통일로 2길 16(순화동 216) AIA 타워 18,19,22층\n- 콜센터(대표번호): 1599-5455\n\n💡 수발신지 주소를 정확히 알려주세요!",
        "keywords": ["퀵", "배송", "택배", "빠른배송", "거래처"],
        "department": "총무팀",
        "link": "https://wiki.encar.com/quick"
    },
    {
        "id": 130,
        "category": "복리후생",
        "question": "웰컴 키트는 뭐가 들어있나요?",
        "main_answer": "신규 입사자를 위한 웰컴 키트를 제공합니다!\n\n**포함 내용**:\n- 엔카 굿즈\n- 업무 필수 아이템\n- 웰컴 가이드\n- 기타 유용한 아이템들\n\n자세한 내용은 그룹웨어 복리후생 게시판에서 확인하실 수 있습니다.\n\n💡 엔카 가족이 되신 것을 환영합니다! 🎉",
        "keywords": ["웰컴키트", "신규입사", "굿즈", "입사", "환영"],
        "department": "P&C팀",
        "link": "http://gwa.encar.com/welcome"
    }
]

# 모든 FAQ 통합
all_faqs = original_faq['faqs'] + expanded_faq['faqs'] + additional_faqs

# ID 중복 제거 및 정렬
seen_ids = set()
unique_faqs = []
for faq in all_faqs:
    if faq['id'] not in seen_ids:
        seen_ids.add(faq['id'])
        unique_faqs.append(faq)

# ID 순으로 정렬
unique_faqs.sort(key=lambda x: x['id'])

# 최종 데이터
final_data = {
    "faqs": unique_faqs,
    "metadata": {
        "total_count": len(unique_faqs),
        "source": "엔카생활가이드 + 기존 FAQ",
        "version": "2.0",
        "last_updated": "2025-10-14"
    }
}

# 저장
with open('data/faq_data_complete.json', 'w', encoding='utf-8') as f:
    json.dump(final_data, f, ensure_ascii=False, indent=2)

print(f"✅ 완전한 FAQ 데이터 생성 완료!")
print(f"📊 총 {len(unique_faqs)}개의 FAQ")
print(f"📁 저장 위치: data/faq_data_complete.json")

# 카테고리별 통계
from collections import Counter
category_count = Counter([faq['category'] for faq in unique_faqs])
print(f"\n📋 카테고리별 통계:")
for cat, count in category_count.most_common():
    print(f"  - {cat}: {count}개")


