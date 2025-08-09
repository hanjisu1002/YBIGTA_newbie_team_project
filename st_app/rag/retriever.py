# st_app/rag/retriever.py
import os
import json
from typing import List, Dict, Any

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI  # pip install openai==1.52.2

# ── 경로/설정 (embedder.py와 동일) ─────────────────────────────────
BASE_DIR    = "st_app/db/faiss_index"
INDEX_PATH  = os.path.join(BASE_DIR, "index.faiss")
META_PATH   = os.path.join(BASE_DIR, "meta.json")
EMBED_MODEL = "embedding-query"               # Upstage 임베딩 모델명
UPSTAGE_URL = "https://api.upstage.ai/v1"     # Upstage OpenAI-호환 엔드포인트
# ──────────────────────────────────────────────────────────────────

load_dotenv()

def _get_upstage_client() -> OpenAI:
    api_key = os.getenv("UPSTAGE_API_KEY")
    if not api_key:
        raise RuntimeError("UPSTAGE_API_KEY가 설정되어 있지 않습니다.")
    return OpenAI(api_key=api_key, base_url=UPSTAGE_URL)

def _embed_query(client: OpenAI, text: str) -> np.ndarray:
    """쿼리 임베딩 생성 + L2 정규화 (IndexFlatIP와 코사인 일치)"""
    resp = client.embeddings.create(model=EMBED_MODEL, input=text)
    vec = np.array(resp.data[0].embedding, dtype="float32").reshape(1, -1)
    faiss.normalize_L2(vec)
    return vec  # (1, D)

class SimpleFaissRetriever:
    """
    embedder.py 산출물(index.faiss + meta.json)에 정합된 수제 리트리버.
    - 인덱스: IndexFlatIP (코사인 동등)
    - 벡터: 사전 정규화 저장 → 쿼리도 정규화 후 IP 검색
    - 메타 필드: {source,id,review,rate,date,weekday}
    """
    def __init__(self, k: int = 3):
        if not (os.path.exists(INDEX_PATH) and os.path.exists(META_PATH)):
            raise FileNotFoundError(f"FAISS/Meta 경로 확인: {INDEX_PATH}, {META_PATH}")
        self.index  = faiss.read_index(INDEX_PATH)
        with open(META_PATH, "r", encoding="utf-8") as f:
            self.meta = json.load(f)
        self.k = k
        self.client = _get_upstage_client()

    def search(self, query: str) -> Dict[str, Any]:
        q = _embed_query(self.client, query)   # (1, D), 정규화 완료
        D, I = self.index.search(q, self.k)    # IP 점수(=코사인)
        hits = []
        for idx, score in zip(I[0], D[0]):
            if idx == -1:
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

    def get_relevant_texts(self, query: str) -> List[str]:
        """RAG 프롬프트 컨텍스트용 간단 라인 포맷"""
        results = self.search(query)["results"]
        lines: List[str] = []
        for r in results:
            star = f"★{r['rate']:.1f}" if isinstance(r.get("rate"), (int, float)) else "★-"
            date = r.get("date") or "-"
            txt  = (r.get("review") or "").strip()
            if txt:
                lines.append(f"[{star} | {date}] {txt}")
        return lines

def load_retriever(k: int = 3) -> SimpleFaissRetriever:
    return SimpleFaissRetriever(k=k)
