# -*- coding: utf-8 -*-
"""
AI Insights Layer — Dashboard v7.0
====================================
Generates Vietnamese-language business insights below each chart by calling
Gemini 1.5 Flash (primary) or OpenAI GPT-4o-mini (fallback).

Usage in tab files:
    from utils.ai_insights import render_insight_box

    st.plotly_chart(fig, ...)
    render_insight_box('exec_time_series', {
        "total_conversations": int(total),
        "peak_day": str(peak_day),
        ...
    })

Requirements:
    pip install google-generativeai>=0.7.0 openai>=1.0.0
    # Both are optional — dashboard works without them.

Secrets (.streamlit/secrets.toml):
    GEMINI_API_KEY  = "AIzaSy..."   # Google AI Studio
    OPENAI_API_KEY  = "sk-..."      # Optional fallback
"""

from __future__ import annotations
import json
from typing import Optional

import streamlit as st

# ─── optional SDK imports ─────────────────────────────────────────────────────
try:
    import google.generativeai as genai
    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False


# ─── shared system prompt ─────────────────────────────────────────────────────
_SYSTEM_PROMPT = (
    "Bạn là chuyên gia phân tích kinh doanh cho cửa hàng kính mắt HMK. "
    "Phân tích dữ liệu chat customer service và đưa ra insight ngắn gọn. "
    "Trả lời bằng tiếng Việt đơn giản, đúng 3-4 câu hoàn chỉnh: "
    "1 nhận xét chính về dữ liệu, 1 điểm đáng chú ý, 1 gợi ý hành động cụ thể. "
    "Không lặp lại số liệu đã hiển thị trên biểu đồ. "
    "Không dùng tiêu đề, bullet points hay markdown formatting — chỉ văn xuôi thuần."
)

# ─── per-chart prompt templates ───────────────────────────────────────────────
CHART_PROMPTS: dict[str, str] = {
    # ── Executive ────────────────────────────────────────────────────────────
    "exec_time_series": (
        "Biểu đồ 'Lượng hội thoại theo thời gian' của HMK. "
        "Dữ liệu tóm tắt (JSON): {data_json}. "
        "Phân tích xu hướng tổng thể (tăng/giảm/ổn định), "
        "ngày cao điểm bất thường và gợi ý điều chỉnh lịch nhân sự hoặc chiến dịch marketing."
    ),
    "exec_intent_pie": (
        "Biểu đồ 'Phân phối mục đích chat' của khách hàng HMK. "
        "Dữ liệu: {data_json}. "
        "Nhận xét intent nào chiếm ưu thế, cân bằng giữa mua hàng/hỏi thông tin/khiếu nại, "
        "và cơ hội tập trung phát triển dịch vụ."
    ),
    "exec_heatmap": (
        "Biểu đồ nhiệt 'Hoạt động theo giờ và ngày trong tuần' của HMK. "
        "Dữ liệu: {data_json}. "
        "Xác định khung giờ và ngày thực sự bận nhất, "
        "đề xuất bố trí nhân sự và thời điểm tối ưu cho quảng cáo retargeting."
    ),

    # ── Customer Intelligence ─────────────────────────────────────────────────
    "intel_disc_pie": (
        "Biểu đồ 'Phân phối tính cách DISC' của khách hàng HMK. "
        "D=quyết đoán, I=ảnh hưởng/vui vẻ, S=ổn định/kiên nhẫn, C=cẩn thận/phân tích. "
        "Dữ liệu: {data_json}. "
        "Nhận xét nhóm tính cách chủ đạo và đề xuất chiến lược tư vấn, "
        "ngôn từ marketing phù hợp nhất với nhóm đó."
    ),
    "intel_gen_bar": (
        "Biểu đồ 'Phân phối thế hệ khách hàng' của HMK. "
        "Gen Z (1997–2012), Millennial (1981–1996), Gen X (1965–1980), Boomer (trước 1965). "
        "Dữ liệu: {data_json}. "
        "Nhận xét thế hệ khách chủ lực, hàm ý cho sản phẩm ưu tiên, "
        "kênh tiếp thị và phong cách giao tiếp phù hợp."
    ),
    "intel_disc_matrix": (
        "Ma trận 'Tính cách DISC × Mục đích mua hàng' tại HMK. "
        "Dữ liệu: {data_json}. "
        "Xác định tổ hợp DISC–Intent nổi bật nhất, "
        "và đề xuất một cách tiếp cận tư vấn cụ thể cho tổ hợp đó."
    ),

    # ── Conversion ────────────────────────────────────────────────────────────
    "conv_funnel": (
        "Biểu đồ 'Phễu giai đoạn mua hàng' tại HMK (Awareness → Purchase). "
        "Dữ liệu: {data_json}. "
        "Xác định giai đoạn thất thoát lớn nhất, "
        "nguyên nhân tiềm ẩn phổ biến trong ngành bán lẻ mắt kính, "
        "và một hành động cụ thể để cải thiện tỉ lệ chuyển đổi."
    ),
    "conv_dropoff": (
        "Biểu đồ 'Điểm khách rời bỏ kênh chat' của HMK. "
        "Dữ liệu: {data_json}. "
        "Phân tích bước thất thoát nghiêm trọng nhất, "
        "hành vi tiêu biểu của khách tại bước đó và giải pháp giữ chân cụ thể."
    ),
    "conv_churn": (
        "Biểu đồ 'Lý do khách hàng rời bỏ (churn)' tại HMK. "
        "Dữ liệu: {data_json}. "
        "Phân tích lý do churn phổ biến nhất và "
        "đề xuất ưu tiên khắc phục nào có ROI cao nhất cho cửa hàng kính mắt."
    ),

    # ── Sentiment ─────────────────────────────────────────────────────────────
    "sent_dist_pie": (
        "Biểu đồ 'Phân phối cảm xúc khách hàng' trong chat tại HMK. "
        "Dữ liệu: {data_json}. "
        "Đánh giá sức khỏe tổng thể trải nghiệm khách hàng, "
        "cảnh báo nếu tỉ lệ tiêu cực đáng lo ngại, "
        "và gợi ý cải thiện điểm tiếp xúc nào."
    ),
    "sent_trend_line": (
        "Biểu đồ 'Xu hướng cảm xúc trung bình theo ngày' tại HMK. "
        "Dữ liệu: {data_json}. "
        "Xác định giai đoạn sụt giảm cảm xúc, ngày bất thường, "
        "và hàm ý về sự kiện hoặc vấn đề sản phẩm/dịch vụ cần điều tra thêm."
    ),
    "sent_trust_pie": (
        "Biểu đồ 'Mức độ tin tưởng của khách hàng' vào HMK qua chat. "
        "Dữ liệu: {data_json}. "
        "Phân tích tỉ lệ niềm tin cao/thấp, ảnh hưởng đến quyết định mua, "
        "và một hành động cụ thể để xây dựng thêm niềm tin với khách hàng."
    ),

    # ── Agent ─────────────────────────────────────────────────────────────────
    "agent_radar": (
        "Biểu đồ radar 'Điểm kỹ năng trung bình nhóm nhân viên' tại HMK. "
        "Dữ liệu: {data_json}. "
        "Nhận xét kỹ năng mạnh nhất, yếu nhất của đội, "
        "và đề xuất một chủ đề training cụ thể nên ưu tiên trong tháng tới."
    ),
    "agent_strengths_bar": (
        "Biểu đồ 'Điểm mạnh phổ biến của nhân viên tư vấn' tại HMK. "
        "Dữ liệu: {data_json}. "
        "Nhận xét điểm mạnh được ghi nhận nhiều nhất có ý nghĩa gì với trải nghiệm khách, "
        "và đề xuất cách nhân rộng thực hành tốt (sharing session, checklist)."
    ),

    # ── Revenue ───────────────────────────────────────────────────────────────
    "rev_funnel": (
        "Biểu đồ 'Phễu cơ hội doanh thu' của HMK (từ tổng hội thoại → chuyển đổi). "
        "Dữ liệu: {data_json}. "
        "Phân tích tỉ lệ chuyển đổi tổng thể, "
        "bước thất thoát doanh thu lớn nhất và hành động cụ thể để cải thiện."
    ),
    "rev_urgency_pie": (
        "Biểu đồ 'Mức độ cấp bách của khách hàng' khi chat với HMK. "
        "Dữ liệu: {data_json}. "
        "Phân tích tỉ lệ khách cần hỗ trợ gấp, "
        "đề xuất quy trình ưu tiên phân loại và follow-up nhanh cho nhân viên."
    ),
    "rev_competitor_bar": (
        "Biểu đồ 'Đối thủ cạnh tranh được nhắc đến' trong chat tại HMK. "
        "Dữ liệu: {data_json}. "
        "Xác định đối thủ được so sánh nhiều nhất, "
        "hàm ý về điểm cạnh tranh cần cải thiện và một thông điệp phân biệt cụ thể."
    ),
    "rev_price_bar": (
        "Biểu đồ 'Khoảng giá khách hàng quan tâm' tại HMK. "
        "Dữ liệu: {data_json}. "
        "Xác định phân khúc giá chủ lực, "
        "cơ hội upsell lên phân khúc cao hơn và chiến lược định giá phù hợp."
    ),
}


# ─── secret helpers ───────────────────────────────────────────────────────────
def _get_gemini_key() -> Optional[str]:
    try:
        val = st.secrets.get("GEMINI_API_KEY", "")
        return val if val else None
    except Exception:
        return None


def _get_openai_key() -> Optional[str]:
    try:
        val = st.secrets.get("OPENAI_API_KEY", "")
        return val if val else None
    except Exception:
        return None


# ─── core cached generation ───────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def generate_chart_insight(chart_id: str, data_summary_json: str) -> Optional[str]:
    """
    Call LLM and return a Vietnamese insight string, or None on any failure.

    Parameters
    ----------
    chart_id : str
        Key into CHART_PROMPTS.
    data_summary_json : str
        JSON string of chart data (str arg → hashable for st.cache_data).

    Returns
    -------
    str or None
    """
    if chart_id not in CHART_PROMPTS:
        return None

    user_prompt = CHART_PROMPTS[chart_id].format(data_json=data_summary_json)

    # ── Try Gemini 1.5 Flash ─────────────────────────────────────────────────
    if _GEMINI_AVAILABLE:
        gemini_key = _get_gemini_key()
        if gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    system_instruction=_SYSTEM_PROMPT,
                )
                response = model.generate_content(
                    user_prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=300,
                        temperature=0.4,
                    ),
                )
                text = response.text.strip() if response.text else ""
                if text:
                    return text
            except Exception:
                pass  # fall through to OpenAI

    # ── Fallback: OpenAI GPT-4o-mini ─────────────────────────────────────────
    if _OPENAI_AVAILABLE:
        openai_key = _get_openai_key()
        if openai_key:
            try:
                client = OpenAI(api_key=openai_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user",   "content": user_prompt},
                    ],
                    max_tokens=300,
                    temperature=0.4,
                )
                text = response.choices[0].message.content
                if text:
                    return text.strip()
            except Exception:
                pass

    return None


# ─── public render function ───────────────────────────────────────────────────
def render_insight_box(chart_id: str, data_summary: dict) -> None:
    """
    Render a collapsible AI-insight expander below a chart.

    Call immediately after every st.plotly_chart() call.
    All values in data_summary must be plain Python types
    (int, float, str, list, dict) — no numpy scalars or DataFrames.

    If no API key is configured or the call fails, nothing is rendered.
    """
    if chart_id not in CHART_PROMPTS:
        return

    try:
        data_json = json.dumps(data_summary, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return

    insight = generate_chart_insight(chart_id, data_json)
    if not insight:
        return

    with st.expander("💡 AI Phân Tích", expanded=False):
        st.markdown(insight)
