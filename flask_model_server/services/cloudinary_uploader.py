import cloudinary
import cloudinary.uploader
import io
import os
from dotenv import load_dotenv

# .env 파일 불러오기
load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

# 레시피 만들기 위해 만든 파일
# 근데 공통으로 쓸 수 있게 만든 범용 업로드 함수임임
def upload_to_cloudinary_from_bytes(image, public_id: str) -> str:
    """
    PIL 이미지 객체를 Cloudinary에 업로드하고 URL 반환
    """
    # 1. 이미지 → BytesIO
    # 
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    buffered.seek(0)

    # 🔥 public_id를 파일명으로 분리
    folder_path, filename = public_id.rsplit("/", 1)

    # 2. Cloudinary 업로드
    result = cloudinary.uploader.upload(
        buffered,
        folder=folder_path,   # 👈 여기 명시적으로 설정
        public_id=filename,
        overwrite=True,
        resource_type="image"
    )
    print("📛 실제 public_id:", result["public_id"])

    return result["secure_url"]


