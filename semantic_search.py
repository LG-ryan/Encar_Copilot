"""
RAG 기반 시맨틱 검색 엔진 v2.0
- 자연어 MD 파일 지원
- H3/H4 기반 Chunk 분할
- Multi-chunk 답변 조합
- LLM 없이 동작 (Lightweight RAG)
"""
import os
import json
import pickle
import re
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np


class SemanticSearchEngineRAG:
    def __init__(self, model_name='jhgan/ko-sroberta-multitask'):
        """
        RAG 기반 한국어 시맨틱 검색 엔진 초기화
        """
        print("🔄 시맨틱 검색 모델 로딩 중 (RAG 버전)...")
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.documents = []
        self.metadata = []
        print("✅ 모델 로딩 완료!")
    
    def load_markdown_file(self, file_path: str) -> List[Dict]:
        """
        자연어 마크다운 파일을 의미 단위(Semantic Chunk)로 분할
        
        분할 전략:
        - H2: 카테고리 (메타데이터)
        - H3: Primary Chunk (독립적인 주제)
        - H4: Secondary Chunk (H3의 세부 주제, H3보다 우선)
        - H5: Tertiary Chunk (H4의 세부 주제, H4보다 우선)
        
        우선순위: H5 > H4 > H3
        """
        print(f"📄 MD 파일 로딩 (RAG): {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        chunks = []
        current_h2 = ""
        current_h3 = ""
        current_h3_content = ""
        current_h4 = ""
        current_h4_content = ""
        
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # 페이지/이미지 라인 건너뛰기
            if self._should_skip_line(line):
                i += 1
                continue
            
            # H2: 카테고리 (청크 생성 안함, 메타데이터만)
            if line.startswith('## ') and not line.startswith('###'):
                current_h2 = line.replace('##', '').strip()
                i += 1
                continue
            
            # H5: 가장 세부적인 주제 (최우선 청크)
            if line.startswith('##### '):
                # 이전 H4 청크 저장
                if current_h4_content.strip():
                    chunks.append(self._create_chunk(
                        h2=current_h2,
                        h3=current_h3,
                        h4=current_h4,
                        content=current_h4_content,
                        level='h4',
                        source=file_path
                    ))
                    current_h4_content = ""
                
                # H5 청크 수집
                h5_title = line.replace('#####', '').strip()
                h5_content = ""
                i += 1
                
                # H5 내용 수집 (다음 헤더 전까지)
                while i < len(lines) and not self._is_header(lines[i]):
                    if not self._should_skip_line(lines[i]):
                        h5_content += lines[i] + '\n'
                    i += 1
                
                # H5 청크 생성
                chunks.append(self._create_chunk(
                    h2=current_h2,
                    h3=current_h3,
                    h4=current_h4,
                    h5=h5_title,
                    content=h5_content,
                    level='h5',
                    source=file_path
                ))
                continue
            
            # H4: 세부 주제 (H3보다 우선)
            if line.startswith('#### '):
                # 이전 H4 청크 저장
                if current_h4_content.strip():
                    chunks.append(self._create_chunk(
                        h2=current_h2,
                        h3=current_h3,
                        h4=current_h4,
                        content=current_h4_content,
                        level='h4',
                        source=file_path
                    ))
                
                # 새 H4 시작
                current_h4 = line.replace('####', '').strip()
                current_h4_content = ""
                i += 1
                continue
            
            # H3: 주요 주제
            if line.startswith('### '):
                # 이전 H4 청크 저장
                if current_h4_content.strip():
                    chunks.append(self._create_chunk(
                        h2=current_h2,
                        h3=current_h3,
                        h4=current_h4,
                        content=current_h4_content,
                        level='h4',
                        source=file_path
                    ))
                    current_h4 = ""
                    current_h4_content = ""
                
                # 이전 H3 청크 저장 (H4가 없었던 경우)
                elif current_h3_content.strip():
                    chunks.append(self._create_chunk(
                        h2=current_h2,
                        h3=current_h3,
                        content=current_h3_content,
                        level='h3',
                        source=file_path
                    ))
                
                # 새 H3 시작
                current_h3 = line.replace('###', '').strip()
                current_h3_content = ""
                i += 1
                continue
            
            # 일반 내용 수집
            if current_h4:
                # H4가 활성화되어 있으면 H4 내용으로
                current_h4_content += line + '\n'
            elif current_h3:
                # H3만 활성화되어 있으면 H3 내용으로
                current_h3_content += line + '\n'
            
            i += 1
        
        # 마지막 청크 저장
        if current_h4_content.strip():
            chunks.append(self._create_chunk(
                h2=current_h2,
                h3=current_h3,
                h4=current_h4,
                content=current_h4_content,
                level='h4',
                source=file_path
            ))
        elif current_h3_content.strip():
            chunks.append(self._create_chunk(
                h2=current_h2,
                h3=current_h3,
                content=current_h3_content,
                level='h3',
                source=file_path
            ))
        
        # 빈 청크 필터링
        chunks = [c for c in chunks if c['content'].strip()]
        
        print(f"✅ {len(chunks)}개 청크 생성 완료 (RAG)")
        return chunks
    
    def _should_skip_line(self, line: str) -> bool:
        """건너뛸 라인 판단"""
        stripped = line.strip()
        return (
            (stripped.startswith('[Page') and stripped.endswith(']')) or
            stripped.startswith('![이미지](data:image') or
            stripped.startswith('![이미지](page')
        )
    
    def _is_header(self, line: str) -> bool:
        """헤더 라인 판단"""
        return line.startswith('#')
    
    def _create_chunk(self, h2: str, h3: str, content: str, level: str, 
                     source: str, h4: str = "", h5: str = "") -> Dict:
        """
        청크 생성
        
        level: 'h3', 'h4', 'h5'
        """
        # 제목 결정 (가장 깊은 레벨 우선)
        if level == 'h5' and h5:
            title = h5
            parent = h4 if h4 else h3
        elif level == 'h4' and h4:
            title = h4
            parent = h3
        else:
            title = h3
            parent = h2
        
        # 키워드 추출
        keywords = self._extract_keywords(f"{h2} {h3} {h4} {h5} {content[:200]}")
        
        # **질문:** / **답변:** 형식 확인 및 추출
        question = ""
        answer = ""
        if '**질문:**' in content and '**답변:**' in content:
            qa_match = re.search(r'\*\*질문:\*\*\s*(.+?)\s*\*\*답변:\*\*\s*(.+)', 
                                content, re.DOTALL)
            if qa_match:
                question = qa_match.group(1).strip()
                answer = qa_match.group(2).strip()
        
        return {
            'h2': h2,  # 카테고리
            'h3': h3,  # 주요 주제
            'h4': h4,  # 세부 주제
            'h5': h5,  # 더 세부 주제
            'title': title,  # 청크 제목 (가장 깊은 레벨)
            'content': content.strip(),
            'level': level,  # 'h3', 'h4', 'h5'
            'parent': parent,  # 부모 주제
            'keywords': keywords,
            'source': source,
            'question': question,  # FAQ 형식인 경우
            'answer': answer,  # FAQ 형식인 경우
            'chunk_type': 'qa' if question else 'natural'  # 청크 타입
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """텍스트에서 키워드 추출"""
        words = re.findall(r'[가-힣a-zA-Z0-9]+', text)
        keywords = list(set([w for w in words if len(w) >= 2]))
        return keywords[:20]
    
    def load_all_markdown_files(self, directory: str = 'docs') -> List[Dict]:
        """docs 폴더의 모든 MD 파일 로딩"""
        from pathlib import Path
        all_chunks = []
        
        md_files = list(Path(directory).glob('*.md'))
        print(f"📂 {len(md_files)}개의 MD 파일 발견: {[f.name for f in md_files]}")
        
        for md_file in sorted(md_files):
            try:
                chunks = self.load_markdown_file(str(md_file))
                all_chunks.extend(chunks)
            except Exception as e:
                print(f"⚠️  {md_file.name} 로딩 실패: {e}")
        
        print(f"🎉 총 {len(all_chunks)}개 청크 로딩 완료 (RAG)!")
        return all_chunks
    
    def build_index(self, documents: List[Dict]):
        """FAISS 인덱스 구축"""
        print("🔨 벡터 인덱스 구축 중 (RAG)...")
        
        self.documents = documents
        self.metadata = documents
        
        # 검색용 텍스트 생성 (제목 + 내용 + 계층 정보)
        texts = []
        for doc in documents:
            # 계층 정보를 포함하여 검색 정확도 향상
            hierarchy = f"{doc['h2']} > {doc['h3']}"
            if doc['h4']:
                hierarchy += f" > {doc['h4']}"
            if doc['h5']:
                hierarchy += f" > {doc['h5']}"
            
            # FAQ 형식인 경우 질문 우선
            if doc['chunk_type'] == 'qa' and doc['question']:
                text = f"{hierarchy}\n질문: {doc['question']}\n답변: {doc['content']}"
            else:
                text = f"{hierarchy}\n{doc['title']}\n{doc['content']}"
            
            texts.append(text)
        
        # 벡터로 변환
        print("⏳ 임베딩 생성 중...")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # FAISS 인덱스 생성
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        
        # 정규화 (코사인 유사도)
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings.astype('float32'))
        
        print(f"✅ 인덱스 구축 완료! (총 {len(documents)}개 문서)")
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """자연어 질문으로 검색"""
        if self.index is None:
            raise ValueError("인덱스가 구축되지 않았습니다.")
        
        # 질문을 벡터로 변환
        query_vector = self.model.encode([query])
        faiss.normalize_L2(query_vector)
        
        # 검색
        scores, indices = self.index.search(query_vector.astype('float32'), top_k)
        
        # 결과 반환
        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx != -1:
                results.append((self.metadata[idx], float(score)))
        
        return results
    
    def save_index(self, path: str = 'data/semantic_index_rag'):
        """인덱스 저장"""
        os.makedirs(path, exist_ok=True)
        
        faiss.write_index(self.index, f'{path}/faiss.index')
        
        with open(f'{path}/metadata.pkl', 'wb') as f:
            pickle.dump(self.metadata, f)
        
        print(f"💾 RAG 인덱스 저장 완료: {path}")
    
    def load_index(self, path: str = 'data/semantic_index_rag'):
        """저장된 인덱스 로드"""
        self.index = faiss.read_index(f'{path}/faiss.index')
        
        with open(f'{path}/metadata.pkl', 'rb') as f:
            self.metadata = pickle.load(f)
        
        self.documents = self.metadata
        print(f"📂 RAG 인덱스 로드 완료: {len(self.metadata)}개 문서")


def build_rag_index():
    """RAG 인덱스 구축"""
    engine = SemanticSearchEngineRAG()
    
    # docs 폴더의 모든 MD 파일 로딩
    all_docs = engine.load_all_markdown_files('docs')
    
    # 인덱스 구축
    engine.build_index(all_docs)
    
    # 저장
    engine.save_index()
    
    print(f"\n🎉 RAG 인덱스 구축 완료!")
    print(f"📊 총 {len(all_docs)}개 문서 인덱싱")
    
    return engine


# 하위 호환성을 위한 alias
def build_semantic_search_index():
    """시맨틱 검색 인덱스 구축 (RAG 버전)"""
    return build_rag_index()


if __name__ == "__main__":
    print("="*60)
    print("  RAG 기반 시맨틱 검색 엔진 구축")
    print("="*60)
    print()
    
    engine = build_rag_index()
    
    # 테스트 검색
    print("\n" + "="*60)
    print("  테스트 검색")
    print("="*60)
    
    test_queries = [
        "하계휴가는 언제까지?",
        "VDI 오류 해결 방법",
        "Mac PC 이름 변경",
        "프린터 IP 주소"
    ]
    
    for query in test_queries:
        print(f"\n🔍 질문: {query}")
        results = engine.search(query, top_k=3)
        
        for i, (doc, score) in enumerate(results, 1):
            print(f"  {i}. [{score:.3f}] {doc['title']}")
            print(f"      레벨: {doc['level']}, 부모: {doc['parent']}")

