# 1.recipe_ingredients에서 해당 recipe_id의 재료 이름 리스트 가져오기

# 2.가장 최근 이미지 (fridge_images) 가져오기

# 3.그 이미지 기준으로 detected_bboxes 테이블에서:

# 이름이 해당 재료들 중 하나인 bbox 좌표 필터링
# 4.프론트에:

#         image filename

#         [ {name: 사과, x1, y1, x2, y2}, ... ] 형식으로 반환

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.db_tables import FridgeImage, DetectedBBox, Recipe, RecipeIngredient
from sqlalchemy import desc

router = APIRouter()

# 가장 최근 이미지에서 감지된 bbox 중에서
# 입력한 재료 이름(target_names)에 해당하는 것만 필터링해서 반환
def filter_bboxes_by_names(target_names: list[str], db: Session) -> list[dict]:
    # 일단 1 고정
    latest_image = db.query(FridgeImage).filter(
            FridgeImage.filename == 'fridge_sample_01.jpg'
        ).first()
    if not latest_image:
        return [], None
    # # 1. 가장 최근 냉장고 이미지 가져오기
    # latest_image = db.query(FridgeImage).order_by(FridgeImage.captured_at.desc()).first()
    # if not latest_image:
    #     return []
    
    print("📷 DB에서 가져온 이미지 파일명:", latest_image.filename)

    # 2. 해당 이미지에서 감지된 bbox 중 이름이 target_names에 포함된 것만 필터링
    matched_bboxes = db.query(DetectedBBox).filter(
        DetectedBBox.image_id == latest_image.id,
        DetectedBBox.name.in_(target_names)
    ).all()

    # 3. 필요한 정보만 딕셔너리 형태로 반환
    bboxes= [
        {
            "name": box.name,
            "x1": box.x1,
            "y1": box.y1,
            "x2": box.x2,
            "y2": box.y2
        }
        for box in matched_bboxes
    ]
    return bboxes, latest_image.filename

# 최신 레시피 → 해당 재료 리스트 → 그 재료가 감지된 bbox 좌표 반환
@router.get("/recipe/bbox")
def get_bbox_for_latest_recipe(db: Session = Depends(get_db)):
    print("🚀 /recipe/bbox 라우터 호출됨")  # ✅ 이거 넣기
    # 1. 가장 최신 레시피 가져오기
    latest_recipe = db.query(Recipe).order_by(desc(Recipe.created_at)).first()
    if not latest_recipe:
        return {"error": "레시피가 존재하지 않습니다."}
    
    # 2. 해당 레시피의 재료 목록 (가장최신레시피의 recipe_ingredint.name)
    ingredient_rows = db.query(RecipeIngredient).filter(RecipeIngredient.recipe_id == latest_recipe.id).all()
    ingredients_names = [row.name for row in ingredient_rows]

    # 3. 필터 함수로 해당 재료의 bbox 좌표만 추출
    bboxes,image_filename= filter_bboxes_by_names(ingredients_names, db)

    return {
        "image_filename": image_filename,
        "bboxes": bboxes
    }

