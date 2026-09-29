from http.server import BaseHTTPRequestHandler
import json
import os
import requests
import google.generativeai as genai

# Vercel 환경에서 직접 실행되는 단일 독립 Serverless Handler
class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        # templates/index.html 읽어서 서빙
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        html_path = os.path.join(base_dir, "templates", "index.html")

        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"index.html not found")

    def do_POST(self):
        # /compare 또는 /api/compare 요청 처리
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            req_json = json.loads(post_data) if post_data else {}

            device_a = req_json.get("device_a", "").strip()
            device_b = req_json.get("device_b", "").strip()

            if not device_a or not device_b:
                self._send_json({"success": False, "error": "두 기기 이름을 모두 입력해 주세요."}, 400)
                return

            gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip().strip('"').strip("'")
            serper_key = (os.getenv("SERPER_API_KEY") or "").strip().strip('"').strip("'")

            if not gemini_key or not serper_key:
                self._send_json({
                    "success": False,
                    "error": "Vercel 대시보드의 Settings -> Environment Variables에 GEMINI_API_KEY와 SERPER_API_KEY가 등록되어 있는지 확인해 주세요."
                }, 500)
                return

            # Serper 실시간 검색
            search_a = self._search_serper(f"{device_a} 스펙 가격 장단점 리뷰", serper_key)
            search_b = self._search_serper(f"{device_b} 스펙 가격 장단점 리뷰", serper_key)

            # Gemini 분석
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-flash-lite-latest")

            prompt = f"""
당신은 IT 기기 전문 리뷰어이자 분석가입니다.
아래 제공된 최신 검색 데이터와 기기 정보를 바탕으로, 두 IT 기기 '{device_a}'와 '{device_b}'를 비교 분석해 주세요.

[기기 A ({device_a}) 검색 데이터]
{json.dumps(search_a, ensure_ascii=False, indent=2)}

[기기 B ({device_b}) 검색 데이터]
{json.dumps(search_b, ensure_ascii=False, indent=2)}

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
            ai_res = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json", "temperature": 0.2}
            )
            parsed = json.loads(ai_res.text.strip())
            self._send_json({"success": True, "data": parsed}, 200)

        except Exception as e:
            self._send_json({"success": False, "error": f"처리 중 오류: {str(e)}"}, 500)

    def _search_serper(self, query, api_key):
        try:
            url = "https://google.serper.dev/search"
            headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
            payload = {"q": query, "num": 5, "gl": "kr", "hl": "ko"}
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            data = res.json()
            return [{"title": i.get("title", ""), "snippet": i.get("snippet", "")} for i in data.get("organic", [])]
        except Exception:
            return []

    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
