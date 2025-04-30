# 🍱 스마트 냉장고 RAG 기반 레시피 추천 시스템

이 프로젝트는 사용자의 요청에 따라
- 식재료를 필터링하고,
- 유사 레시피를 검색하여,
- GPT를 통해 현실적이고 맛있는 요리를 추천하는
스마트 냉장고용 RAG 기반 AI 시스템입니다.

---

## 📁 프로젝트 구조

```
AI_System_Capstone/
├── rag_index_builder.py           # recipes1_rag_ready.csv를 벡터 DB로 인덱싱
├── user_request.py                # 사용자 자연어 요청으로부터 식재료 조건 추출
├── recipe_generator_rag.py       # 추출된 식재료로 레시피 추천
├── run_user_request.sh           # 전체 자동 실행 스크립트 (user_request + 추천)
├── data/
│   ├── recipes1_rag_ready.csv     # 벡터 DB용 정제된 레시피 문서
│   └── filtered_ingredients.csv   # user_request.py 실행 결과 저장 파일
└── db/
    └── chroma/                    # Chroma 벡터 DB 저장 디렉토리 (자동 생성)
```

---

## 🔁 실행 흐름

1. `user_request.py` 실행
   - 예: "오늘은 단백질이 많은 음식을 먹고싶어"
   - GPT가 조건 추출 → `filtered_ingredients.csv`에 저장

2. `recipe_generator_rag.py` 실행
   - `filtered_ingredients.csv` 불러오기
   - Chroma 벡터 DB에서 유사 레시피 검색
   - GPT에게 컨텍스트로 전달해 현실적 레시피 생성

3. 또는 아래처럼 한 번에 실행:
```bash
./run_user_request.sh
```

---

## 💡 RAG 구성
- 💬 사용자 입력 → GPT 기반 키워드 추출
- 📦 정제된 CSV → Chroma DB로 임베딩
- 🔍 유사 레시피 3개 검색
- 🧠 GPT-4-Turbo에 컨텍스트로 전달해 요리 추천

---

## 🛠️ 설치 필요 패키지
- `sentence-transformers`
- `chromadb`
- `openai`
- `python-dotenv`
- `pandas`

```bash
pip install -r requirements.txt
```

(또는 수동 설치)
```bash
pip install openai chromadb sentence-transformers python-dotenv pandas
```

---

## 🔒 API 키 관리
- `.env` 파일을 프로젝트 루트에 생성하고:

```
OPENAI_API_KEY=sk-xxxxxxx...
```

- `.env`는 `.gitignore`에 반드시 포함할 것!

---

## 📌 향후 통합 계획
- 현재는 local CLI 기반
- 추후 FastAPI 기반 REST API 서버로 확장 예정
- 프론트엔드와 연동해 웹 UI로 서비스화 가능

---

문의: [heohyeonjun@yourdomain.com] (예시)

---

🎉 **Enjoy Cooking with Smart AI!**

