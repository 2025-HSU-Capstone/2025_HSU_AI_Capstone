# from io import BytesIO
# from datetime import datetime, timedelta
# from fastapi import APIRouter, UploadFile, File, Depends
# import pandas as pd
# from sqlalchemy.orm import Session
# from app.db.database import get_db
# from app.models.db_tables import FoodItem

# import openai
# from app.core.settings import OPENAI_API_KEY
# print("📦 불러온 API KEY:", OPENAI_API_KEY)
# openai.api_key = OPENAI_API_KEY


# router = APIRouter()

# print("📦 불러온 API KEY:", OPENAI_API_KEY)

# #유통기한 임박 재료 db에서 조회해서 알려주는 api
# @router.get("/expired-soon")
# def get_expiring_items(db: Session = Depends(get_db)):
#     today = datetime.today().date()
#     limit = today + timedelta(days=3)  # 오늘 포함 + 3일
#     items = db.query(FoodItem).filter(FoodItem.expiration_date <= limit).all()


#      # 프론트 형식에 맞게 필드 이름 변경
#     result = [
#         {
#             "name": item.name,
#             "category": item.category,
#             "expiration_date": item.expiration_date.strftime("%Y-%m-%d"),
#             "nutrients": item.nutrients
#         }
#         for item in items
#     ]


#     return result

# # ✅ GPT에게 유통기한 임박 식재료로 요리 추천 요청
# @router.get("/gpt-recipe")
# def gpt_recipe(db: Session = Depends(get_db)):
#     today = datetime.today().date()
#     limit = today + timedelta(days=7)  # GPT 추천은 7일 이내로

#     items = db.query(FoodItem).filter(FoodItem.expiration_date <= limit).all()

#     if not items:
#         return {"message": "유통기한 임박한 재료가 없습니다."}

#     # 📦 GPT 프롬프트 만들기
#     ingredients_list = "\n".join([
#         f"- {item.name} (유통기한: {item.expiration_date}, 영양소: {item.nutrients})"
#         for item in items
#     ])

#     prompt = f"""
# 냉장고에 아래 재료들이 있고, 유통기한이 임박했습니다:

# {ingredients_list}

# 이 재료들을 최대한 활용한 요리를 3가지 추천해주세요.
# """

#     # 📬 GPT API 요청
#     try:
        
#         response = openai.ChatCompletion.create(
#             model="gpt-3.5-turbo",
#             messages=[
#                 {"role": "system", "content": "당신은 요리사입니다."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.7
#         )
#         answer = response.choices[0].message.content
#         return {"recipes": answer}
#     except Exception as e:
#         return {"error": str(e)}
