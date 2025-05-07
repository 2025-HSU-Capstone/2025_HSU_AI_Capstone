#swagger가 payload:dict만 하면 못 읽어서 형식 지정
# 1. 요청(Request body) 데이터의 구조 정의
#클라이언트(프론트엔드나 Swagger)가 보낼 JSON 데이터가 어떤 구조여야 하는지 정의해.
#FastAPI는 이 구조대로 데이터가 들어오면 자동으로 검증하고 파싱

# 2. Pydantic 모델로 타입 검증 및 문서화 지원
# BaseModel을 상속해서 만든 클래스는 JSON 구조를 명확하게 설명할 수 있어.

# Swagger 문서에서도 자동으로 스키마가 생성돼서 개발자가 구조를 쉽게 확인할 수 있음.

from pydantic import BaseModel
from datetime import datetime

class BBox(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int

class DetectedItem(BaseModel):
    name: str
    bbox: BBox

class DetectRequest(BaseModel):
    image_filename: str
    captured_at: datetime
    detected_items: list[DetectedItem]


#요청 바디(json)을 파이선 객체로 바꿔줘야하는데 그걸 자동으로 구조화해주는 Pydantic의 BaseModel 클래스
class RecipeRequest(BaseModel):
    user_input: str 
    