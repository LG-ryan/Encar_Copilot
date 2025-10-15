import json

# FAQ 데이터 로드
with open('data/faq_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 모든 FAQ의 답변에서 연속된 줄바꿈 제거
for faq in data['faqs']:
    if 'main_answer' in faq:
        # 연속된 \n을 하나로 축소
        faq['main_answer'] = faq['main_answer'].replace('\n\n\n', '\n').replace('\n\n', '\n')

# 저장
with open('data/faq_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ {len(data['faqs'])}개 FAQ의 공백 최적화 완료!")


