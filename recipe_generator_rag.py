import os
import pandas as pd
import re
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

# ✅ HTML + base64 이미지 저장
def generate_images_html(recipe_text, output_html="recipe_storyboard.html"):
    steps = re.findall(r"[0-9]+\.\s*(.+)", recipe_text)
    steps = [s.strip() for s in steps if len(s.strip()) > 5]

    # print(f"\n🔥 추출된 스텝 수: {len(steps)}")
    # print("📋 추출된 스텝 내용:", steps)

    html_lines = [
        "<html><head><meta charset='utf-8'><title>요리 스토리보드</title></head><body>",
        "<h2>🍳 조리법 스토리보드</h2>"
    ]

    # ✅ 전체 스텝에 대해 이미지 생성
    for idx, step in enumerate(steps, 1):
        prompt = f"""
        아래는 요리 레시피를 장면별로 표현한 스토리보드입니다.
        이 그림은 모두 **동일한 작가**가 **같은 스타일**로 그린 연속된 장면이어야 합니다.

        - 지금은 Step {idx}입니다.
        - 동작: {step}
        - 스타일: 따뜻하고 간단한 만화 스타일
        - 동일한 주방 배경, 동일한 조리도구, 동일한 손 모양과 색상 사용
        - 인물 없이 손 중심, **한 가지 동작만 표현**
        - 전 스텝들과 연결된 느낌을 주는 **연속 장면 구성** (스토리보드 느낌)
        - 그림체 일관성 유지 필수 (캐릭터/손/재료/기구 스타일 동일)
        - 너무 복잡하지 않게, 요리 중인 장면만 한 컷으로 명확히

        전체 조리법은 각 스텝마다 한 장면으로 표현되며, 이 Step {idx}도 그 시리즈 중 하나입니다.
        """

        try:
            response = client.images.generate(
                model="gpt-image-1",
                prompt=prompt.strip(),
                size="1024x1024",
                n=1,
            )
            b64_image = response.data[0].b64_json
        except Exception as e:
            print(f"⚠️ Step {idx} 이미지 생성 실패: {type(e).__name__} - {e}")
            b64_image = None

        html_lines.append(f"<h4>Step {idx}: {step}</h4>")
        if b64_image:
            html_lines.append(
                f"<img src='data:image/png;base64,{b64_image}' width='512' style='margin-bottom:20px;'>"
            )
        else:
            html_lines.append("<p><i>이미지 생성 실패</i></p>")

    html_lines.append("</body></html>")

    with open(output_html, "w", encoding="utf-8") as f:
        f.write("\n".join(html_lines))

    print(f"📄 HTML 스토리보드 저장 완료 → {output_html}")


# ✅ GPT로 레시피 생성
def get_recipe(ingredients):
    context = retrieve_similar_recipes(ingredients, top_k=3)
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
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1200,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

# ✅ 실행
if ingredients:
    print(f"📥 입력된 식재료: {', '.join(ingredients)}")
    print("\n✅ 추천 레시피:")
    recipe = get_recipe(ingredients)
    print(recipe)

    print("\n🖼️ 스토리보드 생성 중...")
    generate_images_html(recipe)
else:
    print("⚠️ 재료가 비어 있어 레시피 추천을 수행할 수 없습니다.")
