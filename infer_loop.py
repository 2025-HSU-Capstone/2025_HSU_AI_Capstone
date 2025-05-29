import os
import time
import json
from detector import run_inference
from sender import send_to_flask

# ✅ 설정
INCOMING_IMAGE = "/home/elicer/AI_capstone/incoming/capture_combined.jpg"
SLEEP_TIME = 2  # seconds

# ✅ 전송 대상 서버 리스트 (딕셔너리 리스트로 수정)
SERVER_TARGETS = [
    {"url": "https://8d48-223-194-128-40.ngrok-free.app/process_detection", "method": "POST"}, # <-- 변경된 URL
    {"url": "https://a157-223-194-128-40.ngrok-free.app/detect", "method": "POST"}             # <-- 변경된 URL
]

print("🔄 GPU 추론 서버 시작. Ctrl+C로 종료 가능.")

try:
    while True:
        if os.path.exists(INCOMING_IMAGE):
            print("🖼️ 새 이미지 감지됨. 추론 시작...")

            try:
                result = run_inference(INCOMING_IMAGE)

                # ✅ 전송 전 구조 확인
                print("🔎 전송 직전 JSON 구조:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                print("🔍 각 detected_item 타입 확인:")
                for i, item in enumerate(result.get("detected_items", [])):
                    print(f"  [{i}] {type(item)} → {item if isinstance(item, str) else item.get('name')}")

                # ✅ 서버로 전송
                send_results = send_to_flask(result, SERVER_TARGETS)

                if all(send_results.values()):
                    os.remove(INCOMING_IMAGE)
                    print("🧹 이미지 삭제 완료. 다음 캡처 대기 중...")
                else:
                    print("⚠️ 일부 서버 전송 실패. 이미지 삭제 보류.")

            except Exception as e:
                print(f"❌ 처리 중 오류 발생: {e}")

        time.sleep(SLEEP_TIME)

except KeyboardInterrupt:
    print("🛑 수동 종료됨.")