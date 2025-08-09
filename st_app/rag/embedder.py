# st_app/rag/embedder.py
import os
import json
import pandas as pd
import numpy as np
import faiss
from tqdm import tqdm
from openai import OpenAI  # pip install openai==1.52.2
from dotenv import load_dotenv
load_dotenv()  # .env 파일의 환경변수를 불러옴

FAISS_DIR = "st_app/db/faiss_index"
FAISS_INDEX_PATH = f"{FAISS_DIR}/index.faiss"
META_PATH = f"{FAISS_DIR}/meta.json"

# -------- Upstage API --------
def get_upstage_client() -> OpenAI:
    api_key = os.getenv("UPSTAGE_API_KEY")
    if not api_key:
        raise ValueError("환경변수 UPSTAGE_API_KEY가 설정되어 있지 않습니다.")
    return OpenAI(api_key=api_key, base_url="https://api.upstage.ai/v1")

def get_embedding(client: OpenAI, text: str) -> list[float]:
    # Upstage 문서 기준 모델명 (요청대로)
    resp = client.embeddings.create(input=text, model="embedding-query")
    return resp.data[0].embedding

# -------- Data loading --------
def process_file(filepath: str, source_name: str):
    # CSV는 전처리되어 있다고 가정 (컬럼: review, rate, date, weekday)
    df = pd.read_csv(filepath, encoding="utf-8")
    # 텍스트 결측만 기본값 처리
    df["review"] = df["review"].fillna("")
    df["date"] = df["date"].fillna("")
    df["weekday"] = df["weekday"].fillna("")
    # 반환 튜플: (source, row_id, review, rate, date, weekday)
    return [
        (source_name, int(idx), row["review"], row["rate"], row["date"], row["weekday"])
        for idx, row in df.iterrows()
    ]

# -------- FAISS utils --------
def build_faiss_ip_index(dim: int) -> faiss.Index:
    # 코사인 유사도 = 내적 + 벡터 정규화 조합
    return faiss.IndexFlatIP(dim)

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

# -------- Main --------
def main():
    # 루트에서 실행한다고 가정
    files = [
        ("database/preprocessed_reviews_naver.csv", "naver"),
        ("database/preprocessed_reviews_emart.csv", "emart"),
        ("database/preprocessed_reviews_lotteon.csv", "lotteon"),
    ]

    client = get_upstage_client()

    # 모든 데이터 적재
    all_rows = []
    for fp, src in files:
        if not os.path.exists(fp):
            raise FileNotFoundError(f"입력 파일이 없습니다: {fp}")
        all_rows.extend(process_file(fp, src))

    # 임베딩 + 메타 만들기
    embeddings = []
    metadata = []

    # 먼저 첫 유효 리뷰로 차원 파악
    first_text = next((r[2] for r in all_rows if isinstance(r[2], str) and r[2].strip()), None)
    if not first_text:
        raise ValueError("임베딩할 리뷰 텍스트가 없습니다.")
    first_emb = get_embedding(client, first_text)
    dim = len(first_emb)

    index = build_faiss_ip_index(dim)

    for source, row_id, review, rate, date, weekday in tqdm(all_rows, desc="Embedding"):
        text = (review or "").strip()
        if not text:
            # 빈 리뷰는 스킵
            continue

        try:
            emb = get_embedding(client, text)
        except Exception as e:
            # 개별 실패는 스킵하고 계속
            print(f"[WARN] embedding 실패 (source={source}, id={row_id}): {e}")
            continue

        # numpy float32 + 정규화(코사인 유사도용)
        vec = np.asarray(emb, dtype="float32")
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        embeddings.append(vec)

        # NaN은 JSON 직렬화 불가 → None으로
        rate_val = None
        try:
            if pd.notna(rate):
                rate_val = float(rate)
        except Exception:
            rate_val = None

        metadata.append({
            "source": source,
            "id": row_id,
            "review": review,
            "rate": rate_val,
            "date": date,
            "weekday": weekday,
        })

    if not embeddings:
        raise ValueError("생성된 임베딩이 없습니다. 입력 데이터/전처리를 확인하세요.")

    mat = np.vstack(embeddings).astype("float32")
    index.add(mat)

    ensure_dir(FAISS_DIR)
    faiss.write_index(index, FAISS_INDEX_PATH)
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"✅ 생성 완료\n- {FAISS_INDEX_PATH}\n- {META_PATH}\n- 벡터 개수: {index.ntotal}, 차원: {dim}")

if __name__ == "__main__":
    main()
