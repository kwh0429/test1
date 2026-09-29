import os
import json
import logging
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai

# 로깅 설정 (콘솔에 자세한 실행 내역 출력)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# .env 파일로부터 환경 변수 로드
load_dotenv()

# 앞뒤 공백 및 보이지 않는 줄바꿈/특수문자 제거
GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or "").strip().strip('"').strip("'")
SERPER_API_KEY = (os.getenv("SERPER_API_KEY") or "").strip().strip('"').strip("'")

# API 키 유효성 사전 검사
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY가 .env 파일에 설정되지 않았습니다.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

app = Flask(
    __name__,
    template_folder=TEMPLATES_DIR,
    static_folder=STATIC_DIR
)

@app.route('/static/<path:filename>')
def serve_static(filename):
    from flask import send_from_directory
    return send_from_directory(STATIC_DIR, filename)


def search_web_serper(query: str, api_key: str = None) -> list:
    """Serper API를 호출하여 구글 실시간 검색 결과를 가져오는 함수"""
    active_key = api_key or (os.getenv("SERPER_API_KEY") or "").strip().strip('"').strip("'")
    if not active_key:
        logger.error("Serper API Key 누락으로 검색을 진행할 수 없습니다.")
        return []

    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": active_key,
        "Content-Type": "application/json"
    }
    payload = {
        "q": query,
        "num": 5,
        "gl": "kr",
        "hl": "ko"
    }

    try:
        logger.info(f"Serper API 검색 요청: '{query}'")
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        # 일반 유기적 검색 결과 추출
        for item in data.get("organic", []):
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "link": item.get("link", "")
            })
        logger.info(f"Serper 검색 완료: {len(results)}건 수집됨")
        return results
    except Exception as e:
        logger.error(f"Serper API 호출 중 오류 발생: {str(e)}")
        return []

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

def search_image_serper(device_name: str, serper_key: str = None) -> str:
    """1. 키워드 매칭 프리셋 -> 2. 위키피디아 검색 API -> 3. Serper 구글 이미지 -> 4. 기본 IT 이미지"""
    d_clean = device_name.lower().replace(" ", "")

    # 1순위: 가장 정확하고 깨짐 없는 고화질 제품 사진 매핑
    for keywords, img_url in DEVICE_IMAGE_PRESETS:
        for kw in keywords:
            if kw.replace(" ", "") in d_clean:
                return img_url

    # 2순위: 위키피디아 검색 API
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

    # 3순위: Serper 구글 이미지 검색
    active_key = serper_key or (os.getenv("SERPER_API_KEY") or "").strip().strip('"').strip("'")
    if active_key:
        try:
            url = "https://google.serper.dev/images"
            headers = {"X-API-KEY": active_key, "Content-Type": "application/json"}
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

    return "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500&q=80"


def generate_comparison_with_gemini(device_a: str, device_b: str, search_data_a: list, search_data_b: list) -> dict:
    """Gemini 모델을 호출하여 두 기기의 스펙 및 검색 데이터를 바탕으로 대조 결과를 JSON으로 생성하는 함수"""
    if not GEMINI_API_KEY:
        raise ValueError("Gemini API Key가 설정되지 않았습니다.")

    # 무료 한도(Quota)가 넉넉하고 빠른 Flash Lite 최신 모델 사용
    model = genai.GenerativeModel("gemini-flash-lite-latest")

    # 프롬프트 구성
    prompt = f"""
당신은 IT 기기 전문 리뷰어이자 분석가입니다.
아래 제공된 최신 검색 데이터와 기기 정보를 바탕으로, 두 IT 기기 '{device_a}'와 '{device_b}'를 비교 분석해 주세요.

[기기 A ({device_a}) 검색 데이터]
{json.dumps(search_data_a, ensure_ascii=False, indent=2)}

[기기 B ({device_b}) 검색 데이터]
{json.dumps(search_data_b, ensure_ascii=False, indent=2)}

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
    "beginner_analogy": "IT 초보자를 위해 자동차, 운동선수, 책상 등 일상 생활에 빗대어 두 기기의 성격과 체감 차이를 아주 쉽고 재미있게 설명한 2~3줄 비유",
    "recommendation_a": "{device_a}를 추천하는 대상 유형",
    "recommendation_b": "{device_b}를 추천하는 대상 유형"
  }}
}}
"""

    logger.info("Gemini 모델에 비교 분석 프롬프트 전송 시작")
    response = model.generate_content(
        prompt,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.2
        }
    )
    logger.info("Gemini 응답 수신 완료")

    response_text = response.text.strip()
    # 순수 JSON 파싱
    parsed_json = json.loads(response_text)
    return parsed_json


@app.route("/")
@app.route("/api/index")
def index():
    """메인 화면 페이지 렌더링"""
    return render_template("index.html")


@app.route("/compare", methods=["POST"])
@app.route("/api/compare", methods=["POST"])
def compare():
    """기기 비교 비동기 요청 처리 라우트"""
    try:
        data = request.get_json() or {}
        device_a = data.get("device_a", "").strip()
        device_b = data.get("device_b", "").strip()

        logger.info(f"비교 요청 접수: 기기 A='{device_a}', 기기 B='{device_b}'")

        # Vercel 서버리스 환경을 위한 최신 환경변수 동적 로드
        g_key = (os.getenv("GEMINI_API_KEY") or "").strip().strip('"').strip("'")
        s_key = (os.getenv("SERPER_API_KEY") or "").strip().strip('"').strip("'")

        if not device_a or not device_b:
            return jsonify({
                "success": False,
                "error": "두 기기 이름을 모두 입력해 주세요."
            }), 400

        if not s_key or not g_key:
            return jsonify({
                "success": False,
                "error": "Vercel 대시보드의 Settings -> Environment Variables에 GEMINI_API_KEY와 SERPER_API_KEY가 등록되어 있는지 확인해 주세요."
            }), 500

        # 구글 AI 최신 키로 재구성
        genai.configure(api_key=g_key)

        # 2. Serper API로 기기 A와 B 최신 정보 검색
        query_a = f"{device_a} 스펙 가격 장단점 리뷰"
        query_b = f"{device_b} 스펙 가격 장단점 리뷰"

        search_results_a = search_web_serper(query_a)
        search_results_b = search_web_serper(query_b)

        # 3. Gemini Flash 모델로 데이터 분석 및 구조화
        comparison_result = generate_comparison_with_gemini(
            device_a=device_a,
            device_b=device_b,
            search_data_a=search_results_a,
            search_data_b=search_results_b
        )

        # 4. 각 기기 대표 이미지 검색 및 주입
        img_a = search_image_serper(device_a, s_key)
        img_b = search_image_serper(device_b, s_key)

        if "device_a" in comparison_result:
            comparison_result["device_a"]["image_url"] = img_a
        if "device_b" in comparison_result:
            comparison_result["device_b"]["image_url"] = img_b

        return jsonify({
            "success": True,
            "data": comparison_result
        })

    except json.JSONDecodeError as json_err:
        logger.error(f"JSON 파싱 실패: {str(json_err)}")
        return jsonify({
            "success": False,
            "error": "AI 응답 결과를 데이터로 변환하는 중 오류가 발생했습니다. 다시 시도해 주세요."
        }), 500
    except Exception as e:
        logger.error(f"비교 처리 중 예기치 못한 오류 발생: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"처리 중 오류가 발생했습니다: {str(e)}"
        }), 500


if __name__ == "__main__":
    logger.info("Flask AI IT Device Comparator 서버 시작 (http://127.0.0.1:5000)")
    app.run(host="127.0.0.1", port=5000, debug=True)
