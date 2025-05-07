#SQLAlchemy와 MySQL을 연결하고, DB 세션을 관리하는 핵심 설정 파일
#settings.py를 불러와서 사용

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.settings import SQLALCHEMY_DATABASE_URL
#반드시 절대경로 import로 접근
#상대 경로 import는 단독 실행에서는 안 되고, 모듈로 실행할 때만 돼"

#engine: DB와의 실제 연결 객체
#SessionLocal: DB에 접속할 수 있는 “세션 팩토리” (한 요청에 하나씩 연결해서 쓰기 위한 준비)
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

#모든 테이블 모델이 상속받는 기본 클래스
#db_tables.py 안에서 테이블 정의할 때 class FoodItem(Base)처럼 이걸 상속받게 되어 있음
Base = declarative_base()

# DB 세션 제공 함수
#FastAPI에서 의존성 주입으로 Depends(get_db)로 쓰는 함수
#요청마다 새로운 DB 세션을 만들고, 작업이 끝나면 finally로 안전하게 닫아줌
def get_db():
    db = SessionLocal() #DB에 연결할 수 있는 세션(연결 객체)을 하나 생성
    try:
        yield db #FastAPI가 이 함수를 호출한 라우터 함수에 이 db 세션을 넘겨줌
    finally:
        db.close()




#main.py → FastAPI 앱 실행 시 DB 연결됨
#reset.py 같은 초기화 파일 → Base.metadata.create_all(bind=engine)로 DB 생성
#routes/*.py → API 실행할 때마다 Depends(get_db)로 세션 열고 사용
#db_tables.py → Base를 상속해서 테이블 정의함