from app.models.db_tables import Base
from app.db.database import engine

# 모든 테이블 삭제
#Base.metadata.drop_all(bind=engine)

# 다시 생성
# Base.metadata.create_all(bind=engine)

#모든 테이블의 행 삭제제

# reset.py
