# -*- coding: utf-8 -*-
"""
Data Loader for Streamlit Cloud
================================
Reads Gold + Silver Parquet files from Google Drive public share link.

Setup:
1. Share your lakehouse folder on Google Drive (Anyone with link → Viewer)
2. Set GDRIVE_FOLDER_ID in Streamlit secrets
3. Uses gdown to download parquet files
"""
import streamlit as st
import pandas as pd
import os
import glob
import io
import tempfile
from config.settings import CACHE_TTL


# ============================================
# DATA DIRECTORY (local cache on Streamlit Cloud)
# ============================================
DATA_DIR = os.path.join(tempfile.gettempdir(), "hmk_lakehouse_cache")
GOLD_DIR = os.path.join(DATA_DIR, "gold")
SILVER_DIR = os.path.join(DATA_DIR, "silver")


def _download_from_gdrive():
    """
    Download parquet files from Google Drive shared folder.
    Uses Streamlit secrets for folder IDs.
    """
    try:
        import gdown
    except ImportError:
        os.system("pip install gdown -q")
        import gdown

    os.makedirs(GOLD_DIR, exist_ok=True)
    os.makedirs(SILVER_DIR, exist_ok=True)

    # Get folder IDs from Streamlit secrets
    gold_folder_id = st.secrets.get("GOLD_FOLDER_ID", "")
    silver_folder_id = st.secrets.get("SILVER_FOLDER_ID", "")

    if gold_folder_id:
        gold_url = f"https://drive.google.com/drive/folders/{gold_folder_id}"
        try:
            gdown.download_folder(gold_url, output=GOLD_DIR, quiet=True, remaining_ok=True)
        except Exception as e:
            st.warning(f"Gold download issue: {str(e)[:100]}")

    if silver_folder_id:
        silver_url = f"https://drive.google.com/drive/folders/{silver_folder_id}"
        try:
            gdown.download_folder(silver_url, output=SILVER_DIR, quiet=True, remaining_ok=True)
        except Exception as e:
            st.warning(f"Silver download issue: {str(e)[:100]}")


def _read_parquet_dir(directory: str) -> pd.DataFrame:
    """Read all parquet files from a directory."""
    if not os.path.exists(directory):
        return pd.DataFrame()

    files = glob.glob(os.path.join(directory, "**", "*.parquet"), recursive=True)
    files = [f for f in files if '_delta_log' not in f]

    if not files:
        return pd.DataFrame()

    dfs = []
    for f in files:
        try:
            dfs.append(pd.read_parquet(f))
        except Exception:
            pass

    if not dfs:
        return pd.DataFrame()

    df = pd.concat(dfs, ignore_index=True)

    # Dedup by conversation_id
    if 'conversation_id' in df.columns:
        df = df.drop_duplicates(subset=['conversation_id'], keep='last')

    return df


def _ensure_data():
    """Check if data exists locally, download if not."""
    gold_files = glob.glob(os.path.join(GOLD_DIR, "**", "*.parquet"), recursive=True) if os.path.exists(GOLD_DIR) else []

    if not gold_files:
        with st.spinner("📥 Đang tải dữ liệu từ Google Drive..."):
            _download_from_gdrive()


@st.cache_data(ttl=CACHE_TTL)
def load_all_data() -> dict:
    """
    Load all data: Gold + Silver.
    Downloads from Google Drive on first run.
    """
    _ensure_data()

    gold_df = _read_parquet_dir(GOLD_DIR)
    silver_df = _read_parquet_dir(SILVER_DIR)

    # Merge full_conversation from Silver if Gold missing it
    if (not gold_df.empty
            and not silver_df.empty
            and 'conversation_id' in gold_df.columns
            and 'full_conversation' in silver_df.columns):
        needs_merge = (
            'full_conversation' not in gold_df.columns
            or gold_df['full_conversation'].isna().all()
            or (gold_df['full_conversation'].astype(str).isin(['', 'nan', 'None'])).all()
        )
        if needs_merge:
            silver_fc = silver_df[['conversation_id', 'full_conversation']].drop_duplicates(
                subset='conversation_id'
            )
            gold_df = gold_df.merge(
                silver_fc, on='conversation_id', how='left', suffixes=('', '_silver')
            )
            if 'full_conversation_silver' in gold_df.columns:
                gold_df['full_conversation'] = gold_df['full_conversation_silver']
                gold_df.drop(columns=['full_conversation_silver'], inplace=True)

    # Parse dates
    if 'conversation_date' in gold_df.columns:
        gold_df['conversation_date'] = pd.to_datetime(gold_df['conversation_date'], errors='coerce')

    return {
        'ai_unified': gold_df,
        'daily_kpis': pd.DataFrame(),  # Not used in Colab pipeline
        'conversations': silver_df,
        'behavioral_metrics': pd.DataFrame()
    }


def get_data_status(df=None) -> dict:
    """Get data quality metrics."""
    if df is None:
        data = load_all_data()
        df = data.get('ai_unified', pd.DataFrame())

    total = len(df) if not df.empty else 0
    processed = 0

    ai_fields = ['intent_primary', 'sentiment_overall', 'disc_primary', 'agent_overall_score']
    if any(col in df.columns for col in ai_fields):
        for col in ai_fields:
            if col in df.columns:
                processed = int(df[col].notna().sum())
                break

    # Quality metrics (production)
    quality_info = {}
    if 'ai_parse_success' in df.columns:
        quality_info['parse_success'] = int(df['ai_parse_success'].sum())
    if 'ai_quality_score' in df.columns:
        quality_info['avg_quality'] = round(df['ai_quality_score'].mean(), 1)

    return {
        'total': total,
        'processed': processed,
        'pending': total - processed,
        **quality_info
    }


def refresh_data():
    """Force refresh data from Google Drive."""
    # Clear cache
    load_all_data.clear()

    # Clear local files
    import shutil
    if os.path.exists(DATA_DIR):
        shutil.rmtree(DATA_DIR)

    # Re-download
    st.rerun()
