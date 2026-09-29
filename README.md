# ⚡ AI IT Device Comparator (AI IT 기기 스펙 & 가격 대조기)

> 비교하고 싶은 IT 기기 2종을 입력하면, 실시간 구글 웹 검색(Serper API)과 최신 생성형 AI(Google Gemini)가 핵심 스펙, 최신 시장 실거래 가격대, 장단점 및 사용자 리뷰를 한눈에 대조해 주는 풀스택 웹 애플리케이션입니다.

---

## 🌟 주요 기능 (Key Features)

1. **실시간 최신 웹 검색 (Serper API)**:
   - 두 기기에 대한 최신 출시 가격, 오픈마켓 실거래 가격대, 블로그 및 커뮤니티 실사용자 리뷰를 실시간으로 크롤링/수집합니다.
2. **최신 생성형 AI 분석 (Google Gemini Flash Lite)**:
   - 수집된 웹 데이터를 정밀 분석하여 프로세서, 디스플레이, 카메라, 배터리, 무게 등의 핵심 스펙을 정형화된 데이터로 추출합니다.
3. **직관적인 2열 대조 비교 표 (Comparison Table)**:
   - 기기 A(블루)와 기기 B(그린)의 스펙과 가격을 한눈에 알아볼 수 있도록 깔끔한 대조 테이블로 렌더링합니다.
   - 장점(✓)과 단점(✕)을 시각적으로 대비하여 스마트한 구매 결정을 지원합니다.
4. **AI 종합 총평 및 맞춤 추천 가이드**:
   - 두 기기의 핵심 차이점 요약 및 "어떤 사용자에게 어떤 기기가 더 적합한지" 구매 추천 대상을 명확히 제시합니다.
5. **결과 복사 & 마크다운(.md) 파일 다운로드**:
   - 생성된 비교 대조 보고서를 클릭 한 번으로 클립보드에 복사하거나 마크다운 파일로 다운로드하여 소장할 수 있습니다.
6. **철저한 보안 관리**:
   - API Key 등 민감 정보는 `.env`로 격리하여 GitHub 버전 관리에서 안전하게 제외됩니다.

---

## 🛠 기술 스택 (Tech Stack)

| 구분 | 기술 스택 |
| :--- | :--- |
| **Backend** | Python 3.10+, Flask, python-dotenv, requests |
| **AI / Search** | Google Gemini API (gemini-flash-lite-latest), Serper API |
| **Frontend** | Vanilla JavaScript (ES6+ Fetch API), HTML5, CSS3 (Modern Responsive Flex/Grid) |
| **Version Control**| Git, GitHub |

---

## 📂 프로젝트 구조 (Project Structure)

```text
tech-comparator/
├── app.py                  # Flask 백엔드 서버 & Serper/Gemini 연동 로직
├── requirements.txt        # 프로젝트 필수 라이브러리 목록
├── .env                    # 비밀 API Key 보관 파일 (Git 추적 제외)
├── .env.example            # 환경변수 템플릿 파일
├── .gitignore              # Git 제외 규칙 (보안 및 가상환경 격리)
├── README.md               # 프로젝트 상세 설명 문서
├── templates/
│   └── index.html          # 메인 반응형 웹 화면 템플릿
└── static/
    ├── css/
    │   └── style.css       # 모던 2열 대조 표 및 테마 스타일시트
    └── js/
        └── app.js          # 비동기 요청, DOM 동적 렌더링, 복사/다운로드 기능
```

---

## 🚀 빠른 시작 가이드 (Quick Start)

### 1. 저장소 클론 (Clone)
```bash
git clone https://github.com/kwh0429/test1.git
cd test1
```

### 2. 가상환경 생성 및 활성화
```powershell
# 가상환경 생성
py -m venv venv

# 가상환경 활성화 (Windows PowerShell 기준)
.\venv\Scripts\Activate.ps1
```

### 3. 필수 패키지 설치
```bash
py -m pip install -r requirements.txt
```

### 4. 환경 변수(.env) 설정
프로젝트 루트 경로에 `.env` 파일을 생성하고 본인의 API 키를 입력합니다:
```env
GEMINI_API_KEY=your_google_gemini_api_key_here
SERPER_API_KEY=your_serper_dev_api_key_here
```
- [Google AI Studio](https://aistudio.google.com/apikey)에서 Gemini API 키 무료 발급
- [Serper.dev](https://serper.dev)에서 Google Search API 키 무료 발급

### 5. 웹 서버 실행
```bash
py app.py
```
실행 후 브라우저에서 `http://127.0.0.1:5000`으로 접속하여 원하는 기기 2종을 입력해 보세요!

---

## 📄 라이선스 (License)
This project is open-source and available under the MIT License.
