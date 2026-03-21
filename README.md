# RecruitSmart AI - 職位說明與履歷比對輔助系統
> **AI 驅動的自動化招募解決方案：連結企業需求 (JD) 與人才核心價值 (Resume)**

## 📌 專案願景 (Project Vision)
在企業數位轉型過程中，HR 部門面臨大量的履歷篩選壓力。本專案旨在透過 AI 應用架構，將傳統「關鍵字比對」提升至「語意邏輯分析」，協助企業快速識別具備實戰經驗的高潛力人才，並自動化生成高品質的面試準備建議。

## 🚀 核心價值與亮點 (Core Value & Features)
- **AI 優先開發架構**：採用 OpenAI GPT-4o 模型，透過結構化 JSON 模式確保數據穩定性。
- **雙語國際化支援**：介面與 AI 分析內容支援中英文一鍵切換，適應跨國招募場景。
- **可解釋的評分機制 (Explainable AI)**：將適配分數拆解為技術、經驗、影響力、潛力四大維度，並提供視覺化進度條與具體理由。
- **智慧面試導航**：根據履歷中的具體專案內容，自動生成 5 個「追問式」深度面試問題。
- **多模態數據處理**：支援 PDF 履歷解析與多種格式的職位說明 (JD) 輸入。

## 🛠️ 技術選型 (Tech Stack)
- **LLM Engine**: OpenAI GPT-4o (Structured Output / JSON Mode)
- **Framework**: Streamlit (快速原型開發與 UI 佈局)
- **Data Engineering**: PyPDF2 (PDF 解析), Regex (數據清洗)
- **Design Pattern**: Dictionary-based i18n, Environment Variable Security

## 🧠 AI 架構設計思維 (Architect's Insight)
作為 AI 應用架構師，本專案解決了以下技術難點：
1. **輸出穩定性**：透過自定義的 `clean_json_string` 邏輯與正則表達式，克服了 LLM 夾帶 Markdown 標籤導致解析失敗的問題。
2. **提示詞工程 (Prompt Engineering)**：設計了具備「角色扮演」與「邏輯限制」的 System Prompt，確保評分嚴謹度與問題的針對性。
3. **安全與擴展性**：採用 `.env` 環境變數管理金鑰，並使用語系字典架構，未來可輕易擴展至日語、韓語等多國語系。

## 📦 安裝與執行
1. 克隆專案：`git clone https://github.com/Li-YiLing/RecruitSmart-AI.git`
2. 安裝依賴：`pip install -r requirements.txt`
3. 設定環境變數：建立 `.env` 檔案並填入 `OPENAI_API_KEY=你的金鑰`
4. 執行應用：`streamlit run app.py`
