import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
print("📦 불러온 API KEY:", OPENAI_API_KEY) 

#단순히 환경변수들을 파이썬 변수로 정리해주는 역할
#.env를 읽고 파이썬 코드에서 사용할 수 있게 변수화




#load_dotenv()  # .env 파일 불러오기 # 실행 위치가 루트면 자동으로 ../.env 찾음

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

#SQLAlchemy가 MySQL에 연결할 때 쓰는 URL 문자열
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
