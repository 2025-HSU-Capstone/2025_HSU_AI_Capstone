import sys, os
import re
import json
import base64
import io
import pandas as pd
from PIL import Image
from openai import OpenAI
import chromadb
from chromadb.utils import embedding_functions
from services.cloudinary_uploader import upload_to_cloudinary_from_bytes
import time
import openai
from dotenv import load_dotenv

# ✅ .env 파일 로드
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv()

print("✅ CLOUDINARY 환경변수 확인")
print("CLOUDINARY_CLOUD_NAME:", os.getenv("CLOUDINARY_CLOUD_NAME"))
print("CLOUDINARY_API_KEY:", os.getenv("CLOUDINARY_API_KEY"))
print("CLOUDINARY_API_SECRET:", os.getenv("CLOUDINARY_API_SECRET"))

# ✅ 환경 변수에서 API 키 읽기
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_recipe_from_request(user_input: dict):
    user_request = user_input.get("user_input", "")
    detected_ingredients = user_input.get("ingredients", [])

    # ✅ 식재료 데이터 로드
    food_df = pd.read_csv("data/fooddataset.csv")
    food_df.columns = food_df.columns.str.strip().str.replace(" ", "")

    # ✅ 조건 추출 프롬프트
    prompt = f"""
사용자의 음식 요청을 구조화된 JSON으로 바꿔주세요.

단, 아래 fooddataset.csv에서 사용되는 컬럼 값을 기준으로 정확하게 조건을 표현해주세요 (이름 일치 필수):
- 종류 컬럼 값: 육류, 채소, 과일, 해산물, 유제품, 곡류, 생선, 콩류, 나물, 조미료, 통조림
- 주요영양소 컬럼 값: 단백질, 지방, 탄수화물

예: '과일류' → '과일', '해산물 종류' → '해산물'

출력 형식:
{{
  "요리종류": "...",
  "포함조건": ["..."],
  "제외조건": ["..."],
  "기타": ["..."],
  "명시된재료": ["..."]
}}

사용자 요청:
"{user_request}"
"""
    print("🧠 GPT 호출: 조건 추출 시작")
    response = None
    for i in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "당신은 음식 데이터셋 조건 추출 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            break
        except openai.RateLimitError:
            print(f"⚠️ 요청 제한: 재시도 {i + 1}/3")
            time.sleep(2)
        except Exception as e:
            print("❌ 기타 에러 발생:", e)
            break

    if response is None:
        return {"error": "GPT 응답 없음"}

    raw_json = response.choices[0].message.content.strip()
    if raw_json.startswith("```json"):
        raw_json = "\n".join(raw_json.strip().split("\n")[1:-1])
    conditions = json.loads(raw_json)

    types = conditions.get("types", [])
    nutrients = conditions.get("nutrients", [])
    ingredients_list = detected_ingredients

    # ✅ Chroma DB 로드
    CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), "db", "chroma")
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    try:
        collection = chroma_client.get_collection(name="recipes")
    except chromadb.errors.NotFoundError:
        print("❌ 'recipes' 컬렉션이 존재하지 않습니다.")
        return {"error": "'recipes' 컬렉션이 DB에 없습니다. 먼저 rag_index_builder.py를 실행하세요."}

    # ✅ RAG 검색
    query_text = ", ".join(ingredients_list + types + nutrients)
    rag_results = collection.query(query_texts=[query_text], n_results=3)
    rag_docs = rag_results.get("documents", [[]])[0]
    context = "\n\n".join(rag_docs)

    # ✅ 레시피 생성 프롬프트
    recipe_prompt = f"""
🍽️ [사용자 요청 요약]
- 요청 문장: {user_request}
- 요리 종류: {conditions.get('요리종류', '무관')}
- 포함 조건: {', '.join(conditions.get('포함조건', [])) or '없음'}
- 제외 조건: {', '.join(conditions.get('제외조건', [])) or '없음'}
- 기타 조건: {', '.join(conditions.get('기타', [])) or '없음'}

🥦 [사용 가능한 식재료]
{', '.join(ingredients_list)}

📚 [AI가 검색한 유사 레시피 목록]
{context}

🧑‍🍳 [요리 생성 지침]
- 반드시 '요청 요약'의 조건을 최우선으로 반영해주세요.
- 모든 재료를 쓸 필요는 없습니다.
- 유사 레시피는 참고용입니다.
- 대중적인 조리법을 우선 추천해주세요.
- 실제 조리 상식에 어긋나지 않는 조리 방법으로 요리를 구성해주세요.
- 현실적인 단 하나의 요리를 추천해주세요.
- 조리법 단계는 간결하고 구체적으로 구성해주세요.

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
    print("🍳 GPT 호출: 레시피 생성 시작")
    res = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": recipe_prompt.strip()}],
        max_tokens=1200,
        temperature=0.7
    )

    recipe_text = res.choices[0].message.content.strip()
    matches = re.findall(r"\[요리 제안: ([^\]]+)]\s*.*?\[조리법](.+)", recipe_text, re.DOTALL)
    name, steps_raw = matches[0]
    steps = re.findall(r"\d+[.]\s*(.+)", steps_raw.strip())

    step_outputs = []
    for idx, step in enumerate(steps[:2], 1):
        image_prompt = f"""
당신은 요리 일러스트를 그리는 전문가입니다.
아래 조리 과정을 만화 스타일로 그려주세요:

'{step}'

- 주방 배경, 조리도구, 식재료 표현
- 인물은 생략, 손만 등장
- 현실적인 사진 느낌의 그림
"""
        try:
            print(f"🖼️ 이미지 생성 요청: step {idx}")
            image_res = client.images.generate(
                model="gpt-image-1",
                prompt=image_prompt.strip(),
                size="1024x1024",
                n=1
            )
            image_data = base64.b64decode(image_res.data[0].b64_json)
            image = Image.open(io.BytesIO(image_data))

            title_translation = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "한글 요리 제목을 간단한 영문 파일명으로 번역하고 공백은 언더바로 바꿔줘."
                    },
                    {
                        "role": "user",
                        "content": name
                    }
                ],
                temperature=0
            )
            safe_title = title_translation.choices[0].message.content.strip()
            safe_title = re.sub(r"\s+", "_", safe_title)
            safe_title = re.sub(r"[^a-zA-Z0-9_]", "", safe_title)

            public_id = f"smartfridge/recipe_images/{safe_title}_step{idx}"
            print(f"☁️ Cloudinary 업로드 대상 ID: {public_id}")

            try:
                cloudinary_url = upload_to_cloudinary_from_bytes(image, public_id)
                print(f"✅ Cloudinary 업로드 성공: {cloudinary_url}")
            except Exception as e:
                print("❌ Cloudinary 업로드 실패:", e)
                cloudinary_url = f"❌ 업로드 실패: {e}"

            step_outputs.append({
                "step": idx,
                "text": step,
                "image_url": cloudinary_url
            })

        except Exception as e:
            step_outputs.append({
                "text": step,
                "image_url": f"❌ 이미지 생성 실패: {e}"
            })

    return {
        "title": name,
        "ingredients": ingredients_list,
        "steps": step_outputs
    }
