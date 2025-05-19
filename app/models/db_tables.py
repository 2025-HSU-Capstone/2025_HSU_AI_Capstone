# models/db_tables.py
#FastAPI가 MySQL DB랑 연결할 때 쓰는 '설명서' 같은 것이야.
#즉, 모델 = DB 테이블과 연결되는 Python 클래스

#FastAPI ↔ MySQL	이 모델이 있어야 FastAPI가 DB에 insert, query, delete 등을 할 수 있어
#React ↔ FastAPI	프론트는 FastAPI에 요청만 하고, FastAPI는 이 모델을 이용해 DB에서 꺼냄


from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy import Text

Base = declarative_base()


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    user_input = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    # 즉, DB에서는 외래키만 설정해도 되지만,
    # VSCode에서 Python 코드로 객체 간 관계를 다루기 위해서는
    # relationship()을 설정
    ingredients = relationship("RecipeIngredient", back_populates="recipe")
    images = relationship("RecipeImage", back_populates="recipe")


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    name = Column(String(100), nullable=False)

    recipe = relationship("Recipe", back_populates="ingredients")


class RecipeImage(Base):
    __tablename__ = "recipe_images"

    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    step = Column(Text)
    image_url = Column(String(255))

    recipe = relationship("Recipe", back_populates="images")


class FridgeImage(Base):
    __tablename__ = "fridge_images"

    id = Column(Integer, primary_key=True)
    filename = Column(String(255))
    captured_at = Column(DateTime, default=datetime.utcnow)

    food_items = relationship("FoodItem", back_populates="image")
    food_logs = relationship("FoodLog", back_populates="image")
    bboxes = relationship("DetectedBBox", back_populates="image")


class FoodItem(Base):
    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    detected_at = Column(DateTime, default=datetime.utcnow)
    image_id = Column(Integer, ForeignKey("fridge_images.id"))

    image = relationship("FridgeImage", back_populates="food_items")


class FoodLog(Base):
    __tablename__ = "food_logs"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    status = Column(Enum("in", "out", name="food_status"))
    changed_at = Column(DateTime, default=datetime.utcnow)
    image_id = Column(Integer, ForeignKey("fridge_images.id"))

    image = relationship("FridgeImage", back_populates="food_logs")


class DetectedBBox(Base):
    __tablename__ = "detected_bboxes"

    id = Column(Integer, primary_key=True)
    image_id = Column(Integer, ForeignKey("fridge_images.id"))
    name = Column(String(100))
    x1 = Column(Float)
    y1 = Column(Float)
    x2 = Column(Float)
    y2 = Column(Float)

    image = relationship("FridgeImage", back_populates="bboxes")
