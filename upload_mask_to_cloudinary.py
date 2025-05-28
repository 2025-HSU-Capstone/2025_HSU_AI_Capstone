# 더미 마스크 업로드(로컬->cloudinary)

import cloudinary
import cloudinary.uploader
from PIL import Image
import io
import os

# Cloudinary 설정 (.env 안 쓰는 버전)
cloudinary.config(
    cloud_name="dawjwfi88",
    api_key="737816378397999",
    api_secret="P_JWtRHUKXXiy3MuGLzUpsBAADc",
    secure=True
)

def upload_mask_image(image_path: str, public_id: str) -> str:
    with Image.open(image_path) as img:
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        buffered.seek(0)

        folder_path, filename = public_id.rsplit("/", 1)

        result = cloudinary.uploader.upload(
            buffered,
            folder=folder_path,
            public_id=filename,
            overwrite=True,
            resource_type="image"
        )

        print(f"✅ 업로드 완료: {result['secure_url']}")
        return result["secure_url"]

if __name__ == "__main__":
    ingredients = [
        "돼지고기", "소고기", "닭고기", "사과", "파",
        "마늘", "양파", "감자", "계란", "치즈"
    ]

    uploaded = {}

    for name in ingredients:
        local_path = f"./data/mask_images/mask_{name}.png"  # 현재 파일과 같은 폴더에 둘 경우
        public_id = f"smartfridge/mask_images/{name}_mask"
        try:
            url = upload_mask_image(local_path, public_id)
            uploaded[name] = url
        except Exception as e:
            print(f"❌ {name} 업로드 실패:", e)

    print("\n📦 업로드된 URL 목록:")
    for k, v in uploaded.items():
        print(f"{k}: {v}")
