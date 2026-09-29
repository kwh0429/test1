// ==========================================================
// AI IT Device Comparator 클라이언트 스크립트 (app.js)
// ==========================================================

document.addEventListener("DOMContentLoaded", () => {
    // 1. 주요 DOM 엘리먼트 참조
    const compareForm = document.getElementById("compare-form");
    const deviceAInput = document.getElementById("device-a");
    const deviceBInput = document.getElementById("device-b");
    const submitBtn = document.getElementById("submit-btn");

    const loadingSection = document.getElementById("loading-section");
    const errorBox = document.getElementById("error-box");
    const errorMessage = document.getElementById("error-message");
    const resultSection = document.getElementById("result-section");

    const copyBtn = document.getElementById("copy-btn");
    const downloadBtn = document.getElementById("download-btn");

    // 초보자 모드 및 비유 사전 DOM 엘리먼트
    const beginnerToggleBtn = document.getElementById("beginner-toggle-btn");
    const beginnerModeStatus = document.getElementById("beginner-mode-status");
    const dictionaryBtn = document.getElementById("dictionary-btn");
    const dictionaryModal = document.getElementById("dictionary-modal");
    const modalCloseBtn = document.getElementById("modal-close-btn");
    const modalOkBtn = document.getElementById("modal-ok-btn");
    const beginnerAnalogyCard = document.getElementById("beginner-analogy-card");
    const beginnerAnalogyText = document.getElementById("beginner-analogy-text");
    const tableContainer = document.querySelector(".table-container");

    let isBeginnerMode = false;

    // 초보자 쉬운 모드 토글 이벤트
    if (beginnerToggleBtn) {
        beginnerToggleBtn.addEventListener("click", () => {
            isBeginnerMode = !isBeginnerMode;
            beginnerToggleBtn.classList.toggle("active", isBeginnerMode);
            if (beginnerModeStatus) beginnerModeStatus.textContent = isBeginnerMode ? "ON" : "OFF";
            
            if (tableContainer) {
                tableContainer.classList.toggle("beginner-mode-active", isBeginnerMode);
            }

            if (beginnerAnalogyCard && currentComparisonData && currentComparisonData.overall_verdict && currentComparisonData.overall_verdict.beginner_analogy) {
                if (isBeginnerMode) {
                    beginnerAnalogyCard.classList.remove("hidden");
                    beginnerAnalogyCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
                } else {
                    beginnerAnalogyCard.classList.add("hidden");
                }
            }
        });
    }

    // IT 비유 사전 모달 열기/닫기 이벤트
    if (dictionaryBtn && dictionaryModal) {
        dictionaryBtn.addEventListener("click", () => {
            dictionaryModal.classList.remove("hidden");
        });

        const closeModal = () => {
            dictionaryModal.classList.add("hidden");
        };

        if (modalCloseBtn) modalCloseBtn.addEventListener("click", closeModal);
        if (modalOkBtn) modalOkBtn.addEventListener("click", closeModal);
        dictionaryModal.addEventListener("click", (e) => {
            if (e.target === dictionaryModal) closeModal();
        });
    }

    // 최신 비교 결과를 저장할 전역 변수
    let currentComparisonData = null;

    // 2. 폼 제출 이벤트 핸들러
    compareForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const deviceA = deviceAInput.value.trim();
        const deviceB = deviceBInput.value.trim();

        // 프론트엔드 유효성 검증
        if (!deviceA || !deviceB) {
            showError("비교할 두 기기의 이름을 모두 입력해 주세요.");
            return;
        }

        // UI 상태 초기화 및 로딩 시작
        hideError();
        resultSection.classList.add("hidden");
        loadingSection.classList.remove("hidden");
        submitBtn.disabled = true;
        submitBtn.querySelector(".btn-text").textContent = "⏳ 실시간 검색 및 분석 중...";

        try {
            // 백엔드 /compare API 호출
            const response = await fetch("/compare", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    device_a: deviceA,
                    device_b: deviceB
                })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || "비교 분석 중 오류가 발생했습니다.");
            }

            // 결과 렌더링
            currentComparisonData = data.data;
            renderComparison(currentComparisonData);

            // 로딩 종료 및 결과 화면 표시
            loadingSection.classList.add("hidden");
            resultSection.classList.remove("hidden");
            resultSection.scrollIntoView({ behavior: "smooth" });

        } catch (err) {
            console.error("비교 요청 실패:", err);
            loadingSection.classList.add("hidden");
            showError(err.message || "서버와 통신하는 중 문제가 발생했습니다. 잠시 후 다시 시도해 주세요.");
        } finally {
            submitBtn.disabled = false;
            submitBtn.querySelector(".btn-text").textContent = "🔍 두 기기 실시간 비교하기";
        }
    });

    // 기기별 스마트 비주얼 생성 함수 (고화질 이미지 + 로드 실패 시 글래스모피즘 테크 뱃지 자동 전환)
    function getDeviceVisualHtml(device, fallbackPreset) {
        const name = (device.name || "").toLowerCase();
        let icon = "📱";
        let typeLabel = "스마트폰";

        if (name.includes("macbook") || name.includes("laptop") || name.includes("그램") || name.includes("노트북") || name.includes("book")) {
            icon = "💻";
            typeLabel = "노트북 / PC";
        } else if (name.includes("ipad") || name.includes("tab") || name.includes("패드") || name.includes("태블릿")) {
            icon = "📟";
            typeLabel = "태블릿";
        } else if (name.includes("watch") || name.includes("워치")) {
            icon = "⌚";
            typeLabel = "스마트워치";
        } else if (name.includes("airpods") || name.includes("buds") || name.includes("헤드폰") || name.includes("버즈") || name.includes("이어폰")) {
            icon = "🎧";
            typeLabel = "오디오";
        }

        const targetUrl = device.image_url || fallbackPreset;

        return `
            <img class="device-img" 
                 src="${targetUrl}" 
                 referrerpolicy="no-referrer" 
                 alt="${device.name}"
                 onerror="this.onerror=null; this.style.display='none'; this.nextElementSibling.style.display='flex';">
            <div class="device-fallback-badge" style="display: none;">
                <span class="badge-icon">${icon}</span>
                <span class="badge-sub">${typeLabel}</span>
            </div>
        `;
    }

    // 최저가 쇼핑몰 3대장 (다나와 / 네이버 쇼핑 / 쿠팡) 딥링크 생성 함수
    function createShoppingLinksHtml(deviceName) {
        if (!deviceName) return "";
        const q = encodeURIComponent(deviceName.trim());
        const danawaUrl = `https://search.danawa.com/dsearch.php?query=${q}`;
        const naverUrl = `https://search.shopping.naver.com/search/all?query=${q}`;
        const coupangUrl = `https://www.coupang.com/np/search?component=&q=${q}`;

        return `
            <a href="${danawaUrl}" target="_blank" rel="noopener noreferrer" class="shop-btn danawa-btn" title="다나와에서 실시간 최저가 비교">
                <span class="shop-icon">📊</span> 다나와 최저가
            </a>
            <a href="${naverUrl}" target="_blank" rel="noopener noreferrer" class="shop-btn naver-btn" title="네이버 쇼핑에서 최저가 검색">
                <span class="shop-icon">🟢</span> 네이버 쇼핑
            </a>
            <a href="${coupangUrl}" target="_blank" rel="noopener noreferrer" class="shop-btn coupang-btn" title="쿠팡 로켓/최저가 둘러보기">
                <span class="shop-icon">🚀</span> 쿠팡 바로가기
            </a>
        `;
    }

    // 3. 비교 결과 렌더링 함수
    function renderComparison(data) {
        const devA = data.device_a;
        const devB = data.device_b;
        const verdict = data.overall_verdict || {};

        // 테이블 헤더 (이름 및 대표 이미지 직접 생성 주입)
        const cellA = document.getElementById("th-device-a");
        const cellB = document.getElementById("th-device-b");

        const imgHtmlA = getDeviceVisualHtml(devA, "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=500&q=80");
        const imgHtmlB = getDeviceVisualHtml(devB, "https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=500&q=80");

        cellA.innerHTML = `
            <div class="device-header-cell">
                <div class="device-img-wrapper" title="${devA.name}">
                    ${imgHtmlA}
                </div>
                <span class="device-title">${devA.name}</span>
            </div>
        `;

        cellB.innerHTML = `
            <div class="device-header-cell">
                <div class="device-img-wrapper" title="${devB.name}">
                    ${imgHtmlB}
                </div>
                <span class="device-title">${devB.name}</span>
            </div>
        `;

        // 가격
        document.getElementById("val-price-a").textContent = devA.price_range || "가격 정보 없음";
        document.getElementById("val-price-b").textContent = devB.price_range || "가격 정보 없음";

        // 최저가 쇼핑몰 바로가기 링크 주입 (가격 셀 & 하단 추천 박스)
        const shopHtmlA = createShoppingLinksHtml(devA.name);
        const shopHtmlB = createShoppingLinksHtml(devB.name);

        const valShopA = document.getElementById("val-shop-a");
        const valShopB = document.getElementById("val-shop-b");
        if (valShopA) valShopA.innerHTML = shopHtmlA;
        if (valShopB) valShopB.innerHTML = shopHtmlB;

        const recShopA = document.getElementById("rec-shop-a");
        const recShopB = document.getElementById("rec-shop-b");
        if (recShopA) recShopA.innerHTML = shopHtmlA;
        if (recShopB) recShopB.innerHTML = shopHtmlB;

        // 상세 스펙
        document.getElementById("val-cpu-a").textContent = devA.specs.processor || "-";
        document.getElementById("val-cpu-b").textContent = devB.specs.processor || "-";

        document.getElementById("val-display-a").textContent = devA.specs.display || "-";
        document.getElementById("val-display-b").textContent = devB.specs.display || "-";

        document.getElementById("val-camera-a").textContent = devA.specs.camera || "-";
        document.getElementById("val-camera-b").textContent = devB.specs.camera || "-";

        document.getElementById("val-battery-a").textContent = devA.specs.battery || "-";
        document.getElementById("val-battery-b").textContent = devB.specs.battery || "-";

        document.getElementById("val-weight-a").textContent = devA.specs.weight || "-";
        document.getElementById("val-weight-b").textContent = devB.specs.weight || "-";

        // 장점 리스트
        renderBulletList("val-pros-a", devA.pros);
        renderBulletList("val-pros-b", devB.pros);

        // 단점 리스트
        renderBulletList("val-cons-a", devA.cons);
        renderBulletList("val-cons-b", devB.cons);

        // 리뷰 요약
        document.getElementById("val-review-a").textContent = devA.review_summary || "-";
        document.getElementById("val-review-b").textContent = devB.review_summary || "-";

        // 종합 평가 및 추천
        document.getElementById("verdict-summary").textContent = verdict.summary || "-";
        document.getElementById("rec-a-title").textContent = `${devA.name} 추천 대상`;
        document.getElementById("rec-a-desc").textContent = verdict.recommendation_a || "-";
        document.getElementById("rec-b-title").textContent = `${devB.name} 추천 대상`;
        document.getElementById("rec-b-desc").textContent = verdict.recommendation_b || "-";

        // 초보자 일상 비유 요약 텍스트 주입
        const analogy = verdict.beginner_analogy || `${devA.name}와 ${devB.name}의 성능과 특성을 일상 사물에 빗대어 알기 쉽게 비교 분석한 결과입니다.`;
        if (beginnerAnalogyText) {
            beginnerAnalogyText.textContent = analogy;
        }

        if (beginnerAnalogyCard) {
            if (isBeginnerMode && verdict.beginner_analogy) {
                beginnerAnalogyCard.classList.remove("hidden");
            } else {
                beginnerAnalogyCard.classList.add("hidden");
            }
        }
    }

    // 불릿 리스트(장점/단점) 렌더링 헬퍼 함수
    function renderBulletList(elementId, items) {
        const ul = document.getElementById(elementId);
        ul.innerHTML = "";
        if (Array.isArray(items) && items.length > 0) {
            items.forEach(item => {
                const li = document.createElement("li");
                li.textContent = item;
                ul.appendChild(li);
            });
        } else {
            const li = document.createElement("li");
            li.textContent = "-";
            ul.appendChild(li);
        }
    }

    // 4. 클립보드 복사 기능
    copyBtn.addEventListener("click", () => {
        if (!currentComparisonData) return;

        const mdText = generateMarkdownText(currentComparisonData);
        navigator.clipboard.writeText(mdText).then(() => {
            const originalText = copyBtn.textContent;
            copyBtn.textContent = "✅ 복사 완료!";
            setTimeout(() => {
                copyBtn.textContent = originalText;
            }, 2000);
        }).catch(err => {
            alert("클립보드 복사에 실패했습니다: " + err);
        });
    });

    // 5. 마크다운(.md) 파일 다운로드 기능
    downloadBtn.addEventListener("click", () => {
        if (!currentComparisonData) return;

        const mdText = generateMarkdownText(currentComparisonData);
        const blob = new Blob([mdText], { type: "text/markdown;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        const safeNameA = currentComparisonData.device_a.name.replace(/\s+/g, "_");
        const safeNameB = currentComparisonData.device_b.name.replace(/\s+/g, "_");

        a.href = url;
        a.download = `비교_${safeNameA}_vs_${safeNameB}.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });

    // 마크다운 형식 변환 헬퍼 함수
    function generateMarkdownText(data) {
        const a = data.device_a;
        const b = data.device_b;
        const v = data.overall_verdict;
        const qA = encodeURIComponent(a.name);
        const qB = encodeURIComponent(b.name);

        const analogyBlock = v.beginner_analogy ? `
## 🐣 초보자를 위한 3초 일상 비유 요약
> ${v.beginner_analogy}
` : "";

        return `# ⚡ IT 기기 비교 대조: ${a.name} vs ${b.name}
${analogyBlock}
## 📊 주요 스펙 및 가격 비교 표

| 비교 항목 | ${a.name} | ${b.name} |
| :--- | :--- | :--- |
| **최신 실거래 가격대** | ${a.price_range} | ${b.price_range} |
| **프로세서 (AP/CPU)** | ${a.specs.processor} | ${b.specs.processor} |
| **디스플레이** | ${a.specs.display} | ${b.specs.display} |
| **카메라 사양** | ${a.specs.camera} | ${b.specs.camera} |
| **배터리 / 충전** | ${a.specs.battery} | ${b.specs.battery} |
| **무게 및 휴대성** | ${a.specs.weight} | ${b.specs.weight} |
| **실사용자 리뷰 요약** | ${a.review_summary} | ${b.review_summary} |

## 🛒 최저가 쇼핑 바로가기
### 🔹 ${a.name}
- [다나와 실시간 최저가 확인](https://search.danawa.com/dsearch.php?query=${qA})
- [네이버 쇼핑 최저가 비교](https://search.shopping.naver.com/search/all?query=${qA})
- [쿠팡 로켓/최저가 둘러보기](https://www.coupang.com/np/search?component=&q=${qA})

### 🔹 ${b.name}
- [다나와 실시간 최저가 확인](https://search.danawa.com/dsearch.php?query=${qB})
- [네이버 쇼핑 최저가 비교](https://search.shopping.naver.com/search/all?query=${qB})
- [쿠팡 로켓/최저가 둘러보기](https://www.coupang.com/np/search?component=&q=${qB})

## 👍 핵심 장점
### ${a.name}
${a.pros.map(p => `- ${p}`).join("\n")}

### ${b.name}
${b.pros.map(p => `- ${p}`).join("\n")}

## 👎 아쉬운 단점
### ${a.name}
${a.cons.map(c => `- ${c}`).join("\n")}

### ${b.name}
${b.cons.map(c => `- ${c}`).join("\n")}

## 🏆 종합 총평 & 추천
> ${v.summary}

- **${a.name} 추천 대상:** ${v.recommendation_a}
- **${b.name} 추천 대상:** ${v.recommendation_b}
`;
    }

    // 에러 표시 및 숨김 헬퍼 함수
    function showError(msg) {
        errorMessage.textContent = msg;
        errorBox.classList.remove("hidden");
        errorBox.scrollIntoView({ behavior: "smooth" });
    }

    function hideError() {
        errorBox.classList.add("hidden");
    }

    // PWA 서비스 워커 등록
    if ("serviceWorker" in navigator) {
        window.addEventListener("load", () => {
            navigator.serviceWorker.register("/static/sw.js")
                .then(reg => console.log("PWA ServiceWorker 등록 완료:", reg.scope))
                .catch(err => console.log("PWA ServiceWorker 등록 실패:", err));
        });
    }
});
