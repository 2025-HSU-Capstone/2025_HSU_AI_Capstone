import cloudinary
import cloudinary.api
import cloudinary.uploader
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

def delete_all_in_folder(folder_path):
    try:
        # ✅ recipe_images 하위의 전체 assets 목록 가져오기
        resources = cloudinary.api.resources(type="upload", prefix=folder_path, max_results=100)

        for item in resources.get("resources", []):
            public_id = item["public_id"]
            print(f"❌ 삭제 중: {public_id}")
            cloudinary.uploader.destroy(public_id)

        print("✅ 삭제 완료.")
    except Exception as e:
        print("⚠️ 삭제 중 오류 발생:", e)

# 사용 예:
delete_all_in_folder("smartfridge/recipe_images")
