# -*- coding: utf-8 -*-
"""
Data Loader for Streamlit Cloud
================================
Reads Gold + Silver Parquet files from Google Drive public share link.

Setup:
1. Share your lakehouse folder on Google Drive (Anyone with link → Viewer)
2. Set GDRIVE_FOLDER_ID in Streamlit secrets  (ưu tiên)
   HOẶC để nguyên — folder IDs mặc định đã được nhúng sẵn bên dưới.
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
# DEFAULT FOLDER IDs (HMK Production)
# Ưu tiên: st.secrets → fallback về giá trị này
# Cho phép deploy trên domain riêng mà không cần config secrets
# ============================================
_DEFAULT_GOLD_FOLDER_ID   = "175rTXS8xpgpW6cECOn6S7mxuor4uLOiq"
_DEFAULT_SILVER_FOLDER_ID = "1aJ1NONGOQXBn4sbXW90E5N4ywt4Gs984"
_DEFAULT_REPORT_FOLDER_ID = "1RUyMgujndsyoRAqhtv6XVURcNGbTR5XL"


def _secret(key: str, default: str = "") -> str:
    """Đọc secret: st.secrets → env var → default hardcoded."""
    try:
        val = st.secrets.get(key, "")
        if val:
            return val
    except Exception:
        pass
    return os.environ.get(key, default)


# ============================================
# DATA DIRECTORY (local cache on Streamlit Cloud)
# ============================================
DATA_DIR = os.path.join(tempfile.gettempdir(), "hmk_lakehouse_cache")
GOLD_DIR = os.path.join(DATA_DIR, "gold")
SILVER_DIR = os.path.join(DATA_DIR, "silver")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")


def _gdown_folder(folder_id: str, output_dir: str, label: str = ""):
    """Download một Google Drive folder vào output_dir."""
    try:
        import gdown
    except ImportError:
        os.system("pip install gdown -q")
        import gdown

    os.makedirs(output_dir, exist_ok=True)
    url = f"https://drive.google.com/drive/folders/{folder_id}"
    try:
        gdown.download_folder(url, output=output_dir, quiet=True, remaining_ok=True)
    except Exception as e:
        st.warning(f"{label} download issue: {str(e)[:120]}")


def _download_from_gdrive():
    """
    Download parquet files từ Google Drive.

    Ưu tiên: GOLD_FOLDER_ID + SILVER_FOLDER_ID (Option B)
    Fallback: LAKEHOUSE_FOLDER_ID — folder cha chứa toàn bộ lakehouse (Option A)
    """
    gold_folder_id   = _secret("GOLD_FOLDER_ID",   _DEFAULT_GOLD_FOLDER_ID)
    silver_folder_id = _secret("SILVER_FOLDER_ID", _DEFAULT_SILVER_FOLDER_ID)
    lake_folder_id   = _secret("LAKEHOUSE_FOLDER_ID", "")

    if gold_folder_id or silver_folder_id:
        # Option B: từng folder riêng
        if gold_folder_id:
            _gdown_folder(gold_folder_id, GOLD_DIR, "Gold")
        if silver_folder_id:
            _gdown_folder(silver_folder_id, SILVER_DIR, "Silver")
    elif lake_folder_id:
        # Option A: folder cha — tải toàn bộ vào DATA_DIR
        # gdown tạo cấu trúc con: DATA_DIR/gold/..., DATA_DIR/silver/...
        _gdown_folder(lake_folder_id, DATA_DIR, "Lakehouse")


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


def _read_parquet_by_pattern(base_dir: str, layer: str) -> pd.DataFrame:
    """
    Tìm parquet files có chứa 'layer' (gold/silver) trong đường dẫn.
    Dùng khi toàn bộ lakehouse được tải vào cùng 1 base_dir.
    """
    all_files = glob.glob(os.path.join(base_dir, "**", "*.parquet"), recursive=True)
    files = [f for f in all_files
             if layer in f.replace("\\", "/").lower()
             and '_delta_log' not in f]

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
    if 'conversation_id' in df.columns:
        df = df.drop_duplicates(subset=['conversation_id'], keep='last')
    return df


def _ensure_data():
    """Check if data exists locally, download if not."""
    if _secret("LAKEHOUSE_FOLDER_ID") and not _secret("GOLD_FOLDER_ID", _DEFAULT_GOLD_FOLDER_ID):
        existing = glob.glob(os.path.join(DATA_DIR, "**", "*.parquet"), recursive=True)
    else:
        existing = glob.glob(os.path.join(GOLD_DIR, "**", "*.parquet"), recursive=True) if os.path.exists(GOLD_DIR) else []

    if not existing:
        with st.spinner("📥 Đang tải dữ liệu từ Google Drive..."):
            _download_from_gdrive()


@st.cache_data(ttl=CACHE_TTL)
def load_all_data() -> dict:
    """
    Load all data: Gold + Silver.
    Downloads from Google Drive on first run.
    """
    _ensure_data()

    # Khi dùng LAKEHOUSE_FOLDER_ID, phân biệt gold/silver qua tên path
    if _secret("LAKEHOUSE_FOLDER_ID") and not _secret("GOLD_FOLDER_ID", _DEFAULT_GOLD_FOLDER_ID):
        gold_df   = _read_parquet_by_pattern(DATA_DIR, "gold")
        silver_df = _read_parquet_by_pattern(DATA_DIR, "silver")
    else:
        gold_df   = _read_parquet_dir(GOLD_DIR)
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
    """Force refresh data từ Google Drive (chỉ clear in-memory cache)."""
    st.cache_data.clear()
    # Không xoá file cache trên disk — tránh mất data khi Drive bị rate-limit.
    # Nếu muốn tải lại hoàn toàn, xoá thủ công: DATA_DIR trong tempdir.
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


@st.cache_data(ttl=CACHE_TTL)
def load_reports() -> list:
    """
    Download và đọc tất cả Daily Report Markdown files từ Google Drive.

    Yêu cầu Streamlit Secret: REPORT_FOLDER_ID
    (chia sẻ folder reports/daily trên Drive với Anyone with link)

    Returns:
        List of dicts: [{'date': 'YYYY-MM-DD', 'filename': str, 'content': str}]
        Trả về [] nếu chưa có Folder ID hoặc không có file nào.
    """
    import re

    report_folder_id = _secret("REPORT_FOLDER_ID", _DEFAULT_REPORT_FOLDER_ID)
    lake_folder_id   = _secret("LAKEHOUSE_FOLDER_ID", "")

    # Nếu không có folder ID nào → không có gì để tải
    if not report_folder_id and not lake_folder_id:
        return []

    os.makedirs(REPORTS_DIR, exist_ok=True)

    # Download folder nếu chưa có file và có REPORT_FOLDER_ID riêng
    md_files = glob.glob(os.path.join(REPORTS_DIR, "**", "*.md"), recursive=True)
    if not md_files and report_folder_id:
        try:
            import gdown
        except ImportError:
            os.system("pip install gdown -q")
            import gdown

        try:
            url = f"https://drive.google.com/drive/folders/{report_folder_id}"
            gdown.download_folder(url, output=REPORTS_DIR, quiet=True, remaining_ok=True)
        except Exception as e:
            st.warning(f"Report download issue: {str(e)[:120]}")

    # Đọc tất cả file .md — tìm trong REPORTS_DIR hoặc DATA_DIR (lakehouse mode)
    if _secret("LAKEHOUSE_FOLDER_ID") and not _secret("REPORT_FOLDER_ID", _DEFAULT_REPORT_FOLDER_ID):
        # Tìm .md bất kỳ đâu trong DATA_DIR có "report" trong path
        md_files = [
            f for f in glob.glob(os.path.join(DATA_DIR, "**", "*.md"), recursive=True)
            if "report" in f.replace("\\", "/").lower()
        ]
    else:
        # Recursive — gdown có thể tạo subfolder con (vd: daily/)
        md_files = glob.glob(os.path.join(REPORTS_DIR, "**", "*.md"), recursive=True)

    reports = []
    date_pattern = re.compile(r'(\d{4}-\d{2}-\d{2})')

    for filepath in md_files:
        filename = os.path.basename(filepath)
        m = date_pattern.search(filename)
        date_str = m.group(1) if m else "unknown"
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            reports.append({
                'date': date_str,
                'filename': filename,
                'content': content,
            })
        except Exception:
            pass

    return reports
