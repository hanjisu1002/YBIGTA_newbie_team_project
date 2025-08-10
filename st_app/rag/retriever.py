# st_app/rag/retriever.py
import os
import json
from typing import List, Dict, Any

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI  # pip install openai==1.52.2
from .embedder import get_upstage_client


BASE_DIR    = "st_app/db/faiss_index"
INDEX_PATH  = os.path.join(BASE_DIR, "index.faiss")
META_PATH   = os.path.join(BASE_DIR, "meta.json")
EMBED_MODEL = "embedding-query"               


load_dotenv()

def _embed_query(client: OpenAI, text: str) -> np.ndarray:
    """쿼리 임베딩 생성 + L2 정규화"""
    if not text or not text.strip():
        raise ValueError("쿼리 텍스트가 비어있습니다.")
    
    try:
        resp = client.embeddings.create(input=text, model=EMBED_MODEL)
        vec = np.asarray(resp.data[0].embedding, dtype="float32")
        
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        
        return vec.reshape(1, -1)  # (1, D)
    except Exception as e:
        err_type = e.__class__.__name__
        raise RuntimeError(f"임베딩 생성 실패: {err_type}: {e}")

class SimpleFaissRetriever:
    """
    embedder.py 산출물(index.faiss + meta.json)에 정합된 리트리버.
    - 인덱스: IndexFlatIP (코사인 동등)
    - 벡터: 사전 정규화 저장 → 쿼리도 정규화 후 IP 검색
    - 메타 필드: {source,id,review,rate,date,weekday} (embedder.py와 완벽 일치)
    """
    def __init__(self, k: int = 3):
        # 파일 존재 여부 확인
        if not os.path.exists(INDEX_PATH):
            raise FileNotFoundError(f"FAISS 인덱스 파일을 찾을 수 없습니다: {INDEX_PATH}")
        if not os.path.exists(META_PATH):
            raise FileNotFoundError(f"메타데이터 파일을 찾을 수 없습니다: {META_PATH}")
        
        try:
            # FAISS 인덱스 로딩
            self.index = faiss.read_index(INDEX_PATH)
            
            # 메타데이터 로딩
            with open(META_PATH, "r", encoding="utf-8") as f:
                self.meta = json.load(f)
                
        except Exception as e:
            raise RuntimeError(f"파일 로딩 실패: {str(e)}")
        
        # 데이터 유효성 검사
        if self.index.ntotal == 0:
            raise ValueError("FAISS 인덱스가 비어있습니다.")
        if len(self.meta) == 0:
            raise ValueError("메타데이터가 비어있습니다.")
        
        # 메타-인덱스 길이 불일치 경고
        if self.index.ntotal != len(self.meta):
            print(f"경고: FAISS 인덱스({self.index.ntotal})와 메타데이터({len(self.meta)}) 길이 불일치")
        
        # k 값 검증 및 조정
        self.k = min(k, self.index.ntotal, len(self.meta))  # k가 전체 데이터보다 클 수 없음
        
        # Upstage 클라이언트 초기화 (embedder.py의 함수 사용)
        try:
            self.client = get_upstage_client()
        except Exception as e:
            raise RuntimeError(f"Upstage 클라이언트 초기화 실패: {str(e)}")

    def search(self, query: str) -> Dict[str, Any]:
        """쿼리 검색 및 결과 반환"""
        if not query or not query.strip():
            return {"query": query, "results": [], "error": "쿼리가 비어있습니다."}
        
        try:
            # 쿼리 임베딩 생성
            q = _embed_query(self.client, query)   # (1, D), 정규화 완료
            
            # FAISS 검색 수행
            D, I = self.index.search(q, self.k)    # IP 점수(=코사인)
            
            hits = []
            for idx, score in zip(I[0], D[0]):
                if idx == -1 or idx >= len(self.meta):
                    continue
                    
                rec = self.meta[idx]
                hits.append({
                    "review":   rec.get("review", ""),
                    "rate":     rec.get("rate", None),
                    "date":     rec.get("date", ""),
                    "weekday":  rec.get("weekday", ""),
                    "source":   rec.get("source", ""),
                    "id":       rec.get("id", None),
                    "score":    float(score),
                })
            
            return {"query": query, "results": hits}
            
        except Exception as e:
            return {"query": query, "results": [], "error": f"검색 실패: {str(e)}"}

    def get_relevant_texts(self, query: str) -> List[str]:
        """RAG 프롬프트 컨텍스트용 간단 라인 포맷"""
        results = self.search(query)
        
        if "error" in results:
            return []  # 에러 시 빈 리스트 반환 
        
        lines: List[str] = []
        for r in results["results"]:
            # 평점 표시 (숫자일 때만)
            rate = r.get("rate")
            try:
                if isinstance(rate, (int, float)) and rate is not None and not np.isnan(float(rate)):
                    star = f"★{rate:.1f}"
                else:
                    star = "★-"
            except (ValueError, TypeError):
                star = "★-"
            
            # 날짜 표시
            date = r.get("date") or "-"
            
            # 리뷰 텍스트
            txt = (r.get("review") or "").strip()
            if txt:
                # 소스 정보도 포함
                source = r.get("source", "").upper()
                lines.append(f"[{star} | {date} | {source}] {txt}")
        
        return lines if lines else ["관련 리뷰를 찾을 수 없습니다."]

    def get_reviews_by_source(self, source: str, limit: int = 5) -> List[Dict[str, Any]]:
        """특정 소스의 리뷰만 반환"""
        source_reviews = [r for r in self.meta if r.get("source") == source]
        return source_reviews[:limit]

    def get_reviews_by_rating(self, min_rating: float, max_rating: float = 5.0) -> List[Dict[str, Any]]:
        """특정 평점 범위의 리뷰만 반환"""
        filtered_reviews = []
        for r in self.meta:
            rate = r.get("rate")
            if isinstance(rate, (int, float)) and rate is not None and min_rating <= rate <= max_rating:
                filtered_reviews.append(r)
        return filtered_reviews

    def get_statistics(self) -> Dict[str, Any]:
        """데이터베이스 통계 정보 반환"""
        stats = {
            "total_reviews": len(self.meta),
            "total_vectors": self.index.ntotal,
            "vector_dimension": self.index.d,
            "sources": {},
            "rating_distribution": {}
        }
        
        # 소스별 통계
        for r in self.meta:
            source = r.get("source", "unknown")
            stats["sources"][source] = stats["sources"].get(source, 0) + 1
            
            # 평점 분포
            rate = r.get("rate")
            try:
                if isinstance(rate, (int, float)) and rate is not None and not np.isnan(float(rate)):
                    rate_key = f"{int(rate)}"
                    stats["rating_distribution"][rate_key] = stats["rating_distribution"].get(rate_key, 0) + 1
            except (ValueError, TypeError):
                continue
        
        return stats

def load_retriever(k: int = 3) -> SimpleFaissRetriever:
    """리트리버 인스턴스 생성 및 반환"""
    try:
        return SimpleFaissRetriever(k=k)
    except Exception as e:
        raise RuntimeError(f"리트리버 로딩 실패: {str(e)}")

# 테스트용 함수
def test_retriever():
    """리트리버 테스트 함수"""
    try:
        retriever = load_retriever(k=3)
        print("리트리버 로딩 성공")
        
        # 통계 정보 출력
        stats = retriever.get_statistics()
        print(f"데이터베이스 통계:")
        print(f"   - 총 리뷰: {stats['total_reviews']}")
        print(f"   - 총 벡터: {stats['total_vectors']}")
        print(f"   - 벡터 차원: {stats['vector_dimension']}")
        print(f"   - 소스별: {stats['sources']}")
        
        # 간단한 검색 테스트
        test_query = "코카콜라 맛"
        results = retriever.search(test_query)
        print(f"\n 테스트 검색: '{test_query}'")
        print(f"   - 결과 수: {len(results.get('results', []))}")
        
        return True
        
    except Exception as e:
        print(f"리트리버 테스트 실패: {str(e)}")
        return False

if __name__ == "__main__":
    test_retriever()
