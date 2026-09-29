import os
import json
import logging
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

app = Flask(__name__)
logger = logging.getLogger(__name__)

# 검증된 인기 IT 기기 실물/공식 CDN 이미지 프리셋 매핑
DEVICE_IMAGE_PRESETS = [
    # 스마트폰
    (["iphone 16", "아이폰 16"], "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=500&q=80"),
    (["iphone 15", "아이폰 15"], "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=500&q=80"),
    (["iphone 14", "아이폰 14"], "https://images.unsplash.com/photo-1663499482523-1c0c1bae4ce1?w=500&q=80"),
    (["iphone", "아이폰"], "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=500&q=80"),
    (["s24", "갤럭시 s24", "galaxy s24"], "https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=500&q=80"),
    (["s23", "갤럭시 s23", "galaxy s23"], "https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=500&q=80"),
    (["fold", "플립", "flip", "z fold", "z flip"], "https://images.unsplash.com/photo-1580910051074-3eb694886505?w=500&q=80"),
    (["galaxy", "갤럭시"], "https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=500&q=80"),
    (["pixel", "픽셀"], "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=500&q=80"),
    # 노트북 & 데스크톱
    (["macbook pro", "맥북 프로", "맥북프로"], "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500&q=80"),
    (["macbook", "맥북", "macbook air", "맥북 에어"], "https://images.unsplash.com/photo-1611186871348-b1ce696e52c9?w=500&q=80"),
    (["gram", "그램"], "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=500&q=80"),
    (["galaxy book", "갤럭시북", "갤럭시 북"], "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=500&q=80"),
    (["laptop", "노트북"], "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500&q=80"),
    # 태블릿
    (["ipad pro", "아이패드 프로", "아이패드프로"], "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=500&q=80"),
    (["ipad", "아이패드"], "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=500&q=80"),
    (["galaxy tab", "갤럭시탭", "갤럭시 탭"], "https://images.unsplash.com/photo-1561154464-82e9adf32764?w=500&q=80"),
    # 스마트워치 & 웨어러블
    (["apple watch", "애플워치", "애플 워치"], "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=500&q=80"),
    (["galaxy watch", "갤럭시 워치", "갤럭시워치"], "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&q=80"),
    (["watch", "워치"], "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&q=80"),
    # 이어폰 & 헤드폰
    (["airpods max", "에어팟 맥스"], "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=500&q=80"),
    (["airpods", "에어팟"], "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=500&q=80"),
    (["buds", "버즈"], "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=500&q=80"),
    (["headphone", "헤드폰"], "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&q=80"),
]

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
    """1. 키워드 매칭 프리셋 -> 2. 위키피디아 검색 API -> 3. Serper 구글 이미지 -> 4. 기본 IT 이미지"""
    d_clean = device_name.lower().replace(" ", "")

    # 1순위: 가장 정확하고 깨짐 없는 고화질 제품 사진 매핑
    for keywords, img_url in DEVICE_IMAGE_PRESETS:
        for kw in keywords:
            if kw.replace(" ", "") in d_clean:
                return img_url

    # 2순위: 위키피디아 검색 API (generator=search 방식이 단순 타이틀 조회보다 훨씬 정확함)
    for lang in ["ko", "en"]:
        try:
            wiki_url = (
                f"https://{lang}.wikipedia.org/w/api.php?action=query&generator=search"
                f"&gsrsearch={requests.utils.quote(device_name)}&gsrlimit=1"
                f"&prop=pageimages&piprop=original|thumbnail&pithumbsize=600&format=json"
            )
            res = requests.get(wiki_url, timeout=4, headers={"User-Agent": "TechComparator/1.0"})
            if res.status_code == 200:
                pages = res.json().get("query", {}).get("pages", {})
                for pid, pdata in pages.items():
                    orig = pdata.get("original", {}).get("source")
                    thumb = pdata.get("thumbnail", {}).get("source")
                    if orig or thumb:
                        return orig or thumb
        except Exception as e:
            logger.warning(f"위키피디아({lang}) 조회 패스: {e}")

    # 3순위: Serper 구글 이미지 검색 (Google Thumbnail 활용)
    if serper_key:
        try:
            url = "https://google.serper.dev/images"
            headers = {"X-API-KEY": serper_key, "Content-Type": "application/json"}
            payload = {"q": f"{device_name} official", "num": 5, "gl": "kr"}
            res = requests.post(url, headers=headers, json=payload, timeout=5)
            if res.status_code == 200:
                images = res.json().get("images", [])
                for img in images:
                    t_url = img.get("thumbnailUrl") or img.get("imageUrl")
                    if t_url and not t_url.endswith(".svg"):
                        return t_url
        except Exception as e:
            logger.error(f"구글 이미지 검색 패스: {e}")

    # 4순위: 범용 최신 테크 디바이스 고화질 이미지
    return "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500&q=80"

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
