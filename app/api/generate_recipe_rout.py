# ✅ 통합 구조: 백엔드 (FastAPI), 모델 서버 (Flask), 프론트 (React) 연동을 위한 generate_recipe_rout.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse  # ✅ 이거 추가!!
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.database import get_db
from app.models.db_tables import Recipe, RecipeIngredient, RecipeImage, FoodItem
from app.schemas.detect_swagger import RecipeRequest
import requests
import urllib3
import json


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

router = APIRouter()

@router.post("/generate_recipe/stream")
def generate_recipe_stream(payload: RecipeRequest, db: Session = Depends(get_db)):
    user_input = payload.user_input.model_dump()
    items = db.query(FoodItem.name).all()
    ingredient_names = [name for (name,) in items]

    if not ingredient_names:
        raise HTTPException(status_code=400, detail="감지된 재료가 없습니다.")

    flask_url = "https://4e56-58-142-221-141.ngrok-free.app/api/generate"
    model_payload = {
        "user_input": user_input,
        "ingredients": ingredient_names
    }

    try:
        res = requests.post(flask_url, json=model_payload, timeout=120, verify=False)
        res.raise_for_status()
        result = res.json()
        return JSONResponse(content=result)
    except requests.exceptions.RequestException as e:
        print("❌ Flask 모델 호출 실패:", e)
        raise HTTPException(status_code=500, detail="Flask 모델 호출 실패")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail="JSON 디코딩 실패: " + str(e))
    
    
    # result는 다음 구조여야 함:
    # {
    #   "title": "요리 제목",
    #   "ingredients": [...],
    #   "steps": [
    #     { "step": 1, "text": "조리 단계", "image_url": "..." },
    #     ...
    #   ]
    # }

    

# ✅ 프론트와의 JSON 인터페이스 명세
# 프론트엔드는 다음 구조를 받음:
# {
#   title: "레시피 제목",
#   ingredients: ["재료1", "재료2", ...],
#   steps: [
#     {
#       step: 1,
#       text: "조리 단계 설명",
#       image_url: "http://..."
#     },
#     ...
#   ]
# }

# ✅ 프론트 (React/RecipeStoryboard.jsx)는 이 JSON을 기반으로 렌더링하고 있음 → `text`, `image_url` 필드 포함 필수
# ✅ Flask 모델 (`generate_recipe_from_request_stream`)는 반드시 위 구조를 지켜야 하고, `text`, `step`, `image_url` 필드를 포함해야 함
