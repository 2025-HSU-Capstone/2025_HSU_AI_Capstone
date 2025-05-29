# --- rag_index_builder.py ---

import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import os
from tqdm import tqdm

# ✅ 데이터 불러오기
DATA_PATH = "data/recipes1_rag_ready.csv"
DB_PATH = "db/chroma"

print("📦 데이터 로딩 중...")
df = pd.read_csv(DATA_PATH)
df["document"] = df["document"].astype(str)

# ✅ 임베딩 함수 정의
model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
model = SentenceTransformer(model_name)
embed_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)

# ✅ Chroma DB 생성
client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_or_create_collection("recipes", embedding_function=embed_func)

# ✅ 이미 존재하는 경우 중복 방지
if collection.count() == 0:
    print("🔨 벡터 임베딩 진행 중...")
    docs = df["document"].tolist()
    ids = [f"doc_{i}" for i in range(len(docs))]

    # 진행률 출력
    batch_size = 1000
    for i in tqdm(range(0, len(docs), batch_size), desc="📊 진행률"):
        batch_docs = docs[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        collection.add(documents=batch_docs, ids=batch_ids)

    print("✅ 벡터 DB 생성 완료!")
else:
    print("✅ 기존 벡터 DB가 존재합니다. 건너뜁니다.")
