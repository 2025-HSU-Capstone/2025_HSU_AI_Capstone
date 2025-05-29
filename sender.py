import aiohttp
import asyncio
import json

# ✅ 서버에 하나씩 전송 (GET 또는 POST)
async def send_one(session, target, json_data):
    url = target["url"]
    method = target.get("method", "POST").upper()

    try:
        if method == "POST":
            async with session.post(url, json=json_data, timeout=10) as response:
                if response.status == 200:
                    print(f"✅ POST 성공: {url}")
                    return (url, True)
                else:
                    print(f"❌ POST 실패 {url}: {response.status}")
                    return (url, False)

        elif method == "GET":
            async with session.get(url, params=json_data, timeout=10) as response:
                if response.status == 200:
                    print(f"✅ GET 성공: {url}")
                    return (url, True)
                else:
                    print(f"❌ GET 실패 {url}: {response.status}")
                    return (url, False)

        else:
            print(f"❌ 지원되지 않는 메서드: {method}")
            return (url, False)

    except Exception as e:
        print(f"❌ 전송 중 오류 발생: {url} [{method}] → {e}")
        return (url, False)

# ✅ 병렬 전송
async def send_to_multiple_flask_async(json_data: dict, server_targets: list[dict]):
    async with aiohttp.ClientSession() as session:
        tasks = [send_one(session, target, json_data) for target in server_targets]
        results = await asyncio.gather(*tasks)
        return dict(results)

# ✅ 동기 래퍼 함수 (외부에서 import해서 사용)
def send_to_flask(json_data: dict, server_targets: list[dict]) -> dict:
    result = asyncio.run(send_to_multiple_flask_async(json_data, server_targets))
    print("\n📤 전체 전송 결과:")
    for url, success in result.items():
        status = "✅ 성공" if success else "❌ 실패"
        print(f" - {url}: {status}")
    return result