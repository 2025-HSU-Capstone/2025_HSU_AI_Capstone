from flask import Flask
from generation import generation_bp
from detection import bp as detection_bp  # ✅ 추가

app = Flask(__name__)
app.register_blueprint(generation_bp, url_prefix="/api")
app.register_blueprint(detection_bp)  # /process_detection

@app.route("/")
def index():
    return "✅ 서버 정상 작동 중!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)  # ✅ 외부 접근 허용
