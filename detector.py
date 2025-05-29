import cv2
import numpy as np
from ultralytics import YOLO
from segment_anything import sam_model_registry, SamPredictor
from collections import defaultdict
import cloudinary
import cloudinary.uploader
import tempfile
import os
import json
from datetime import datetime

# ✅ Cloudinary 설정
cloudinary.config(
    cloud_name="dawjwfi88",
    api_key="737816378397999",
    api_secret="P_JWtRHUKXXiy3MuGLzUpsBAADc",
    secure=True
)

# ✅ 설정
YOLO_MODEL_PATH = "/home/elicer/AI_capstone/best.pt"
SAM_CHECKPOINT = "/home/elicer/AI_capstone/sam_vit_b.pth"
CLASS_NAMES = ['당근', '마늘', '양파', '돼지고기', '감자']

# ✅ 모델 초기화 (처음 1번만)
yolo_model = YOLO(YOLO_MODEL_PATH)
sam = sam_model_registry["vit_b"](checkpoint=SAM_CHECKPOINT)
predictor = SamPredictor(sam)

def run_inference(image_path: str) -> dict:
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"❌ 이미지 파일을 찾을 수 없습니다: {image_path}")

    # ✅ YOLO 추론
    results = yolo_model.predict(
        source=img,
        save=False,
        conf=0.3,
        imgsz=640
    )
    boxes = results[0].boxes

    # ✅ SAM 설정
    predictor.set_image(img)

    mask_counter = defaultdict(int)
    detected_items = []

    for i in range(len(boxes)):
        cls_id = int(boxes.cls[i].item())
        label = CLASS_NAMES[cls_id]
        x1, y1, x2, y2 = map(int, boxes.xyxy[i].tolist())

        masks, _, _ = predictor.predict(
            box=np.array([x1, y1, x2, y2]),
            multimask_output=False
        )

        mask = masks[0].astype(np.uint8) * 255
        mask_counter[label] += 1
        mask_index = mask_counter[label]

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            temp_path = tmp.name
            cv2.imwrite(temp_path, mask)

        upload_result = cloudinary.uploader.upload(
            temp_path,
            folder="smartfridge/mask_images/",
            public_id=f"{label}_mask_{mask_index}",
            overwrite=True
        )

        os.remove(temp_path)

        mask_url = upload_result["secure_url"]
        print(f"☁️ Uploaded {label} to Cloudinary: {mask_url}")

        detected_items.append({
            "name": label,
            "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
            "mask_url": mask_url
        })

    output_json = {
        "image_filename": os.path.basename(image_path),
        "captured_at": datetime.utcnow().isoformat(),
        "detected_items": detected_items
    }

    # ✅ 최종 결과 JSON 출력
    print("📦 최종 추론 결과 JSON:")
    print(json.dumps(output_json, indent=2, ensure_ascii=False))

    return output_json