# reset_recipe_data.py

from sqlalchemy import text
from app.db.database import SessionLocal

def reset_recipe_tables():
    db = SessionLocal()
    try:
        print("🔄 레시피 관련 테이블 초기화 중...")

        # 삭제 → AUTO_INCREMENT 리셋 순서 중요
        db.execute(text("DELETE FROM recipe_images"))
        db.execute(text("DELETE FROM recipe_ingredients"))
        db.execute(text("DELETE FROM recipes"))

        db.execute(text("ALTER TABLE recipe_images AUTO_INCREMENT = 1"))
        db.execute(text("ALTER TABLE recipe_ingredients AUTO_INCREMENT = 1"))
        db.execute(text("ALTER TABLE recipes AUTO_INCREMENT = 1"))

        db.commit()
        print("✅ 레시피 데이터 초기화 및 id 리셋 완료.")
    except Exception as e:
        db.rollback()
        print("❌ 오류 발생:", e)
    finally:
        db.close()

if __name__ == "__main__":
    reset_recipe_tables()
