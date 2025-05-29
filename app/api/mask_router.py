from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.db_tables import FridgeImage, DetectedMask
from sqlalchemy import desc

router = APIRouter()

@router.get("/fridge/masks")
def get_segmentation_masks(db: Session = Depends(get_db)):
    # fridge_images 테이블에서 가장 최근 이미지 1장을 찾음
    latest_image = db.query(FridgeImage).order_by(desc(FridgeImage.captured_at)).first()
    if not latest_image:
        return {"masks": []}
    # 해당 image_id에 연결된 detected_masks 테이블의 데이터를 조회
    masks = db.query(DetectedMask).filter(DetectedMask.image_id == latest_image.id).all()
    
    
    # 각 마스크에 대해 name(재료 이름)과 mask_url(Cloudinary URL)로 구성된 리스트를 JSON으로 반환
    CLOUDINARY_BASE = "https://res.cloudinary.com/dawjwfi88/image/upload/smartfridge/captured_images"
    
    return {
        "image_filename":f"{CLOUDINARY_BASE}/{latest_image.filename}",
        "masks": [
            {
                "name": mask.name,
                "mask_url": mask.mask_url
            }
            for mask in masks
        ]
    }
