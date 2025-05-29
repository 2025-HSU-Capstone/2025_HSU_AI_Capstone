# 작동 흐름름
# 1감지된 재료 DB에서 불러오기
# 2모델 API 호출->레시피 받아오기(제목+재료+스텝이미지 등등)
# 3모델 응답(JSON)을 DB에 저장
    #recipes: 제목 + 유저 입력
    #recipe_ingredients: 사용된 재료들
    #recipe_images: 단계별 이미지
# 4프론트에 보여줄 데이터 JSON으로 응답(이름 + 설명 or 이미지 리스트)

# 1.프론트 → 백엔드
#  사용자가 버튼을 누르면, 프론트는 백엔드의 /generate-recipe 같은 라우터에 요청을 보냄
# 2.백엔드 → 모델 API
#   백엔드는 받은 식재료나 이미지 정보를 정리해서, "모델 API"에 POST 요청함
#   requests.post("http://모델API주소", json=payload) 같은 방식으로
# 3.모델 → 백엔드
#   모델이 응답(JSON)을 반환하면, 백엔드는 그걸 받아서
#   DB에 저장하고
#   프론트에 다시 응답해줌


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.database import get_db
from app.models.db_tables import Recipe, RecipeIngredient, RecipeImage, FoodItem
from app.schemas.detect_swagger import RecipeRequest

router = APIRouter()

from fastapi.responses import FileResponse
from fastapi import Request
import os

#Flask 연결
import requests

# 🔁 임시로 모델 역할을 해주는 함수 (모델 API 대신)
def dummy_model_response(user_input: str, ingredients: list[str]) -> dict:
    if user_input == "단백질 많은 레시피 추천해줘":
        return {
            "title": "단백질 폭탄 오믈렛",
            "ingredients": ingredients,
            "steps": [
                {"step": 1, "image_url": "/recipe_images/step1.png"},
                {"step": 2, "image_url": "/recipe_images/step2.png"}
            ]
        }
    else:
        return {
            "title": "기본 감자계란전",
            "ingredients": ingredients,
            "steps": [
                {"step": 1, "image_url": "/recipe_images/step1.png"},
                {"step": 2, "image_url": "/recipe_images/step2.png"}
            ]
        }


#사용자 입력받고 버튼 누르면 레시피 반환하는 라우터
@router.post("/generate_recipe") #그 변수의 이름 #클라이언트가 보낸 데이터 묶음"이라는 뜻으로 자주 써.
def generate_recipe_from_detected(payload: RecipeRequest,db: Session = Depends(get_db)):
                                #input                 #입력받은 값을 일일이 Session = Depends(get_db)로 받을 수 없으므로 db로 바꿈꿈
        #사용자 요청사항 입력
        user_input = payload.user_input

        #백엔드가 db에서 사진에서 감지된 재료(food_item.name) 불러옴
        items = db.query(FoodItem.name).all()
        print("📦 감지된 재료:", items)

        ingredient_names = [name for (name,) in items]
        if not ingredient_names:
            return {"message": "감지된 재료가 없습니다."}

        #  Flask 모델 서버로 요청 보내기
        try:
            flask_url = "/api/generate" #다른 노트북 서버로 변경경
            payload = {
                "user_input": user_input,
                "ingredients": ingredient_names
            }
            res = requests.post(flask_url, json=payload)
            res.raise_for_status()
            gpt_response = res.json()
            print("📡 Flask 모델 응답:", gpt_response)
            print("📡 Flask 상태코드:", res.status_code)
        except Exception as e:
            print("❌ Flask 모델 호출 실패:", e)
            print("📡 Flask 상태코드:", res.status_code)
            return {"error": "Flask 모델 호출 실패"}
        
        # 레시피 저장
        recipe = Recipe(
            title=gpt_response["title"],
            user_input=user_input, 
            created_at=datetime.utcnow()
        )
        db.add(recipe)
        db.commit()
        print("📌 레시피 저장 완료")

        # 재료 저장
        for ing in gpt_response["ingredients"]:
            db.add(RecipeIngredient(recipe_id=recipe.id, name=ing))

        # 이미지 저장
        for step_data in gpt_response["steps"]:
            db.add(RecipeImage(
                recipe_id=recipe.id,
                step=step_data["text"],
                image_url=step_data["image_url"]
            ))

        db.commit()
        print("📌 모든 저장 완료")

        #프론트에 json으로 반환
        return {
            "title": recipe.title,
            "ingredients": gpt_response["ingredients"],
            "steps": gpt_response["steps"]
        }
   

