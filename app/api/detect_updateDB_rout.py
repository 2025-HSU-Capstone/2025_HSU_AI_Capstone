#카메라->백엔드->모델 로직 붙이기 방법:
#1.POST /upload-image 라우터 붙이기 또는
#2./detect 라우터를 고쳐서 한 라우터로 처리하기 
    #변화 후
    # POST /detect (이미지 업로드 포함)
    # 이 라우터 하나에서:
    # 이미지 파일 업로드 (프론트나 카메라에서)
    # 백엔드가 모델 API에 이미지 전송 (→ JSON 받기)
    # 받은 JSON으로 DB 업데이트 (지금 있는 로직 그대로)
    # 프론트에 결과 응답 (추가/삭제된 항목)
    # -> 이미지 업로드 + 모델 호출 코드만 추가하면 됨 



# 라우터를 수정하는 게 아니라,
# "이 라우터를 호출하는 위치"를 다음처럼 바꾸는 것:

# 1.📸 사진 찍힘
# 2.🤖 모델이 객체 탐지해서 .json 생성
# 3.🌐 백엔드의 /detect 라우터에 .json 전송
#     POST http://your-server/detect
#     body: { image_filename, captured_at, detected_items: [...] }
# 즉, 모델이 자동으로 호출되든 수동으로 하든, .json만 이 라우터에 전달되면 자동처리 돼.


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.schemas.detect_swagger import DetectRequest
from app.models.db_tables import FoodItem, FoodLog, FridgeImage, DetectedBBox
from app.db.database import get_db

router = APIRouter()

#모델에서 반환한 json을 비교하여 db에 저장(업데이트) 허는 라우터
@router.post("/detect") #http://localhost:8000/detect=호출되는 api 주소
def process_detected_items(payload: DetectRequest, db: Session = Depends(get_db)):
    try: 
        detected_items = payload.detected_items
        if not detected_items:
            raise HTTPException(status_code=400, detail="No detected items provided")

        detected_names = {item.name for item in detected_items}
        current_items = db.query(FoodItem.name).all()
        current_names = {name for (name,) in current_items}

        to_add = detected_names - current_names
        to_remove = current_names - detected_names
        to_keep = detected_names & current_names

    # 이미지 정보 저장
        image = FridgeImage(
            filename=payload.image_filename,
            captured_at=payload.captured_at
        )
        db.add(image)
        db.commit()

        for item in detected_items:
            name = item.name
            bbox = item.bbox

            if name in to_add:
                db.add(FoodItem(
                    name=name,
                    detected_at=datetime.now(),
                    image_id=image.id
                ))
                db.add(FoodLog(
                    name=name,
                    status="in",
                    changed_at=datetime.now(),
                    image_id=image.id
                ))

            elif name in to_keep:
                item_row = db.query(FoodItem).filter_by(name=name).first()
                if item_row:
                    item_row.detected_at = datetime.now()
            db.add(DetectedBBox(
                image_id=image.id,
                name=name,
                x1=bbox.x1,
                y1=bbox.y1,
                x2=bbox.x2,
                y2=bbox.y2
            ))

        for name in to_remove:
            db.query(FoodItem).filter_by(name=name).delete()
            db.add(FoodLog(
                name=name,
                status="out",
                changed_at=datetime.now(),
                image_id=image.id
            ))

        db.commit()
        return {"added": list(to_add), "removed": list(to_remove), "updated": list(to_keep)}
    
    except Exception as e:
        print(" 처리 중 오류 발생:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")
#json 어떻게 받는지 
# @router.post("/detect")	이 라우터가 POST 요청 처리
# payload: DetectRequest	JSON 전체를 객체로 받음
# DetectRequest=변수형같은거	JSON 구조를 정의함 (filename, captured_at, detected_items)
# payload.detected_items	감지된 항목 리스트에 접근
# 요청 본문(JSON)은 FastAPI가 자동으로 DetectRequest 객체로 파싱

#swagger의 HTTP POST 요청의 body에 넣어야 함

#원리
# 1️⃣ 감지 JSON 수신	POST /detect로 JSON 받음 (image_filename, captured_at, detected_items)
# 2️⃣ 이미지 정보 저장	fridge_images 테이블에 저장 후 image_id 확보
# 3️⃣ 현재 DB 상태 비교	기존 food_items와 감지 결과를 이름 기준으로 비교
# 4️⃣ 처리	
# - 새로 감지됨 → INSERT + 로그 "in"	
# - 사라짐 → DELETE + 로그 "out"	
# - 유지됨 → UPDATE detected_at	
# 5️⃣ BBox 저장	모든 감지된 항목에 대해 detected_bboxes 저장
# ✅ 결과 응답	어떤 항목이 추가/삭제/갱신됐는지 JSON 반환