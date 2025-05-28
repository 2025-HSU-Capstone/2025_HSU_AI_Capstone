# generation.py
# Flask 라우터 정의 파일
# /generate 라우트를 정의하고 외부 요청을 받음.
# POST 요청이 들어오오면 JSON을 파싱하고 generate_recipe_from_request() 함수에 전달.
# 그 결과를 그대로 jsonify()로 프론트에 응답함.

# 클라이언트가 /generate에 POST 요청 (user_input, ingredients 포함된 JSON)을 보냄.
# recipe_model.py의 generate_recipe_from_request()를 호출.
# 결과(JSON 형태의 레시피)를 받아 응답으로 반환.

from flask import Blueprint, jsonify, request
from recipe_model import generate_recipe_from_request
# 레시피 모델 함수화 함수 
generation_bp = Blueprint("generation", __name__)

@generation_bp.route("/generate", methods=["POST"])
def generate_recipe():
    print("🍳 /generate 요청 수신됨")
    try:
        user_input = request.get_json(force=True)  # user_input = dict 그대로
        result = generate_recipe_from_request(user_input)
        return jsonify(result)
    except Exception as e:
        import traceback
        print("❌ Flask /generate 예외 발생:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    # if user_input == "단백질 많은 레시피 추천해줘":
    #     return jsonify({
    #         "title": "단백질 폭탄 오믈렛",
    #         "ingredients": ingredients,
    #         "steps": [
    #             {"step": 1, "image_url": "/recipe-images/step1.png"},
    #             {"step": 2, "image_url": "/recipe-images/step2.png"}
    #         ]
    #     })
    # else:
    #     return jsonify({
    #         "title": "기본 감자계란전",
    #         "ingredients": ingredients,
    #         "steps": [
    #             {"step": 1, "image_url": "/recipe-images/step1.png"},
    #             {"step": 2, "image_url": "/recipe-images/step2.png"}
    #         ]
    #     })

