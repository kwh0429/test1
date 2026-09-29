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


def search_web_serper(query: str) -> list:
    """Serper API를 호출하여 구글 실시간 검색 결과를 가져오는 함수"""
    if not SERPER_API_KEY:
        logger.error("Serper API Key 누락으로 검색을 진행할 수 없습니다.")
        return []

    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": SERPER_API_KEY,
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

        # 1. 입력값 검증 (두 기기명 모두 필수)
        if not device_a or not device_b:
            return jsonify({
                "success": False,
                "error": "두 기기 이름을 모두 입력해 주세요."
            }), 400

        if not SERPER_API_KEY or not GEMINI_API_KEY:
            return jsonify({
                "success": False,
                "error": ".env 파일에 GEMINI_API_KEY와 SERPER_API_KEY가 올바르게 설정되어 있는지 확인해 주세요."
            }), 500

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
