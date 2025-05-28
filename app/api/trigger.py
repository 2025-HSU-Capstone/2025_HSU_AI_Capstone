from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.schemas.detect_swagger import DetectRequest
from app.schemas.detect_swagger import DetectRequest, DetectedItem
from app.models.db_tables import FoodItem, FoodLog, FridgeImage, DetectedBBox, DetectedMask

from app.db.database import get_db
# Flask 연결
import requests
from pathlib import Path

router = APIRouter()

print("trigger_router.py 불러와짐")

def update_db(payload: DetectRequest, db: Session) -> dict:
    # 여기 기존 라우터 로직 그대로 복붙
    # 마지막에 return {"added": ..., "removed": ..., "updated": ...}

    print("update_db() 진입")
    print("이미지 파일명:", payload.image_filename)
    print("촬영 시간:", payload.captured_at)

    # detected_items 검사
    detected_items = payload.detected_items
    print("감지된 재료 수:", len(detected_items))
    print("감지된 재료 리스트:", [item.name for item in detected_items])

    # 감지된 재료 이름 추출 vs DB에 이미 있는 재료 비교
    detected_names = {item.name for item in detected_items} 
    current_items = db.query(FoodItem.name).all()
    current_names = {name for (name,) in current_items}
    print("현재 DB 내 재료:", current_names)

    to_add = detected_names - current_names     # 새로 들어온 재료
    to_remove = current_names - detected_names  # 냉장고에서 사라진 재료
    to_keep = detected_names & current_names    # 그대로 남아 있는 재료
    print("추가할 재료:", to_add)
    print("제거할 재료:", to_remove)
    print("유지할 재료:", to_keep)

    # 1.새로운 냉장고 사진(FridgeImage) 저장(fridge_images)
    image = FridgeImage(
        filename=payload.image_filename,
        captured_at=payload.captured_at
    )
    db.add(image)
    db.commit()
    print("이미지 DB에 저장됨 → image_id:", image.id)

    # food_item 테이블
    for item in detected_items:
        name = item.name
        bbox = item.bbox

        print(f"재료 처리 중: {name} / bbox: {bbox}")

    # 2.식재료 이름 저장 (food_items)
        # FoodItem 테이블에 신규 재료 등록
        # FoodLog 테이블에 "in" 로그 기록
        if name in to_add:
            db.add(FoodItem(
                name=name,
                detected_at=datetime.now(),
                image_id=image.id
            ))
        # 3.입출 기록 저장 (food_logs)
            db.add(FoodLog(
                name=name,
                status="in",
                changed_at=datetime.now(),
                image_id=image.id
            ))
            print(f"새 재료 추가됨: {name}")
        # FoodItem.detected_at 최신화
        elif name in to_keep:
            item_row = db.query(FoodItem).filter_by(name=name).first()
            if item_row:
                item_row.detected_at = datetime.now()
                item_row.image_id = image.id  # ✅ 이거 추가
                print(f"감지시간 및 이미지ID 갱신됨: {name}")

        # 4.감지된 모든 재료의 bbox 저장 (detected_bboxes)
        bbox_entry = DetectedBBox(
            image_id=image.id,
            name=name,
            x1=bbox.x1,
            y1=bbox.y1,
            x2=bbox.x2,
            y2=bbox.y2
        )
        db.add(bbox_entry)
        db.commit()
        db.refresh(bbox_entry)

        # 5.SAM 마스크 저장 (마스크 URL은 이름 기반 하드코딩 매핑) (detected_masks)
        mask_url = item.mask_url
        if mask_url:
            db.add(DetectedMask(
                image_id=image.id,
                name=name,
                bbox_id=bbox_entry.id,
                mask_url=mask_url
            ))
            print(f"🖼️ 마스크 저장됨: {name} → {mask_url}")


    # 냉장고에서 사라졌다고 판단 → 삭제
    # → 동시에 "out" 로그로 FoodLog 테이블에 남기기
    for name in to_remove:
        db.query(FoodItem).filter_by(name=name).delete()
        db.add(FoodLog(
            name=name,
            status="out",
            changed_at=datetime.now(),
            image_id=image.id
        ))
        print(f"제거된 재료: {name}")

    db.commit()
    print("모든 DB 변경 사항 커밋 완료")

    # 어느 재료가 새로 생겼고, 어느 것이 없어진 것이고, 어느 것은 그대로 있었는지 알림
    return {"added": list(to_add), "removed": list(to_remove), "updated": list(to_keep)}

@router.post("/detect")
def detect_from_model(payload: DetectRequest, db: Session = Depends(get_db)):
    return update_db(payload, db)
