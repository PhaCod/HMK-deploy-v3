# -*- coding: utf-8 -*-
"""
Settings for Streamlit Cloud Dashboard
========================================
"""
import os

# ============================================
# CACHE SETTINGS
# ============================================
CACHE_TTL = 600  # 10 minutes (Cloud is slower to refresh)

# ============================================
# APP SETTINGS
# ============================================
APP_TITLE = "HMK Optical Analytics v7.0"
APP_ICON = "📊"
VERSION = "7.0.0-cloud"

# ============================================
# PAGE CONFIG
# ============================================
PAGE_CONFIG = {
    "page_title": APP_TITLE,
    "page_icon": APP_ICON,
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# ============================================
# TAB DEFINITIONS
# ============================================
TAB_NAMES = [
    "📈 Executive",
    "🧠 Customer Intel",
    "🔄 Conversion",
    "💬 Sentiment",
    "👥 Agent Team",
    "💰 Revenue",
    "🔍 Explorer",
    "📋 Daily Reports"
]

# ============================================
# DATA TABLES (compatibility)
# ============================================
GOLD_TABLES = ['ai_unified']
SILVER_TABLES = ['conversations']

# ============================================
# COLUMN GROUPS FOR EXPLORER
# ============================================
COLUMN_GROUPS = {
    "Basic Info": ['conversation_id', 'customer_id', 'conversation_date', 'platform', 'duration_minutes'],
    "AI Classification": ['intent_primary', 'intent_secondary', 'funnel_type', 'purchase_stage'],
    "Sentiment": ['sentiment_overall', 'sentiment_start', 'sentiment_end', 'sentiment_score', 'sentiment_delta'],
    "Customer Profile": ['disc_primary', 'generation_cohort', 'lifestyle_segment', 'price_sensitivity', 'trust_level'],
    "Agent Performance": ['agent_overall_score', 'empathy_score', 'agent_response_speed', 'agent_strengths', 'agent_improvements'],
    "Revenue": ['product_interest', 'price_mentioned', 'price_range', 'urgency_level', 'competitor_brand'],
    "AI Quality": ['ai_parse_success', 'ai_quality_score', 'ai_was_truncated', 'ai_confidence', 'ai_validation_issues'],
    "Processing": ['ai_model', 'ai_version', 'source_silver_file', 'processed_at']
}

# ============================================
# COLOR SCHEMES
# ============================================
COLORS = {
    "primary": "#667eea",
    "secondary": "#764ba2",
    "success": "#00f5d4",
    "warning": "#f77f00",
    "danger": "#ef476f",
    "info": "#4cc9f0",
    "neutral": "#a0a0a0"
}

GRADIENT = {
    "primary": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    "success": "linear-gradient(135deg, #00b09b 0%, #96c93d 100%)",
    "danger": "linear-gradient(135deg, #ee0979 0%, #ff6a00 100%)"
}
