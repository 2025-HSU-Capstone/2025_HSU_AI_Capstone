# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from datetime import datetime

# from app.schemas.detect_swagger import DetectRequest
# from app.schemas.detect_swagger import DetectRequest, DetectedItem
# from app.models.db_tables import FoodItem, FoodLog, FridgeImage, DetectedBBox, DetectedMask

# from app.db.database import get_db
# # Flask 연결
# import requests
# from pathlib import Path

# # 역할 : "냉장고 사진 1장을 찍고 → 모델에 보내서 재료를 감지하고 → DB에 저장하는 전체 자동화 흐름"
# # 1. /trigger/detect 라우터가 호출되면
# # 2. capture_image() 호출
# #   📸 냉장고 사진 1장을 찍음 (더미 이미지 사용 중)
# #   현재 시간도 함께 저장
# # 3. call_detection_model() 호출
# #   Flask 모델 서버에 이미지 전송 (지금은 더미 JSON 반환)
# #   재료 리스트 + bbox 좌표 + mask_url 포함된 감지 결과 JSON 생성
# router = APIRouter()
# # 버리는 라우터터
# print("trigger_router.py 불러와짐")

# def update_db(payload: DetectRequest, db: Session) -> dict:
#     # 여기 기존 라우터 로직 그대로 복붙
#     # 마지막에 return {"added": ..., "removed": ..., "updated": ...}

#     print("update_db() 진입")
#     print("이미지 파일명:", payload.image_filename)
#     print("촬영 시간:", payload.captured_at)

#     # detected_items 검사
#     detected_items = payload.detected_items
#     print("감지된 재료 수:", len(detected_items))
#     print("감지된 재료 리스트:", [item.name for item in detected_items])

#     # 감지된 재료 이름 추출 vs DB에 이미 있는 재료 비교
#     detected_names = {item.name for item in detected_items} 
#     current_items = db.query(FoodItem.name).all()
#     current_names = {name for (name,) in current_items}
#     print("현재 DB 내 재료:", current_names)

#     to_add = detected_names - current_names     # 새로 들어온 재료
#     to_remove = current_names - detected_names  # 냉장고에서 사라진 재료
#     to_keep = detected_names & current_names    # 그대로 남아 있는 재료
#     print("추가할 재료:", to_add)
#     print("제거할 재료:", to_remove)
#     print("유지할 재료:", to_keep)

#     # 새로운 냉장고 사진(FridgeImage) 저장
#     image = FridgeImage(
#         filename=payload.image_filename,
#         captured_at=payload.captured_at
#     )
#     db.add(image)
#     db.commit()
#     print("이미지 DB에 저장됨 → image_id:", image.id)

#     # food_item 테이블
#     for item in detected_items:
#         name = item.name
#         bbox = item.bbox

#         print(f"재료 처리 중: {name} / bbox: {bbox}")

#         # FoodItem 테이블에 신규 재료 등록
#         # FoodLog 테이블에 "in" 로그 기록
#         if name in to_add:
#             db.add(FoodItem(
#                 name=name,
#                 detected_at=datetime.now(),
#                 image_id=image.id
#             ))
#             db.add(FoodLog(
#                 name=name,
#                 status="in",
#                 changed_at=datetime.now(),
#                 image_id=image.id
#             ))
#             print(f"새 재료 추가됨: {name}")
#         # FoodItem.detected_at 최신화
#         elif name in to_keep:
#             item_row = db.query(FoodItem).filter_by(name=name).first()
#             if item_row:
#                 item_row.detected_at = datetime.now()
#                 item_row.image_id = image.id  # ✅ 이거 추가
#                 print(f"감지시간 및 이미지ID 갱신됨: {name}")

#         # 감지된 모든 재료의 bbox 저장 (DetectedBBox)
#         bbox_entry = DetectedBBox(
#             image_id=image.id,
#             name=name,
#             x1=bbox.x1,
#             y1=bbox.y1,
#             x2=bbox.x2,
#             y2=bbox.y2
#         )
#         db.add(bbox_entry)
#         db.commit()
#         db.refresh(bbox_entry)

#         # SAM 마스크 저장 (마스크 URL은 이름 기반 하드코딩 매핑)
#         mask_url = item.mask_url
#         if mask_url:
#             db.add(DetectedMask(
#                 image_id=image.id,
#                 name=name,
#                 bbox_id=bbox_entry.id,
#                 mask_url=mask_url
#             ))
#             print(f"🖼️ 마스크 저장됨: {name} → {mask_url}")


#     # 냉장고에서 사라졌다고 판단 → 삭제
#     # → 동시에 "out" 로그로 FoodLog 테이블에 남기기
#     for name in to_remove:
#         db.query(FoodItem).filter_by(name=name).delete()
#         db.add(FoodLog(
#             name=name,
#             status="out",
#             changed_at=datetime.now(),
#             image_id=image.id
#         ))
#         print(f"제거된 재료: {name}")

#     db.commit()
#     print("모든 DB 변경 사항 커밋 완료")

#     # 어느 재료가 새로 생겼고, 어느 것이 없어진 것이고, 어느 것은 그대로 있었는지 알림
#     return {"added": list(to_add), "removed": list(to_remove), "updated": list(to_keep)}

# def capture_image() -> tuple[Path, datetime]:
#     # 1. 현재 시간
#     now = datetime.now()

#     # 2. 더미 이미지 파일 경로 (지금 청사할 경우에는 카메라 코드로 대체)
#     filename = "fridge_sample_01.jpg"  # 더미이미지 이름
#     image_path = Path(f"./data/captured_images/{filename}")  # 실제 저장 위치

#     # 3. (실제로는 여기에 카메라 청사 로직이 들어가며)
#     print(f"이미지 캡처됨: {image_path}")

#     return image_path, now

# def call_detection_model(image_path: Path) -> dict:
#     # 실제로는 모델 서버에 requests.post(...)로 전송해야 함
#     now = datetime.now()
#     print(f"모델에 이미지 전송: {image_path.name}")

#     # 더미로 보내는 JSON 데이터
#     return {
#         "image_filename": image_path.name,
#         "captured_at": now,
#         "detected_items": [
#             {
#                 "name": "돼지고기",
#                 "bbox": { "x1": 18, "y1": 90, "x2": 100, "y2": 163 },
#                 "mask_url": "https://res.cloudinary.com/dawjwfi88/image/upload/v1748196093/smartfridge/mask_images/돼지고기_mask.png"
#             },
#             {
#                 "name": "소고기",
#                 "bbox": { "x1": 23, "y1": 19, "x2": 102, "y2": 115 },
#                 "mask_url": "https://res.cloudinary.com/dawjwfi88/image/upload/v1748196093/smartfridge/mask_images/소고기_mask.png"
#             },
#             {
#                 "name": "닭고기",
#                 "bbox": { "x1": 63, "y1": 51, "x2": 149, "y2": 135 },
#                 "mask_url": "https://res.cloudinary.com/dawjwfi88/image/upload/v1748196094/smartfridge/mask_images/닭고기_mask.png"
#             },
#             {
#                 "name": "사과",
#                 "bbox": { "x1": 65, "y1": 10, "x2": 154, "y2": 74 },
#                 "mask_url": "https://res.cloudinary.com/dawjwfi88/image/upload/v1748196095/smartfridge/mask_images/사과_mask.png"
#             },
#             {
#                 "name": "파",
#                 "bbox": { "x1": 45, "y1": 82, "x2": 108, "y2": 145 },
#                 "mask_url": "https://res.cloudinary.com/dawjwfi88/image/upload/v1748196096/smartfridge/mask_images/파_mask.png"
#             },
#             {
#                 "name": "마늘",
#                 "bbox": { "x1": 92, "y1": 37, "x2": 190, "y2": 133 },
#                 "mask_url": "https://res.cloudinary.com/dawjwfi88/image/upload/v1748196097/smartfridge/mask_images/마늘_mask.png"
#             },
#             {
#                 "name": "양파",
#                 "bbox": { "x1": 53, "y1": 69, "x2": 109, "y2": 169 },
#                 "mask_url": "https://res.cloudinary.com/dawjwfi88/image/upload/v1748196097/smartfridge/mask_images/양파_mask.png"
#             },
#             {
#                 "name": "감자",
#                 "bbox": { "x1": 23, "y1": 15, "x2": 118, "y2": 66 },
#                 "mask_url": "https://res.cloudinary.com/dawjwfi88/image/upload/v1748196098/smartfridge/mask_images/감자_mask.png"
#             },
#             {
#                 "name": "계란",
#                 "bbox": { "x1": 52, "y1": 22, "x2": 102, "y2": 93 },
#                 "mask_url": "https://res.cloudinary.com/dawjwfi88/image/upload/v1748196099/smartfridge/mask_images/계란_mask.png"
#             },
#             {
#                 "name": "치즈",
#                 "bbox": { "x1": 37, "y1": 32, "x2": 91, "y2": 94 },
#                 "mask_url": "https://res.cloudinary.com/dawjwfi88/image/upload/v1748196099/smartfridge/mask_images/치즈_mask.png"
#             }
#         ]
#     }

# # 카메라사진호출 → 반환값 (냉장고사진) 모델호출 → 반환값(.json) db 업데이트하는 최종 라우터
# @router.post("/trigger/detect")
# def run_detection_trigger(db: Session = Depends(get_db)):
#     print("라우터 진입 확인")
#     try:
#         # 1. 카메라 → 이미지 촬영
#         image_path, timestamp = capture_image()
#         # 2. 객체 탐지 모델에 이미지 전송
#         result = call_detection_model(image_path)
#         # 3. 모델이 반환한 감지 결과를 payload로 가공
#         detected_items = [DetectedItem(**item) for item in result["detected_items"]]
        
#         detect_payload = DetectRequest(
#             image_filename=result["image_filename"],
#             captured_at=result["captured_at"],
#             detected_items=detected_items
#         )
#         return update_db(detect_payload, db)

#     except Exception as e:
#         print("전체 예외 발생:", e)
#         raise HTTPException(status_code=500, detail=str(e))

# # 이벤트 기반 처리 시 내부 함수 호출 필요
# # 각각 기능 디버깅하게 각 함수를 라우터에 넣는다
# @router.post("/detect")
# def detect_from_model(payload: DetectRequest, db: Session = Depends(get_db)):
#     return update_db(payload, db)

# # ✅ 최종적으로 저장되는 DB 항목 요약
# # 1. 📸 FridgeImage
# # 냉장고 사진 1장당 1개 생성됨

# # 항목: filename, captured_at

# # ✔ image_id는 나머지 테이블들과 연결되는 기준 ID로 사용됨

# # 2. 🍱 FoodItem
# # 새로 감지된 재료만 생성됨 (이전에 없던 것)

# # 항목: name, detected_at, image_id

# # ✔ 기존에 있던 항목이면 detected_at만 갱신되고 재삽입 안 됨

# # 3. 🪵 FoodLog
# # 상태 변경 기록 (in, out) 저장

# # 항목: name, status, changed_at, image_id

# # ✔ added된 재료는 status = in, removed된 재료는 status = out

# # 4. 🔲 DetectedBBox
# # 감지된 모든 재료에 대해 bbox 좌표 저장

# # 항목: image_id, name, x1, y1, x2, y2

# # ✔ added, updated 둘 다 bbox는 새로 저장됨

# # 5. 🎭 DetectedMask
# # 감지된 재료 중 mask_url이 존재할 경우만 저장

# # 항목: image_id, name, bbox_id, mask_url

# # ✔ bbox_id는 위에서 생성된 DetectedBBox의 ID

