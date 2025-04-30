# --- recipe_generator_rag.py ---

import os
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions

# ✅ 환경설정
load_dotenv(dotenv_path=".env", override=True)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ 데이터 로딩
filtered_df = pd.read_csv("data/filtered_ingredients.csv")
ingredients = filtered_df["식재료"].tolist()

# ✅ Chroma DB 로드
model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
embed_func = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)
chroma_client = chromadb.PersistentClient(path="db/chroma")
collection = chroma_client.get_or_create_collection("recipes", embedding_function=embed_func)

# ✅ 유사 레시피 검색
def retrieve_similar_recipes(query_ingredients, top_k=3):
    query = ", ".join(query_ingredients)
    results = collection.query(query_texts=[query], n_results=top_k)
    return "\n\n".join(results["documents"][0])

# ✅ GPT로 레시피 생성
def get_recipe(ingredients):
    context = retrieve_similar_recipes(ingredients, top_k=3)

    # 길이 제한 조절용 (너무 긴 context 방지)
    if len(context) > 1500:
        context = context[:1500] + "..."

    prompt = f"""
    [상황]
    사용자 요청에 따라 아래 재료들을 사용하여 요리를 추천해야 합니다:
    - {', '.join(ingredients)}

    아래는 참고할 수 있는 유사 레시피입니다:
    {context}

    위 재료들과 유사 레시피를 참고하여 현실적이고 맛있는 요리를 제안해주세요.
    반드시 모든 재료를 하나의 요리에 억지로 넣지 않아도 됩니다. 
    상황에 따라 두 가지 이상의 요리를 제안해주셔도 좋습니다.

    각 요리에는 [재료], [조리법]을 한국어로 포함해주세요.
    """

    response = client.chat.completions.create(
        model="gpt-4.1",  # 최신 모델: GPT-4o
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1200,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

# ✅ 실행
if ingredients:
    print(f"📥 입력된 식재료: {', '.join(ingredients)}")
    print("\n✅ 추천 레시피:")
    print(get_recipe(ingredients))
else:
    print("⚠️ 재료가 비어 있어 레시피 추천을 수행할 수 없습니다.")

