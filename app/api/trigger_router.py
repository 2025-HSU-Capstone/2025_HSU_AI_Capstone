from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.schemas.detect_swagger import DetectRequest
from app.models.db_tables import FoodItem, FoodLog, FridgeImage, DetectedBBox
from app.db.database import get_db

router = APIRouter()

def update_db(payload: DetectRequest, db: Session) -> dict:
    # 여기 기존 라우터 로직 그대로 복붙
    # 마지막에 return {"added": ..., "removed": ..., "updated": ...}
    
    #detected_items 검사
    detected_items = payload.detected_items
    if not detected_items:
         raise HTTPException(status_code=400, detail="No detected items provided")

    #감지된 재료 이름 추출 vs DB에 이미 있는 재료 비교
    detected_names = {item.name for item in detected_items} 
    current_items = db.query(FoodItem.name).all()
    current_names = {name for (name,) in current_items}

    to_add = detected_names - current_names     # 새로 들어온 재료  
    to_remove = current_names - detected_names  # 냉장고에서 사라진 재료
    to_keep = detected_names & current_names    # 그대로 남아 있는 재료

    # 새로운 쟁장고 사진(FridgeImage) 저장
    image = FridgeImage(
        filename=payload.image_filename,
        captured_at=payload.captured_at
    )
    db.add(image)
    db.commit()

    #food_item테이블블
    for item in detected_items:
        name = item.name
        bbox = item.bbox

        #FoodItem 테이블에 신규 재료 등록
        #FoodLog 테이블에 "in" 로그 기록
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
        #FoodItem.detected_at 최신화
        elif name in to_keep:
            item_row = db.query(FoodItem).filter_by(name=name).first()
            if item_row:
                item_row.detected_at = datetime.now()

        #감지된 모든 재료의 bbox 저장 (DetectedBBox)
        db.add(DetectedBBox(
            image_id=image.id,
            name=name,
            x1=bbox.x1,
            y1=bbox.y1,
            x2=bbox.x2,
            y2=bbox.y2
        ))

    #냉장고에서 사라졌다고 판단 → 삭제
    #→ 동시에 "out" 로그로 FoodLog 테이블에 남김
    for name in to_remove:
        db.query(FoodItem).filter_by(name=name).delete()
        db.add(FoodLog(
                name=name,
                status="out",
                changed_at=datetime.now(),
                image_id=image.id
        ))
    db.commit()


    #어떤 재료가 새로 생겼고, 어떤 게 없어졌고, 어떤 건 그대로 있었는지 알려줌
    return {"added": list(to_add), "removed": list(to_remove), "updated": list(to_keep)}
    
from datetime import datetime
from pathlib import Path

def capture_image() -> tuple[Path, datetime]:
    # 1. 현재 시간
    now = datetime.now()

    # 2. 더미 이미지 파일 경로 (진짜 촬영할 경우엔 카메라 코드로 대체)
    filename = "fridge_sample_01.jpg" #더미이미지 이름름
    # filename = f"fridge_{now.strftime('%Y%m%d_%H%M%S')}.jpg" #실제 이미지 이름
    image_path = Path(f"./data/captured_images/{filename}")  # 실제 저장 위치

    # 3. (실제로는 여기에 카메라 촬영 로직이 들어갈 수 있음)
    print(f"📸 이미지 캡처됨: {image_path}")

    return image_path, now

def call_detection_model(image_path: Path) -> dict:
    # 실제로는 모델 서버에 requests.post(...)로 전송해야 함
    print(f"📤 모델에 이미지 전송: {image_path.name}")

    # 더미 응답 예시 (모델이 반환하는 감지 결과 JSON 형식)
    return{
  "image_filename": "image_path.name",
  "captured_at": "datetime.now().isoformat()",
  "detected_items": [
      {
      "name": "돼지고기",
      "bbox": { "x1": 18, "y1": 90, "x2": 100, "y2": 163 }
      },
      {
        "name": "소고기",
        "bbox": { "x1": 23, "y1": 19, "x2": 102, "y2": 115 }
      },
      {
        "name": "닭고기",
        "bbox": { "x1": 63, "y1": 51, "x2": 149, "y2": 135 }
      },
      {
        "name": "사과",
        "bbox": { "x1": 65, "y1": 10, "x2": 154, "y2": 74 }
      },
      {
        "name": "파",
        "bbox": { "x1": 45, "y1": 82, "x2": 108, "y2": 145 }
      },
      {
        "name": "당근",
        "bbox": { "x1": 92, "y1": 37, "x2": 190, "y2": 133 }
      },
      {
        "name": "양파",
        "bbox": { "x1": 53, "y1": 69, "x2": 109, "y2": 169 }
      },
      {
        "name": "감자",
        "bbox": { "x1": 23, "y1": 15, "x2": 118, "y2": 66 }
      },
      {
        "name": "계란",
        "bbox": { "x1": 52, "y1": 22, "x2": 102, "y2": 93 }
      },
      {
        "name": "치즈",
        "bbox": { "x1": 37, "y1": 32, "x2": 91, "y2": 94 }
      }
    ]
  }
  
#카메라사진호출->반환값(냉장고사진)모델호출->반환값(.json)db업뎃하는 최종 라우터터
@router.post("/trigger/detect")
def run_detection_trigger(db: Session = Depends(get_db)):
    # 1. 카메라 → 이미지 촬영
    image_path, timestamp = capture_image()

    # 2. 객체 탐지 모델에 이미지 전송
    result = call_detection_model(image_path)

    # 3. 모델이 반환한 감지 결과를 payload로 가공
    detect_payload = DetectRequest(
        image_filename=image_path.name,
        captured_at=timestamp,
        detected_items=result["detected_items"]
    )

    # 4. 감지 결과 DB 저장
    return update_db(detect_payload, db)

#이벤트 기반 처리 시 내부 함수 호출 필수
#각각 기능 디버깅하게 각 함수를 라우터에 넣는다다
# detect_logic.py


@router.post("/detect")
def detect_from_model(payload: DetectRequest, db: Session = Depends(get_db)):
    return update_db(payload, db)
