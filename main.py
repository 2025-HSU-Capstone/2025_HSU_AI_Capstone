#React 웹페이지에서 요청을 보낼 거고
#FastAPI 백엔드는 요청을 처리하고 응답을 줄 거야

#JSON:	{ "이름": "값" } 형태로 데이터를 주고받는 형식 (FastAPI 기본 응답 방식)

# # 🎬 실제 상황처럼 비유하면…
# 너가 브라우저로 "문 열어주세요"라고 말했더니,
# FastAPI가 "안녕! Hello from FastAPI!"라고 대답해준 것이야!
# 너 = 요청자 (브라우저)
# FastAPI = 응답자 (서버)
# 대답 = JSON

print("✅ main.py 시작")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from starlette.responses import FileResponse
import os

from app.api.detect_updateDB_rout import router as detect_router
from app.api.generate_recipe_rout import router as generate_recipe_router
from app.api.bbox_recipe_rout import router as bbox_router
from app.api.trigger_router import router as trigger_router

from app.core import settings

# ✅ FastAPI 앱 생성
app = FastAPI(
    title="SmartFridge API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)
print("✅ FastAPI 인스턴스 생성 완료")

# ✅ CORS 허용 설정 (React용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 프론트 주소
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 정적 이미지에 CORS 허용 적용
class CORSEnabledStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
        return response

app.mount(
    "/images",
    CORSEnabledStaticFiles(directory=os.path.abspath("data/captured_images")),
    name="images"
)

# 신규 추가: 레시피 스텝 이미지용
app.mount(
    "/recipe_images",
    StaticFiles(directory=os.path.abspath("data/recipe_images")),
    name="recipe_images"
)


# ✅ 라우터 등록
app.include_router(detect_router)
app.include_router(generate_recipe_router)
app.include_router(bbox_router)
app.include_router(trigger_router)

print(f"📦 불러온 비밀번호 repr: {repr(settings.DB_PASSWORD)}")
print("✅ FastAPI 앱 시작됨")

from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print("🔥 예외 발생:", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

# ✅ 루트 페이지 확인용
@app.get("/")
def read_root():
    print("루트 라우터 실행됨")
    return {"message": "FastAPI는 살아있음"}


#http://127.0.0.1:8000/docs 
#uvicorn main:app --reload

#루트 페이지들 위미미
# http://127.0.0.1:8000/	루트 상태 확인 (read_root() 응답)
# http://127.0.0.1:8000/docs	Swagger API 문서 UI
# http://127.0.0.1:8000/openapi.json	API 스키마 JSON

# from PIL import Image
# img = Image.open("data/raw_images/fridge_sample_01.jpg")
# img.show()

# 실험할 때마다 삭제 삭제 안 해도 되는 테이블들
#:FoodLog FridgeImage DetectedBBox