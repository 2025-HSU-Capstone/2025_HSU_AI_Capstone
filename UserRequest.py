import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import pandas as pd
import re
from dotenv import load_dotenv
from openai import OpenAI

# ✅ 환경설정
load_dotenv(dotenv_path="C:/Users/이현승/Desktop/2025_AI_Capstone/.env", override=True)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ CSV 데이터 로딩
food_df = pd.read_csv("C:/Users/이현승/Desktop/2025_AI_Capstone/fooddataset.csv")
food_df.columns = food_df.columns.str.strip().str.replace(" ", "")

# ✅ 사용자 요청
user_request = "오늘은 육류를 먹어야겠어."

# ✅ 조건 추출 프롬프트 구성
prompt = f"""
다음 문장을 분석하여 식재료를 고르는 데 필요한 조건들을 추출해줘.
만약 문장에 구체적인 식재료 명칭(예: 파, 사과 등)이 포함되어 있다면, 다른 조건은 무시하고 반드시 그 식재료 명칭만 추출해줘.
만약 식재료 명칭이 없다면, '식재료 종류'나 '주요 영양소' 조건을 추출해줘.
혹시 DB에 조건에 맞는 식재료가 없을 때는 너가 스스로 보고 판단해서 괜찮은 음식이 나올만한 것으로 하나 추천해줘.

문장: {user_request}

결과는 리스트 형식으로, 각 조건을 쉼표로 구분해서 응답해줘.
예: 파   또는   단백질, 채소
"""

# ✅ GPT 키워드 추출
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "당신은 음식 조건 분석 전문가입니다."},
        {"role": "user", "content": prompt}
    ]
)
raw_keywords = response.choices[0].message.content.strip()
keywords = [kw.strip() for kw in raw_keywords.split(",") if kw.strip()]
print(f"\n정제된 조건 목록: {keywords}")

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

# ✅ 레시피 생성 함수 (조건 포함 + 보유 식재료만 활용)
def get_recipe(ingredients, required_keywords):
    prompt = f"""
    [상황]
    현재 사용자가 냉장고에 가지고 있는 재료는 다음과 같습니다:
    - {', '.join(ingredients)}

    그리고 사용자 요청 조건은 다음과 같습니다:
    - {', '.join(required_keywords)}

    [요청 사항]
    - 반드시 위 재료 목록 안에서만 식재료를 선택하여 요리를 구성해주세요.
    - 조건에 해당하는 주요 식재료는 반드시 포함해주세요.
    - 자연스럽고 조화로운 요리를 구성해주세요.
    - 불필요한 재료는 생략해도 괜찮습니다.
    - 첫 번째 줄에 "요리 이름: ~~" 형식으로 요리 이름을 알려주세요.
    - 그 다음 [재료], [조리법] 순서로 작성해주세요.
    - 조리법은 가능한 한 문장을 짧게 나누어 단계별로 분리해주세요.
    - 예: '고기를 썰고 볶는다' → '고기를 썬다.', '고기를 볶는다.'
    """
    response = client.chat.completions.create(
        model='gpt-4-turbo',
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

# ✅ 요리 이름 추출
def extract_recipe_name(recipe_text):
    match = re.search(r'요리 이름\s*:\s*(.+)', recipe_text)
    return match.group(1).strip() if match else "추천 요리"

# ✅ 조리법 스텝별 그림 생성 (그림체 통일)
def generate_images_from_recipe(recipe_text):
    steps = re.findall(r"(?:[0-9]+\.\s*|•\s*|- )?.*?[\.!\?](?:\n|$)", recipe_text)
    steps = [s.strip() for s in steps if len(s.strip()) > 5]

    images = []
    for idx, step in enumerate(steps, 1):
        prompt = f"""
{step}
이 장면을 **같은 스타일의 단순한 조리 만화 일러스트**로 한 컷 그려줘.
모든 단계가 **통일된 그림체, 색감, 배경 톤**을 가지도록 해줘.
복잡하지 않고, 조리 동작 중심의 일관된 스타일로 간결하게 표현해줘.
"""
        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt.strip(),
                size="1024x1024",
                quality="standard",
                n=1,
            )
            image_url = response.data[0].url
        except Exception as e:
            print(f"⚠️ Step {idx} 이미지 생성 실패: {e}")
            image_url = "이미지 생성 실패"

        images.append((f"Step {idx}", step, image_url))

    return images

# ✅ 실행 흐름
if not filtered_df.empty:
    input_ingredients = filtered_df["식재료"].tolist()
    print(f"\n요청 조건에 맞는 식재료: {', '.join(input_ingredients)}")

    recipe_text = get_recipe(input_ingredients, keywords)
    recipe_name = extract_recipe_name(recipe_text)
    recipe_text_clean = re.sub(r'요리 이름\s*:\s*.+\n?', '', recipe_text, count=1, flags=re.IGNORECASE)

    print(f"\n🍽️ 추천 요리: {recipe_name}")
    print("\n📋 레시피:")
    print(recipe_text_clean)

    print("\n🖼️ 조리법 스토리보드 이미지:")
    storyboard = generate_images_from_recipe(recipe_text_clean)

    for step_title, step_text, img_url in storyboard:
        print(f"{step_title}: {step_text}\n이미지 링크: {img_url}\n")

else:
    print("\n⚠️ 해당 조건에 맞는 식재료가 없습니다.")
