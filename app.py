import streamlit as st
import PyPDF2
import openai
import os
import json
import re
from dotenv import load_dotenv

# 載入 .env 檔
load_dotenv()

LANG_TEXT = {
    "繁體中文": {
        "lang_label": "語言",
        "lang_select_label": "Language / 語言",
        "title": "RecruitSmart AI",
        "subtitle": "職位適配與智慧面試導航系統",
        "intro": "上傳職缺說明 (JD) 與多份履歷，AI 將自動完成評分、排序並生成面試建議。",
        "sidebar_api": "系統設定",
        "sidebar_key": "OpenAI API 金鑰",
        "sidebar_key_help": "若留空則使用環境變數",
        "jd_subheader": "職缺說明 (JD)",
        "jd_input_mode_paste": "貼上文字",
        "jd_input_mode_upload": "上傳檔案",
        "jd_textarea_label": "貼上內容",
        "jd_textarea_placeholder": "請將職缺說明貼上此處...",
        "jd_uploader_label": "上傳 JD (PDF/TXT)",
        "jd_uploader_help": "支援 PDF, .txt, .md",
        "jd_format_warning": "格式錯誤，請重新上傳。",
        "resume_subheader": "人才履歷 (Resumes)",
        "resume_uploader_label": "上傳履歷 (可多選 PDF)",
        "analyze_btn": "開始自動化分析",
        "error_no_key": "請提供 API Key 以啟動 AI 分析。",
        "error_analyze": "分析發生錯誤：{msg}",
        "score_subheader": "適配分數",
        "score_metric_label": "總分",
        "score_metric_help": "由 AI 根據技術、經驗、成果、潛力加總",
        "score_details": "評分組成說明",
        "technical_skills_label": "技術技能匹配",
        "experience_label": "相關經驗契合",
        "impact_label": "專案影響力與成果",
        "potential_label": "職位潛力與適配性",
        "skills_subheader": "核心技能匹配",
        "career_subheader": "職涯發展潛力",
        "missing_subheader": "缺少的關鍵經驗",
        "questions_subheader": "建議深度面試問題",
        "no_data": "無資料",
        "analyzing": "AI 員工正在努力分析中...",
        "ranking_title": "候選人排名 (Ranking)",
    },
    "English": {
        "lang_label": "Language",
        "lang_select_label": "Language / 語言",
        "title": "RecruitSmart AI",
        "subtitle": "JD & Resume Intelligent Matcher",
        "intro": "Upload a JD and multiple resumes. AI will score, rank, and generate insights automatically.",
        "sidebar_api": "Settings",
        "sidebar_key": "OpenAI API Key",
        "sidebar_key_help": "Leave blank to use env var",
        "jd_subheader": "Job Description (JD)",
        "jd_input_mode_paste": "Paste Text",
        "jd_input_mode_upload": "Upload File",
        "jd_textarea_label": "Paste JD Here",
        "jd_textarea_placeholder": "Paste job description content...",
        "jd_uploader_label": "Upload JD (PDF/TXT)",
        "jd_uploader_help": "Supports PDF, .txt, .md",
        "jd_format_warning": "Invalid format, please try again.",
        "resume_subheader": "Candidate Resumes",
        "resume_uploader_label": "Upload Resumes (Multiple PDF)",
        "analyze_btn": "Start AI Analysis",
        "error_no_key": "Please provide an API Key to start.",
        "error_analyze": "Error: {msg}",
        "score_subheader": "Match Score",
        "score_metric_label": "Overall Score",
        "score_metric_help": "Calculated based on skills, experience, impact, and potential",
        "score_details": "Score Breakdown & Criteria",
        "technical_skills_label": "Technical Skills Match",
        "experience_label": "Relevant Experience Fit",
        "impact_label": "Project Impact & Outcomes",
        "potential_label": "Role Potential & Fit",
        "skills_subheader": "✅ Core Skills Match",
        "career_subheader": "🚀 Career Potential",
        "missing_subheader": "⚠️ Missing Experience",
        "questions_subheader": "💡 Suggested Interview Questions",
        "no_data": "N/A",
        "analyzing": "AI Employee is analyzing...",
        "ranking_title": "🏆 Candidate Ranking",
    },
}

def clean_json_string(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return text[start : end + 1]
    return text

def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    return "".join([page.extract_text() or "" for page in reader.pages])

def analyze_resume(jd_text, resume_text, api_key, target_lang="English"):
    # 強化 Prompt 指令，確保輸出語言絕對一致
    lang_instruction = (
        f"IMPORTANT: You must output ALL analysis, reasons, and descriptions strictly in {target_lang}. "
        f"If the input is Chinese but target_lang is English, translate everything into English. "
        "Keep the JSON keys in English."
    )
    
    system_prompt = (
        "你是一位嚴苛的矽谷技術招募官。請依據以下格式回傳 JSON，並從履歷提取候選人全名。\n"
        "{\n"
        '  "name": "Full Name",\n'
        '  "score": int, \n'
        '  "score_breakdown": {\n'
        '    "technical_skills": { "score": int, "reason": "string" },\n'
        '    "experience": { "score": int, "reason": "string" },\n'
        '    "impact": { "score": int, "reason": "string" },\n'
        '    "potential": { "score": int, "reason": "string" }\n'
        '  },\n'
        '  "core_skills_match": ["string"],\n'
        '  "missing_experience": ["string"],\n'
        '  "career_potential": "string",\n'
        '  "interview_questions": ["string"]\n'
        "}\n"
        f"{lang_instruction}"
    )
    
    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"JD:\n{jd_text}\n\nResume:\n{resume_text}"}],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        return json.loads(clean_json_string(response.choices[0].message.content))
    except Exception as e:
        return {"error": str(e)}

# --- UI Setup ---
with st.sidebar:
    lang = st.selectbox(LANG_TEXT["繁體中文"]["lang_select_label"], options=["繁體中文", "English"])
    t = LANG_TEXT[lang]
    st.subheader(t["sidebar_api"])
    api_key_input = st.text_input(t["sidebar_key"], type="password")
    api_key = api_key_input.strip() if api_key_input else os.getenv("OPENAI_API_KEY")

st.title(t["title"])
st.subheader(t["subtitle"])

if "results" not in st.session_state: st.session_state.results = []

# --- Layout ---
c1, c2 = st.columns(2)
with c1:
    st.subheader(t["jd_subheader"])
    jd_mode = st.radio(