# --- user_request.py ---

import os
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

# ✅ 환경설정
load_dotenv(dotenv_path=".env", override=True)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ 데이터 로딩
food_df = pd.read_csv("data/fooddataset.csv")
food_df.columns = food_df.columns.str.strip().str.replace(" ", "")

# ✅ 사용자 요청 입력 (외부에서 받는 방식으로 교체해도 됨)
user_request = "오늘은 단백질이 포함된 음식을 먹어야겠어."

# ✅ 조건 추출 프롬프트
prompt = f"""
다음 문장을 분석하여 식재료를 고르는 데 필요한 조건들을 추출해줘.
만약 문장에 구체적인 식재료 명칭(예: 파, 사과 등)이 포함되어 있다면, 다른 조건은 무시하고 반드시 그 식재료 명칭만 추출해줘.
만약 식재료 명칭이 없다면, '식재료 종류'나 '주요 영양소' 조건을 추출해줘.
혹시 DB에 조건에 맞는 식재료가 없을 때는 너가 스스로 보고 판단해서 괜찮은 음식이 나올만한것으로 하나 추천해줘.

문장: {user_request}

결과는 리스트 형식으로, 각 조건을 쉼표로 구분해서 응답해줘.
예: 파   또는   단백질, 채소
"""

# ✅ GPT 키워드 추출
response = client.chat.completions.create(model="gpt-4.1",
messages=[
    {"role": "system", "content": "당신은 음식 조건 분석 전문가입니다."},
    {"role": "user", "content": prompt}
])

raw_keywords = response.choices[0].message.content.strip()
keywords = [kw.strip() for kw in raw_keywords.split(",") if kw.strip()]

# ✅ 식재료 필터링
food_names = set(food_df["식재료"].str.strip().unique())
is_food_request = any(kw in food_names for kw in keywords)

if is_food_request:
    filtered_df = food_df[food_df["식재료"].apply(lambda x: x.strip() in keywords)]
else:
    filtered_df = food_df[food_df.apply(
        lambda row: any(kw in str(row["종류"]) or kw in str(row["주요영양소"]) for kw in keywords),
        axis=1
    )]

# ✅ 결과 저장
if not filtered_df.empty:
    input_ingredients = filtered_df["식재료"].tolist()
    print(f"\n✅ 요청 조건에 맞는 식재료: {', '.join(input_ingredients)}")

    # 👉 이후 모듈(recipe_generator_rag.py 등)에서 불러쓸 수 있도록 저장
    pd.DataFrame({"식재료": input_ingredients}).to_csv("data/filtered_ingredients.csv", index=False)
else:
    print("\n⚠️ 해당 조건에 맞는 식재료가 없습니다.")
    pd.DataFrame({"식재료": []}).to_csv("data/filtered_ingredients.csv", index=False)
