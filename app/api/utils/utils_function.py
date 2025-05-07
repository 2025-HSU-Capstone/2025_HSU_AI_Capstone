#테스트 seed json swagger가 알아듣도록 변환하는 함수
#insert_seed_on_startup() 함수는 FastAPI 앱 실행 시 자동으로 seed_detected.json을 읽고 DB에 넣는 백그라운드 작업
#실행하면 자동 실행되는 함수라 필요없을듯 이미 detected라우터가 있음음
import json
from datetime import datetime
from pathlib import Path
from app.db.database import SessionLocal
from app.models.db_tables import FoodItem, FoodLog, FridgeImage, DetectedBBox
import traceback

def insert_seed_on_startup():
    path = Path("data/test_inputs/seed_detected.json")
    if not path.exists():
        print("seed_detected.json not found.")
        return

    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    db = SessionLocal()
    try:
        detected_items = payload.get("detected_items", [])
        if not detected_items:
            print("No detected_items in JSON.")
            return

        detected_names = {item["name"] for item in detected_items}
        current_items = db.query(FoodItem.name).all()
        current_names = {name for (name,) in current_items}

        to_add = detected_names - current_names
        to_remove = current_names - detected_names
        to_keep = detected_names & current_names

        image = FridgeImage(
            filename=payload["image_filename"],
            captured_at=datetime.fromisoformat(payload["captured_at"])
        )
        db.add(image)
        db.commit()
        db.refresh(image)

        for item in detected_items:
            name = item["name"]
            bbox = item["bbox"]

            if name in to_add:
                db.add(FoodItem(name=name, detected_at=datetime.now(), image_id=image.id))
                db.add(FoodLog(name=name, status="in", changed_at=datetime.now(), image_id=image.id))
            elif name in to_keep:
                existing = db.query(FoodItem).filter_by(name=name).first()
                if existing:
                    existing.detected_at = datetime.now()

            db.add(DetectedBBox(
                image_id=image.id,
                name=name,
                x1=bbox["x1"],
                y1=bbox["y1"],
                x2=bbox["x2"],
                y2=bbox["y2"]
            ))

        for name in to_remove:
            db.query(FoodItem).filter_by(name=name).delete()
            db.add(FoodLog(name=name, status="out", changed_at=datetime.now(), image_id=image.id))

        db.commit()
        print("자동으로 DB에 seed_detected.json 반영 완료.")
    except Exception as e:
        print("에러 발생:")
        print(traceback.format_exc().encode("ascii", errors="ignore").decode())
    finally:
        db.close()
