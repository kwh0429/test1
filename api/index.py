import os
import json
import logging
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

app = Flask(__name__)

def get_api_keys():
    g = (os.getenv("GEMINI_API_KEY") or "").strip().strip('"').strip("'")
    s = (os.getenv("SERPER_API_KEY") or "").strip().strip('"').strip("'")
    return g, s

def search_web_serper(query: str, serper_key: str) -> list:
    if not serper_key:
        return []
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": serper_key, "Content-Type": "application/json"}
    payload = {"q": query, "num": 5, "gl": "kr", "hl": "ko"}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        res.raise_for_status()
        data = res.json()
        return [{"title": item.get("title", ""), "snippet": item.get("snippet", "")} for item in data.get("organic", [])]
    except Exception:
        return []

def search_image_serper(device_name: str, serper_key: str) -> str:
    """기기의 대표 이미지를 구글 이미지 검색(Serper Images)으로 가져오는 함수"""
    if not serper_key:
        return ""
    url = "https://google.serper.dev/images"
    headers = {"X-API-KEY": serper_key, "Content-Type": "application/json"}
    payload = {"q": f"{device_name} official 누끼 제품", "num": 3, "gl": "kr"}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=8)
        res.raise_for_status()
        data = res.json()
        images = data.get("images", [])
        if images and len(images) > 0:
            return images[0].get("imageUrl", "")
    except Exception as e:
        logger.error(f"이미지 검색 실패: {e}")
    return ""

def generate_comparison_with_gemini(device_a: str, device_b: str, data_a: list, data_b: list, gemini_key: str) -> dict:
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel("gemini-flash-lite-latest")

    prompt = f"""
당신은 IT 기기 전문 리뷰어이자 분석가입니다.
아래 제공된 최신 검색 데이터와 기기 정보를 바탕으로, 두 IT 기기 '{device_a}'와 '{device_b}'를 비교 분석해 주세요.

[기기 A ({device_a}) 검색 데이터]
{json.dumps(data_a, ensure_ascii=False, indent=2)}

[기기 B ({device_b}) 검색 데이터]
{json.dumps(data_b, ensure_ascii=False, indent=2)}

반드시 아래 JSON 형식에 정확히 맞추어 응답해 주세요. 마크다운 코드 블록(```json 등) 없이 오직 순수 JSON 문자열만 출력해야 합니다.

{{
  "device_a": {{
    "name": "{device_a}",
    "price_range": "한국 출시가 또는 최신 시장 실거래 가격대 (원화 표기)",
    "specs": {{
      "processor": "프로세서(AP/CPU)",
      "display": "디스플레이 크기, 패널 종류, 주사율",
      "camera": "카메라 사양 요약",
      "battery": "배터리 용량 및 충전 스펙",
      "weight": "무게 및 휴대성"
    }},
    "pros": ["장점 1", "장점 2", "장점 3"],
    "cons": ["단점 1", "단점 2", "단점 3"],
    "review_summary": "실사용자 리뷰 핵심 요약 2~3줄"
  }},
  "device_b": {{
    "name": "{device_b}",
    "price_range": "한국 출시가 또는 최신 시장 실거래 가격대 (원화 표기)",
    "specs": {{
      "processor": "프로세서(AP/CPU)",
      "display": "디스플레이 크기, 패널 종류, 주사율",
      "camera": "카메라 사양 요약",
      "battery": "배터리 용량 및 충전 스펙",
      "weight": "무게 및 휴대성"
    }},
    "pros": ["장점 1", "장점 2", "장점 3"],
    "cons": ["단점 1", "단점 2", "단점 3"],
    "review_summary": "실사용자 리뷰 핵심 요약 2~3줄"
  }},
  "overall_verdict": {{
    "summary": "두 기기 총평 및 핵심 차이점 요약 (3~4줄)",
    "recommendation_a": "{device_a}를 추천하는 대상 유형",
    "recommendation_b": "{device_b}를 추천하는 대상 유형"
  }}
}}
"""
    res = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json", "temperature": 0.2}
    )
    return json.loads(res.text.strip())


@app.route("/", defaults={"path": ""}, methods=["GET", "POST"])
@app.route("/<path:path>", methods=["GET", "POST"])
def catch_all(path):
    # POST 요청은 무조건 기기 비교 수행
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        device_a = data.get("device_a", "").strip()
        device_b = data.get("device_b", "").strip()

        if not device_a or not device_b:
            return jsonify({"success": False, "error": "두 기기 이름을 모두 입력해 주세요."}), 400

        gemini_key, serper_key = get_api_keys()
        if not gemini_key or not serper_key:
            return jsonify({
                "success": False,
                "error": "Vercel Settings -> Environment Variables에 GEMINI_API_KEY와 SERPER_API_KEY를 등록해 주세요."
            }), 500

        search_a = search_web_serper(f"{device_a} 스펙 가격 장단점 리뷰", serper_key)
        search_b = search_web_serper(f"{device_b} 스펙 가격 장단점 리뷰", serper_key)

        # 각 기기의 대표 이미지 검색
        img_a = search_image_serper(device_a, serper_key)
        img_b = search_image_serper(device_b, serper_key)

        result = generate_comparison_with_gemini(device_a, device_b, search_a, search_b, gemini_key)
        
        # 이미지 URL 결과에 주입
        if "device_a" in result:
            result["device_a"]["image_url"] = img_a
        if "device_b" in result:
            result["device_b"]["image_url"] = img_b

        return jsonify({"success": True, "data": result})

    # GET 요청 시 메인 HTML 화면 직접 반환
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    html_path = os.path.join(base_dir, "templates", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read(), 200, {"Content-Type": "text/html; charset=utf-8"}
