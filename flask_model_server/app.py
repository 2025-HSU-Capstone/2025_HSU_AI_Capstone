# from flask import Flask, send_from_directory
# from detection import detection_bp
# from generation import generation_bp

# app = Flask(__name__)

# # 블루프린트 등록
# app.register_blueprint(detection_bp, url_prefix="/api")
# app.register_blueprint(generation_bp, url_prefix="/api")

# # ✅ 이미지 파일 서빙용 엔드포인트 추가
# @app.route('/recipe-images/<path:filename>')
# def serve_image(filename):
#     return send_from_directory("outputs", filename)

# # ✅ 서버 실행
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)

from flask import Flask
from generation import generation_bp

app = Flask(__name__)
app.register_blueprint(generation_bp, url_prefix="/api")

@app.route("/")
def index():
    return "✅ 서버 정상 작동 중!"

if __name__ == "__main__":
    app.run(debug=True)
