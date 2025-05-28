# csv_updater.py
import pandas as pd
from datetime import datetime, timedelta
import os
from collections import Counter

# Rule 기반 맵핑
NUTRITION_MAP = {
    "마늘": "탄수화물",
    "감자": "탄수화물",
    "돼지고기": "단백질",
    "당근": "탄수화물",
    "양파": "탄수화물"
}

EXPIRY_DAYS = {
    "마늘": 10,
    "감자": 14,
    "돼지고기": 4,
    "당근": 12,
    "양파": 15
}

def generate_fooddataset_from_json(json_data: dict, csv_path: str):
    captured_at = json_data.get("captured_at")
    capture_date = datetime.fromisoformat(captured_at)

    items = json_data.get("detected_items", [])
    name_counts = Counter(item["name"] for item in items)

    rows = []
    for name, count in name_counts.items():
        nutrition = NUTRITION_MAP.get(name, "기타")
        expiry = capture_date + timedelta(days=EXPIRY_DAYS.get(name, 7))

        # ✅ 수량 로직: 2번 감지 시 → 1, 1번 감지 시 → 1
        quantity = count / 2 if count >= 2 else 1

        rows.append({
            "이름": name,
            "주요영양소": nutrition,
            "유통기한날짜": expiry.strftime("%Y-%m-%d"),
            "탐지일자": capture_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "수량": quantity
        })

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.to_csv(csv_path, index=False)
    print(f"✅ Saved to {csv_path}")
