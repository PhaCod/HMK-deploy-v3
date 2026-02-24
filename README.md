# HMK Optical Chat Analytics — Streamlit Cloud

Dashboard phân tích hội thoại kính mắt HMK Optical.
**Data pipeline**: Colab GPU → Google Drive → Streamlit Cloud.

## Deploy lên Streamlit Cloud

### Bước 1: Push lên GitHub
```bash
cd streamlit-cloud
git init
git add .
git commit -m "Initial dashboard deploy"
git remote add origin https://github.com/YOUR_USERNAME/hmk-analytics-dashboard.git
git push -u origin main
```

### Bước 2: Chia sẻ data trên Google Drive
1. Mở Google Drive → `chat-analytics/lakehouse/gold/ai_unified_v6/`
2. Click phải → **Share** → **Anyone with the link** → **Viewer**
3. Copy URL → lấy **folder ID** (phần sau `/folders/`)
4. Làm tương tự cho folder `silver/conversations/`

### Bước 3: Deploy trên Streamlit Cloud
1. Vào [share.streamlit.io](https://share.streamlit.io)
2. **New app** → chọn repo GitHub
3. **Main file path**: `app.py`
4. **Advanced settings → Secrets**:
```toml
GOLD_FOLDER_ID = "1abc_YOUR_GOLD_FOLDER_ID"
SILVER_FOLDER_ID = "1xyz_YOUR_SILVER_FOLDER_ID"
```
5. Click **Deploy**!

## Cấu trúc

```
streamlit-cloud/
├── app.py                  # Main entry
├── requirements.txt        # Dependencies
├── .streamlit/
│   └── secrets.toml        # Google Drive folder IDs
├── config/
│   ├── settings.py         # App settings, tab names, colors
│   └── styles.py           # CSS styles
├── data/
│   └── loader.py           # Google Drive → Parquet loader
├── components/
│   ├── sidebar.py          # Sidebar filters
│   └── drill_down.py       # Drill-down component
├── tabs/
│   ├── tab_executive.py    # 📈 Executive overview
│   ├── tab_customer_intel.py # 🧠 Customer intelligence
│   ├── tab_conversion.py   # 🔄 Conversion funnel
│   ├── tab_sentiment.py    # 💬 Sentiment analysis
│   ├── tab_agent.py        # 👥 Agent performance
│   ├── tab_revenue.py      # 💰 Revenue insights
│   └── tab_explorer.py     # 🔍 Data explorer
└── utils/
    ├── charts.py           # Chart utilities
    └── helpers.py          # Helper functions
```

## Update data
Mỗi khi chạy pipeline trên Colab xong, nhấn nút 🔄 trên dashboard để refresh data mới.
