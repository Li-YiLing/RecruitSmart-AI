import streamlit as st
import PyPDF2
import openai
import os
import json
import re
from dotenv import load_dotenv

LANG_TEXT = {
    "繁體中文": {
        "lang_label": "語言",
        "lang_select_label": "Language / 語言",
        "title": "RecruitSmart AI",
        "subtitle": "職位說明與履歷比對輔助",
        "intro": "請輸入職缺說明（JD）並上傳個人履歷，AI 會協助初步比對與給出建議。",
        "sidebar_api": "API 設定",
        "sidebar_key": "OpenAI API 金鑰",
        "sidebar_key_help": "若留空則使用環境變數 OPENAI_API_KEY",
        "jd_subheader": "職缺說明（JD）",
        "jd_input_mode_paste": "貼上文字",
        "jd_input_mode_upload": "上傳檔案",
        "jd_textarea_label": "直接貼上 JD 內容",
        "jd_textarea_placeholder": "請將職缺說明貼上此處...",
        "jd_uploader_label": "上傳 JD (PDF 或純文字)",
        "jd_uploader_help": "支援 PDF、.txt、.md 格式",
        "jd_format_warning": "JD 檔案格式錯誤，請上傳 PDF 或純文字檔 (.txt, .md)。",
        "resume_subheader": "個人履歷（Resume）",
        "resume_uploader_label": "上傳 Resume (PDF)",
        "analyze_btn": "開始分析",
        "error_no_key": "請在左側側邊欄輸入 OpenAI API Key，或設定環境變數 OPENAI_API_KEY。",
        "error_analyze": "分析時發生錯誤：{msg}",
        "score_subheader": "適配分數",
        "score_metric_label": "分數",
        "score_metric_help": "0-100，分數越高表示越適合",
        "score_details": "分數細項",
        "technical_skills_label": "技術技能匹配",
        "experience_label": "相關經驗契合",
        "impact_label": "專案影響力與成果",
        "potential_label": "職位潛力與適配性",
        "reason_prefix": "理由",
        "skills_subheader": "核心技能匹配",
        "career_subheader": "職涯發展潛力",
        "missing_subheader": "缺少的經驗",
        "questions_subheader": "建議面試問題",
        "no_data": "—",
        "analyzing": "分析中，請稍候...",
    },
    "English": {
        "lang_label": "Language",
        "lang_select_label": "Language / 語言",
        "title": "RecruitSmart AI",
        "subtitle": "JD & Resume Matcher",
        "intro": "Upload or paste Job Description (JD) and Resume. AI will analyze the match.",
        "sidebar_api": "API Settings",
        "sidebar_key": "OpenAI API Key",
        "sidebar_key_help": "Leave empty to use OPENAI_API_KEY env var.",
        "jd_subheader": "Job Description (JD)",
        "jd_input_mode_paste": "Paste Text",
        "jd_input_mode_upload": "Upload File",
        "jd_textarea_label": "Paste JD Content Here",
        "jd_textarea_placeholder": "Paste job description here...",
        "jd_uploader_label": "Upload JD (PDF, txt, md)",
        "jd_uploader_help": "Supports PDF, .txt, .md",
        "jd_format_warning": "Invalid format. Please upload PDF or text (.txt, .md).",
        "resume_subheader": "Resume",
        "resume_uploader_label": "Upload Resume (PDF)",
        "analyze_btn": "Start Analysis",
        "error_no_key": "Please enter OpenAI API Key in the sidebar, or set OPENAI_API_KEY env var.",
        "error_analyze": "Analysis error: {msg}",
        "score_subheader": "Match Score",
        "score_metric_label": "Score",
        "score_metric_help": "0-100, higher means better fit.",
        "score_details": "Score Details",
        "technical_skills_label": "Technical Skills Match",
        "experience_label": "Relevant Experience Fit",
        "impact_label": "Project Impact & Outcomes",
        "potential_label": "Role Potential & Fit",
        "reason_prefix": "Reason",
        "skills_subheader": "Core Skills Match",
        "career_subheader": "Career Potential",
        "missing_subheader": "Missing Experience",
        "questions_subheader": "Suggested Interview Questions",
        "no_data": "—",
        "analyzing": "Analyzing...",
    },
}

# 載入 .env 檔讀取環境變數
load_dotenv()

def clean_json_string(text):
    """
    清理 AI 回傳內容，移除 Markdown 標籤並只提取 { } 之間的 JSON 內容。
    """
    if not text or not isinstance(text, str):
        return ""
    text = text.strip()
    # 移除 Markdown 程式碼區塊標籤（如 ```json、``` 等）
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text)
    text = text.strip()
    # 只提取 { 和 } 之間的內容
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text

def extract_text_from_pdf(pdf_file):
    """
    讀取上傳的 PDF 並提取出全部文字內容。
    """
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def analyze_resume(jd_text, resume_text, api_key, target_lang="English"):
    """
    以 OpenAI GPT-4o/4-turbo 來分析 JD 及履歷內容，
    回傳包含：適配分數(0-100)、核心技能匹配、缺少經驗、5個面試問題的 JSON 格式。
    """
    lang_instruction = (
        f"You are a world-class HR Expert. All your analysis and content in the JSON response MUST BE in {target_lang}. "
        "Keep the JSON keys in English for system stability."
    )
    system_prompt = (
        "你是一位嚴苛的矽谷技術招募官，以高標準審視候選人。你的評分邏輯必須考量：\n\n"
        "1. **技能的相關性**：不只比對關鍵字，要深入檢視候選人是否在『實際專案』中運用過 JD 要求的技術。"
        "僅列出技能名稱而無專案佐證者，不計入匹配。\n\n"
        "2. **職涯發展潛力**：根據過往專案的複雜度、技術深度、成長軌跡，評估候選人是否有潛力勝任更高階挑戰。\n\n"
        "3. **面試問題必須極度具體**：每題必須直接引用履歷中的真實內容，格式範例："
        "『我看到你在 [具體專案名稱] 用了 [X 技術]，請問你是如何解決 [Y 問題/挑戰] 的？』"
        "禁止泛泛而談（例如：『請介紹你的專案經驗』）。\n\n"
        "請依下述格式回傳 JSON：{\n"
        '  "score": int,       // 總分 0-100，必須等於 score_breakdown 四項加總\n'
        '  "score_breakdown": {\n'
        '    "technical_skills": { "score": int (0-25), "reason": string },  // 技術技能匹配\n'
        '    "experience": { "score": int (0-25), "reason": string },        // 相關經驗契合\n'
        '    "impact": { "score": int (0-25), "reason": string },            // 專案影響力與成果\n'
        '    "potential": { "score": int (0-25), "reason": string }          // 職位潛力與適配性\n'
        '  },\n'
        '  "core_skills_match": [string],   // 有專案經驗佐證的核心技能匹配，每項簡述對應專案\n'
        '  "missing_experience": [string],  // 履歷缺少的經驗或技能（具體說明差距）\n'
        '  "career_potential": string,      // 簡短評估職涯發展潛力（1-2 句）\n'
        '  "interview_questions": [string]  // 5 個針對履歷具體內容的深度面試問題\n'
        "}\n"
        "score 必須等於 score_breakdown 四項分數的加總。只回傳純 JSON，不要說明文字。Return ONLY a valid JSON object. Do not include any preamble or postscript.\n\n"
        f"{lang_instruction}"
    )
    user_prompt = (
        f"職缺說明(JD)：\n{jd_text}\n\n"
        f"候選人履歷(Resume)：\n{resume_text}\n"
    )
    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=2000,
            response_format={"type": "json_object"},
        )
        raw_content = response.choices[0].message.content.strip()
        cleaned = clean_json_string(raw_content)
        result = json.loads(cleaned)
        return result
    except Exception as e:
        return {"error": str(e)}

# 側邊欄：語言選擇、API Key
with st.sidebar:
    lang = st.selectbox(
        LANG_TEXT["繁體中文"]["lang_select_label"],
        options=["繁體中文", "English"],
        key="lang_select",
    )
    texts = LANG_TEXT[lang]

    st.subheader(texts["sidebar_api"])
    api_key_input = st.text_input(
        texts["sidebar_key"],
        type="password",
        placeholder="sk-...",
        help=texts["sidebar_key_help"],
        key="api_key_input"
    )
    openai_api_key = api_key_input.strip() if api_key_input else os.getenv("OPENAI_API_KEY")

st.title(texts["title"])
st.subheader(texts["subtitle"])
st.write(texts["intro"])

col1, col2 = st.columns(2)
with col1:
    st.subheader(texts["jd_subheader"])
    jd_input_mode = st.radio(
        "Input mode",
        options=[texts["jd_input_mode_paste"], texts["jd_input_mode_upload"]],
        key="jd_mode",
        horizontal=True,
        label_visibility="collapsed"
    )
    if jd_input_mode == texts["jd_input_mode_paste"]:
        jd_text = st.text_area(
            texts["jd_textarea_label"],
            placeholder=texts["jd_textarea_placeholder"],
            height=200,
            key="jd_text"
        )
        jd_text = jd_text.strip() if jd_text else None
    else:
        jd_file = st.file_uploader(
            texts["jd_uploader_label"],
            type=["pdf", "txt", "md"],
            help=texts["jd_uploader_help"],
            key="jd_file"
        )
        jd_text = None
        if jd_file is not None:
            file_ext = jd_file.name.lower().split(".")[-1] if jd_file.name else ""
            if jd_file.type == "application/pdf" or file_ext == "pdf":
                jd_text = extract_text_from_pdf(jd_file)
            elif jd_file.type == "text/plain" or file_ext in ("txt", "md", "text"):
                jd_text = jd_file.read().decode("utf-8", errors="replace")
            else:
                st.warning(texts["jd_format_warning"])
with col2:
    st.subheader(texts["resume_subheader"])
    resume_file = st.file_uploader(texts["resume_uploader_label"], type=["pdf"], key="resume_file")

resume_text = None
if resume_file is not None:
    resume_text = extract_text_from_pdf(resume_file)

if st.button(texts["analyze_btn"]) and jd_text and resume_text:
    if not openai_api_key:
        st.error(texts["error_no_key"])
    else:
        target_lang = "Traditional Chinese" if lang == "繁體中文" else "English"
        with st.spinner(texts["analyzing"]):
            result = analyze_resume(jd_text, resume_text, openai_api_key, target_lang=target_lang)
        if "error" in result:
            st.error(texts["error_analyze"].format(msg=result["error"]))
        else:
            st.subheader(texts["score_subheader"])
            st.metric(texts["score_metric_label"], result.get("score", 0), help=texts["score_metric_help"])

            score_breakdown = result.get("score_breakdown", {})
            breakdown_config = [
                ("technical_skills", texts["technical_skills_label"]),
                ("experience", texts["experience_label"]),
                ("impact", texts["impact_label"]),
                ("potential", texts["potential_label"]),
            ]
            if score_breakdown and isinstance(score_breakdown, dict):
                with st.expander(texts["score_details"], expanded=False):
                    for key, label in breakdown_config:
                        item = score_breakdown.get(key, {})
                        if isinstance(item, dict):
                            s = int(item.get("score", 0))
                            r = str(item.get("reason", "")).strip()
                            c1, c2 = st.columns(2)
                            with c1:
                                st.markdown(f'<p style="font-size: 1.2em; font-weight: 600;">{label}</p>', unsafe_allow_html=True)
                            with c2:
                                st.markdown(f'<p style="font-size: 1.2em; text-align: right;">{s}/25</p>', unsafe_allow_html=True)
                            st.progress(min(max(s / 25, 0), 1.0))
                            if r:
                                st.write(r)
                        elif isinstance(item, (int, float)):
                            s = int(item)
                            c1, c2 = st.columns(2)
                            with c1:
                                st.markdown(f'<p style="font-size: 1.2em; font-weight: 600;">{label}</p>', unsafe_allow_html=True)
                            with c2:
                                st.markdown(f'<p style="font-size: 1.2em; text-align: right;">{s}/25</p>', unsafe_allow_html=True)
                            st.progress(min(max(s / 25, 0), 1.0))
            else:
                with st.expander(texts["score_details"], expanded=False):
                    st.write(texts["no_data"])

            st.subheader(texts["skills_subheader"])
            core_skills = result.get("core_skills_match", [])
            if isinstance(core_skills, list) and core_skills:
                markdown = "\n".join([f"- ✅ {str(skill)}" for skill in core_skills])
                st.markdown(markdown)
            else:
                st.write(texts["no_data"])

            st.subheader(texts["career_subheader"])
            st.write(result.get("career_potential", texts["no_data"]))

            st.subheader(texts["missing_subheader"])
            missing_exp = result.get("missing_experience", [])
            if isinstance(missing_exp, list) and missing_exp:
                markdown = "\n".join([f"- ⚠️ {str(item)}" for item in missing_exp])
                st.markdown(markdown)
            else:
                st.write(texts["no_data"])

            st.subheader(texts["questions_subheader"])
            for i, q in enumerate(result.get("interview_questions", []), 1):
                st.write(f"{i}. {q}")