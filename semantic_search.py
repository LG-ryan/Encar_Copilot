"""
시맨틱 검색 엔진 - 100% 무료, 로컬 전용
Sentence Transformers + FAISS 사용
"""
import os
import json
import pickle
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class SemanticSearchEngine:
    def __init__(self, model_name='jhgan/ko-sroberta-multitask'):
        """
        한국어 시맨틱 검색 엔진 초기화
        model: jhgan/ko-sroberta-multitask (한국어 최적화)
        """
        print("🔄 시맨틱 검색 모델 로딩 중...")
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.documents = []
        self.metadata = []
        print("✅ 모델 로딩 완료!")
    
    def load_markdown_file(self, file_path: str) -> List[Dict]:
        """
        마크다운 파일을 읽어서 청크로 분할 (H3 단위 청킹)
        H2 = 카테고리 (메타데이터)
        H3 = 실제 청크 단위
        """
        print(f"📄 MD 파일 로딩: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # H3 단위로 분할
        chunks = []
        current_category = ""  # H2 카테고리
        current_section = ""   # H3 섹션 내용
        current_title = ""     # H3 제목
        
        for line in content.split('\n'):
            # [Page X] 라인은 건너뛰기
            if line.strip().startswith('[Page') and line.strip().endswith(']'):
                continue
            
            # H2: 카테고리 저장 (청크 분리 안함)
            if line.startswith('## ') and not line.startswith('###'):
                current_category = line.replace('##', '').strip()
                continue
            
            # H3: 실제 청크 단위로 분리
            if line.startswith('### '):
                # 이전 섹션 저장
                if current_section.strip() and current_title:
                    # [Page X] 텍스트 제거
                    cleaned_content = '\n'.join([
                        l for l in current_section.split('\n') 
                        if not (l.strip().startswith('[Page') and l.strip().endswith(']'))
                    ])
                    
                    chunks.append({
                        'category': current_category,  # H2 카테고리 추가
                        'title': current_title,
                        'content': cleaned_content.strip(),
                        'source': file_path
                    })
                
                # 새 H3 섹션 시작
                current_title = line.replace('###', '').strip()
                current_section = ""
            else:
                # H3 섹션 내용 누적
                current_section += line + '\n'
        
        # 마지막 섹션 저장
        if current_section.strip() and current_title:
            # [Page X] 텍스트 제거
            cleaned_content = '\n'.join([
                l for l in current_section.split('\n') 
                if not (l.strip().startswith('[Page') and l.strip().endswith(']'))
            ])
            
            chunks.append({
                'category': current_category,
                'title': current_title,
                'content': cleaned_content.strip(),
                'source': file_path
            })
        
        print(f"✅ {len(chunks)}개 청크 생성 완료")
        return chunks
    
    def load_faq_data(self, faq_file: str = 'data/faq_data.json') -> List[Dict]:
        """
        FAQ 데이터를 로드
        """
        print(f"📋 FAQ 데이터 로딩: {faq_file}")
        
        with open(faq_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        chunks = []
        for faq in data.get('faqs', []):
            chunks.append({
                'title': faq['question'],
                'content': f"질문: {faq['question']}\n\n답변: {faq['main_answer']}",
                'source': 'FAQ',
                'category': faq.get('category', ''),
                'department': faq.get('department', ''),
                'link': faq.get('link', ''),
                'faq_id': faq.get('id', 0)
            })
        
        print(f"✅ {len(chunks)}개 FAQ 로딩 완료")
        return chunks
    
    def build_index(self, documents: List[Dict]):
        """
        문서들을 벡터화하여 FAISS 인덱스 구축
        """
        print("🔨 벡터 인덱스 구축 중...")
        
        self.documents = documents
        self.metadata = documents
        
        # 문서를 텍스트로 변환 (제목 + 내용)
        texts = [f"{doc['title']}\n{doc['content']}" for doc in documents]
        
        # 벡터로 변환
        print("⏳ 임베딩 생성 중... (최초 1회만 수행)")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # FAISS 인덱스 생성
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # 내적(Inner Product) 사용
        
        # 정규화 (코사인 유사도를 위해)
        faiss.normalize_L2(embeddings)
        
        # 인덱스에 추가
        self.index.add(embeddings.astype('float32'))
        
        print(f"✅ 인덱스 구축 완료! (총 {len(documents)}개 문서)")
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """
        자연어 질문으로 검색
        
        Returns:
            List of (document, similarity_score) tuples
        """
        if self.index is None:
            raise ValueError("인덱스가 구축되지 않았습니다. build_index()를 먼저 실행하세요.")
        
        # 질문을 벡터로 변환
        query_vector = self.model.encode([query])
        faiss.normalize_L2(query_vector)
        
        # 검색
        scores, indices = self.index.search(query_vector.astype('float32'), top_k)
        
        # 결과 반환
        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx != -1:  # 유효한 인덱스인 경우
                results.append((self.metadata[idx], float(score)))
        
        return results
    
    def save_index(self, path: str = 'data/semantic_index'):
        """
        인덱스를 디스크에 저장
        """
        os.makedirs(path, exist_ok=True)
        
        # FAISS 인덱스 저장
        faiss.write_index(self.index, f'{path}/faiss.index')
        
        # 메타데이터 저장
        with open(f'{path}/metadata.pkl', 'wb') as f:
            pickle.dump(self.metadata, f)
        
        print(f"💾 인덱스 저장 완료: {path}")
    
    def load_index(self, path: str = 'data/semantic_index'):
        """
        저장된 인덱스 로드
        """
        # FAISS 인덱스 로드
        self.index = faiss.read_index(f'{path}/faiss.index')
        
        # 메타데이터 로드
        with open(f'{path}/metadata.pkl', 'rb') as f:
            self.metadata = pickle.load(f)
        
        print(f"📂 인덱스 로드 완료: {len(self.metadata)}개 문서")


def build_semantic_search_index():
    """
    시맨틱 검색 인덱스 구축 (최초 1회 실행)
    """
    engine = SemanticSearchEngine()
    
    # 모든 문서 로드
    all_docs = []
    
    # 1. FAQ 데이터
    all_docs.extend(engine.load_faq_data('data/faq_data.json'))
    
    # 2. 엔카생활가이드
    if os.path.exists('docs/엔카생활가이드.md'):
        all_docs.extend(engine.load_markdown_file('docs/엔카생활가이드.md'))
    
    # 3. 추가 MD 파일들 (있으면)
    for md_file in ['docs/IT가이드.md', 'docs/사업가이드.md']:
        if os.path.exists(md_file):
            all_docs.extend(engine.load_markdown_file(md_file))
    
    # 인덱스 구축
    engine.build_index(all_docs)
    
    # 저장
    engine.save_index()
    
    print(f"\n🎉 시맨틱 검색 인덱스 구축 완료!")
    print(f"📊 총 {len(all_docs)}개 문서 인덱싱")
    
    return engine


if __name__ == "__main__":
    # 인덱스 구축 및 테스트
    print("="*60)
    print("  시맨틱 검색 엔진 구축")
    print("="*60)
    print()
    
    engine = build_semantic_search_index()
    
    # 테스트 검색
    print("\n" + "="*60)
    print("  테스트 검색")
    print("="*60)
    
    test_queries = [
        "휴가가 언제 생겨?",
        "컴퓨터 비번 까먹었어",
        "회의실 예약 어떻게 해?",
        "쏘카 할인 받을 수 있어?"
    ]
    
    for query in test_queries:
        print(f"\n🔍 질문: {query}")
        results = engine.search(query, top_k=3)
        
        for i, (doc, score) in enumerate(results, 1):
            print(f"  {i}. [{score:.3f}] {doc['title'][:50]}...")


