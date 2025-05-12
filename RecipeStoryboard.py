import os
import re
import json
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
user_request = "오늘은 지방이 적은 음식이 먹고싶어."

# ✅ 전체 식재료 데이터 로드 및 전처리
food_df = pd.read_csv("/Users/heohyeonjun/Desktop/AI_Capstone/2025_HSU_AI_Capstone/data/fooddataset.csv")
food_df.columns = food_df.columns.str.strip().str.replace(" ", "")  # 컬럼명 정제

# ✅ GPT 프롬프트 구성: 조건 추출 (JSON 형식)
prompt = f"""
사용자의 음식 요청을 구조화된 JSON으로 바꿔주세요.

단, 아래 fooddataset.csv에서 사용되는 컬럼 값을 기준으로 정확하게 조건을 표현해주세요 (이름 일치 필수):
- 종류 컬럼 값: 육류, 채소, 과일, 해산물, 유제품, 곡류, 생선, 콩류, 나물, 조미료, 통조림
- 주요영양소 컬럼 값: 단백질, 지방, 탄수화물

예: '과일류' → '과일', '해산물 종류' → '해산물'

출력 형식:
{{
  "요리종류": "...",
  "포함조건": ["..."],  ← 위 컬럼 값 중 정확히 일치하게만 작성
  "제외조건": ["..."],
  "기타": ["..."],
  "명시된재료": ["..."]
}}

사용자 요청:
"{user_request}"
"""

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "당신은 음식 데이터셋 조건 추출 전문가입니다."},
        {"role": "user", "content": prompt}
    ],
    temperature=0
)

raw_json = response.choices[0].message.content.strip()
if raw_json.startswith("```json"):
    raw_json = "\n".join(raw_json.strip().split("\n")[1:-1])

try:
    conditions = json.loads(raw_json)
except Exception as e:
    print(f"❌ JSON 파싱 실패, 원본 응답:\n{raw_json}\n오류: {e}")
    raise e

ingredients = conditions.get("ingredients", [])
types = conditions.get("types", [])
nutrients = conditions.get("nutrients", [])

# ✅ 조건에 맞는 식재료 필터링
filtered_df = pd.DataFrame()
food_names = set(food_df["식재료"].str.strip().unique())

if ingredients:
    # 명시적 식재료가 있으면 그것만 필터링
    valid_ingredients = [ing for ing in ingredients if ing in food_names]
    if valid_ingredients:
        filtered_df = food_df[food_df["식재료"].apply(lambda x: x.strip() in valid_ingredients)]
else:
    # 식재료 명시 없으면 종류, 주요영양소 조건으로 필터링
    def row_match(row):
        type_match = any(t in str(row["종류"]) for t in types) if types else True
        nutrient_match = any(n in str(row["주요영양소"]) for n in nutrients) if nutrients else True
        return type_match and nutrient_match

    filtered_df = food_df[food_df.apply(row_match, axis=1)]

# fallback: 조건에 맞는 식재료가 없으면 기존 CSV 있으면 불러오고 없으면 전체 데이터에서 랜덤 3개 추출
filtered_path = "/Users/heohyeonjun/Desktop/AI_Capstone/2025_HSU_AI_Capstone/data/filtered_ingredients.csv"
if filtered_df.empty:
    if os.path.exists(filtered_path):
        print("📁 기존 필터링된 식재료를 불러옵니다.")
        filtered_df = pd.read_csv(filtered_path)
    else:
        print("⚠️ 조건에 맞는 식재료가 없습니다. 전체 데이터에서 임의로 선택합니다.")
        filtered_df = food_df.sample(3, random_state=42)

ingredients_list = filtered_df["식재료"].dropna().unique().tolist()
print(f"\n✅ 요청 조건에 맞는 식재료: {', '.join(ingredients_list)}")

# ✅ Chroma DB를 사용한 유사 레시피 검색 (RAG)
embed_func = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
chroma_client = chromadb.PersistentClient(path="/Users/heohyeonjun/Desktop/AI_Capstone/2025_HSU_AI_Capstone/db/chroma")
try:
    collection = chroma_client.get_collection(name="recipes")
except:
    raise RuntimeError("❌ 'recipes' 컬렉션이 존재하지 않습니다. 기존 DB가 필요합니다.")

query_text = ", ".join(ingredients_list + types + nutrients)
rag_results = collection.query(query_texts=[query_text], n_results=3)
rag_docs = rag_results.get("documents", [[]])[0]
context = "\n\n".join(rag_docs)

# ✅ GPT에 레시피 생성 요청
recipe_prompt = f"""
🍽️ [사용자 요청 요약]
- 요청 문장: {user_request}
- 요리 종류: {conditions.get('요리종류', '무관')}
- 포함 조건: {', '.join(conditions.get('포함조건', [])) or '없음'}
- 제외 조건: {', '.join(conditions.get('제외조건', [])) or '없음'}
- 기타 조건: {', '.join(conditions.get('기타', [])) or '없음'}

🥦 [사용 가능한 식재료]
{', '.join(ingredients)}

📚 [AI가 검색한 유사 레시피 목록]
아래는 다양한 요리 아이디어를 위한 참고용 레시피입니다.  
이 목록은 단지 힌트이며, 아래 내용 자체를 복사하거나 그대로 따라하지 마세요.  
**사용자 요청 조건에 가장 적합한 요리를 새롭게 구성해 주세요.**

{context}

🧑‍🍳 [요리 생성 지침]
- 반드시 '요청 요약'의 조건을 최우선으로 반영해주세요.
- 모든 재료를 쓸 필요는 없습니다.
- 유사 레시피는 창의적인 영감을 위한 참고용입니다. 복사하지 말고 새로운 조합을 만들어주세요.
- 대중적인 조리법을 이용해서 만들 수 있는 요리를 우선으로 추천해주세요.
- 실제 조리 상식에 어긋나지 않는 조리 방법으로 요리를 할 수 있도록 출력해주세요.
- 현실적으로 만들 수 있는 단 하나의 요리를 출력해주세요.

📄 출력 형식:
[요리 제안: OO]
[재료]
- 항목1
- 항목2
...

[조리법]
1. ...
2. ...
"""

res = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": recipe_prompt.strip()}],
    max_tokens=1200,
    temperature=0.7
)
recipe_text = res.choices[0].message.content.strip()
print("\n✅ 생성된 레시피:\n", recipe_text)

# ✅ 조리법 파싱 (정규표현식으로 [요리 제안]과 [조리법] 구간 추출)
matches = re.findall(r"\[요리 제안: ([^\]]+)]\s*.*?\[조리법](.+)", recipe_text, re.DOTALL)
recipes = []
for name, steps_raw in matches:
    steps = re.findall(r"\d+[.]\s*(.+)", steps_raw.strip())
    recipes.append({"title": name.strip(), "steps": steps})

# ✅ 이미지 생성 및 HTML로 출력
os.makedirs("outputs", exist_ok=True)
html = [
    "<html><head><meta charset='utf-8'><title>추천 레시피</title></head><body>",
    "<h1>🍽️ AI 추천 레시피</h1><hr/>"
]

for recipe in recipes:
    html.append(f"<h2>{recipe['title']}</h2>")
    for idx, step in enumerate(recipe["steps"][:2], 1):
        html.append(f"<p><b>{idx}. {step}</b></p>")

        # ✅ 조리 단계 시각화를 위한 이미지 프롬프트 생성
        image_prompt = f"""
당신은 요리 일러스트를 그리는 전문가입니다.
아래 조리 과정을 만화 스타일로 그려주세요:

'{step}'

- 주방 배경, 조리도구, 식재료 표현
- 인물은 생략, 손만 등장
- 조금 더 현실적인 느낌으로 사진과 같은 그림
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

# ✅ 토큰 사용량 출력 (선택 사항)
if hasattr(res, 'usage'):
    usage = res.usage
    print(f"\n💡 토큰 사용량 - 프롬프트: {usage.prompt_tokens}, 생성: {usage.completion_tokens}, 합계: {usage.total_tokens}")