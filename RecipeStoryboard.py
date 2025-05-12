import os
import re
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions

# ✅ 환경 설정: API 키 불러오기 (.env 파일에서)
load_dotenv(dotenv_path="/Users/heohyeonjun/Desktop/AI_Capstone/2025_HSU_AI_Capstone/.env", override=True)
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
client = OpenAI(api_key=openai_api_key)

# ✅ 사용자 자연어 요청
user_request = "오늘은 탄수화물이 풍부한 음식이 먹고싶어."

# ✅ 전체 식재료 데이터 로드 및 전처리
food_df = pd.read_csv("/Users/heohyeonjun/Desktop/AI_Capstone/2025_HSU_AI_Capstone/data/fooddataset.csv")
food_df.columns = food_df.columns.str.strip().str.replace(" ", "")  # 컬럼명 정제

# ✅ GPT 프롬프트 구성: 식재료명 또는 조건 추출
prompt = f"""
다음 문장을 분석하여 식재료를 고르는 데 필요한 조건들을 추출해줘.
만약 문장에 구체적인 식재료 명칭(예: 파, 사과 등)이 포함되어 있다면, 다른 조건은 무시하고 반드시 그 식재료 명칭만 추출해줘.
만약 식재료 명칭이 없다면, '식재료 종류'나 '주요 영양소' 조건을 추출해줘.
문장: {user_request}
결과는 리스트 형식으로, 각 조건을 쉼표로 구분해서 응답해줘.
"""

# ✅ GPT를 통해 조건 추출
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "당신은 음식 조건 분석 전문가입니다."},
        {"role": "user", "content": prompt}
    ]
)
raw_keywords = response.choices[0].message.content.strip()
keywords = [kw.strip() for kw in raw_keywords.split(",") if kw.strip()]  # 쉼표로 분리된 키워드

# ✅ 조건에 맞는 식재료 필터링 (직접 언급된 식재료 vs 조건 기반)
food_names = set(food_df["식재료"].str.strip().unique())
if any(kw in food_names for kw in keywords):
    # 직접 식재료 이름이 언급된 경우
    filtered_df = food_df[food_df["식재료"].apply(lambda x: x.strip() in keywords)]
else:
    # 식재료가 직접 언급되지 않은 경우 → 종류 or 영양소 기준
    filtered_df = food_df[food_df.apply(
        lambda row: any(kw in str(row["종류"]) or kw in str(row["주요영양소"]) for kw in keywords),
        axis=1
    )]

# ✅ 필터링 결과가 없으면 종료
if filtered_df.empty:
    print("\n⚠️ 조건에 맞는 식재료가 없습니다.")
    exit()

# ✅ 필터링된 결과를 CSV로 저장
filtered_path = "data/filtered_ingredients.csv"
filtered_df.to_csv(filtered_path, index=False, encoding="utf-8-sig")

# ✅ 저장된 CSV에서 다시 식재료 리스트 추출
ingredients_df = pd.read_csv(filtered_path)
ingredients = ingredients_df["식재료"].tolist()
print(f"\n✅ 요청 조건에 맞는 식재료: {', '.join(ingredients)}")

# ✅ Chroma DB를 사용한 유사 레시피 검색 (RAG)
embed_func = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
chroma_client = chromadb.PersistentClient(path="db/chroma")
collection = chroma_client.get_or_create_collection(name="recipes", embedding_function=embed_func)

# ✅ 유사 레시피 검색 결과 가져오기
context = collection.query(query_texts=[", ".join(ingredients)], n_results=3)["documents"][0]
context = "\n\n".join(context)

# ✅ GPT에 레시피 생성 요청
recipe_prompt = f"""
[상황]
사용자 요청에 따라 아래 재료들 중 일부를 활용하여 현실적인 요리 하나를 추천해주세요.

[사용자 요청]
{user_request}

[입력된 식재료]
{', '.join(ingredients)}

[참고 가능한 유사 레시피]
{context}

요구사항에 맞고, 현실적으로 만들 수 있는 맛있는 요리를 하나 추천해주세요.

- 반드시 모든 재료를 사용할 필요는 없습니다.
- 유사 레시피를 참고하되 그대로 복사하지 말고, 조합하거나 응용해도 좋습니다.
- 출력은 다음 포맷을 따라주세요:

[요리 제안: OO]
[재료]
- 항목1
- 항목2
...

[조리법]
1. ...
2. ...
3. ...
"""

res = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": recipe_prompt.strip()}],
    max_tokens=1200,
    temperature=0.7
)
recipe_text = res.choices[0].message.content.strip()
print("\n✅ 생성된 레시피:\n", recipe_text)

# ✅ 조리법 파싱 (정규표현식으로 [조리법] 구간만 추출)
matches = re.findall(r"\[요리 제안: ([^\]]+)]\s*.*?\[조리법](.+)", recipe_text, re.DOTALL)
recipes = []
for name, steps_raw in matches:
    steps = re.findall(r"\d+[.]\s*(.+)", steps_raw.strip())
    recipes.append({"title": name.strip(), "steps": steps})

# ✅ 이미지 생성 및 HTML로 출력
os.makedirs("outputs", exist_ok=True)
html = ["<html><head><meta charset='utf-8'><title>추천 레시피</title></head><body>",
        "<h1>🍽️ AI 추천 레시피</h1><hr/>"]

for recipe in recipes:
    html.append(f"<h2>{recipe['title']}</h2>")
    for idx, step in enumerate(recipe["steps"], 1):
        html.append(f"<p><b>{idx}. {step}</b></p>")

        # ✅ 조리 단계 시각화를 위한 이미지 프롬프트 생성
        image_prompt = f"""
        당신은 요리 일러스트를 그리는 전문가입니다.
        아래 조리 과정을 만화 스타일로 그려주세요:

        '{step}'

        - 주방 배경, 조리도구, 식재료 표현
        - 인물은 생략, 손만 등장
        - 따뜻한 톤 사용
        """
        try:
            image_res = client.images.generate(
                model="gpt-image-1",
                prompt=image_prompt.strip(),
                size="1024x1024",
                n=1
            )
            image_data = f"data:image/png;base64,{image_res.data[0].b64_json}"
            html.append(f"<img src='{image_data}' style='max-width:500px; margin-bottom:20px;'/><br/><br/>")
        except Exception as e:
            html.append(f"<p>❌ 이미지 생성 실패: {e}</p>")

    html.append("<hr/>")

html.append("</body></html>")
with open("outputs/combined_recipe.html", "w", encoding="utf-8") as f:
    f.write("\n".join(html))

print("\n📄 HTML 저장 완료: outputs/combined_recipe.html")