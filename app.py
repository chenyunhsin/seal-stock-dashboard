import streamlit as st
import pandas as pd
import yfinance as yf

st.title("💡 輕鬆存股計算機")
st.write("從下方選單點選股票或 ETF，輸入持有股數，即可為您計算資產與分析！")

# Initialize session state to store portfolio items dynamically
if "portfolio" not in st.session_state:
    st.session_state.portfolio = []

# Popular stock choices for selection (no manual typing needed)
popular_stocks = {
    "00878.TW - 國泰永續高股息": "00878.TW",
    "00888.TW - 永豐台灣ESG": "00888.TW",
    "00919.TW - 群益台灣精選高息": "00919.TW",
    "2330.TW - 台積電": "2330.TW",
    "2454.TW - 聯發科": "2454.TW",
    "0050.TW - 元大台灣50": "0050.TW",
    "0056.TW - 元大高股息": "0056.TW"
}

# 1. Interactive selection interface (Click-to-add)
st.subheader("➕ 新增持股")
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    selected_label = st.selectbox("選擇股票 / ETF", list(popular_stocks.keys()))
    selected_ticker = popular_stocks[selected_label]
    # Extract name for display
    stock_name = selected_label.split(" - ")[1]
with col2:
    input_shares = st.number_input("持有股數 (或零股數)", min_value=1, value=1000, step=1)
with col3:
    st.write("") # Spacing
    st.write("")
    add_btn = st.button("加入清單")

if add_btn:
    # Check if ticker already exists, update shares if it does
    existing_item = next((item for item in st.session_state.portfolio if item["Stock"] == selected_ticker), None)
    if existing_item:
        existing_item["Shares"] += input_shares
    else:
        # Determine category based on ticker
        category = "高股息ETF" if "00" in selected_ticker else "個股"
        st.session_state.portfolio.append({
            "Stock": selected_ticker,
            "Name": stock_name,
            "Shares": input_shares,
            "Category": category
        })
    st.rerun()

# 2. Display and manage current portfolio
st.subheader("📊 目前持股清單")

if len(st.session_state.portfolio) > 0:
    df_current = pd.DataFrame(st.session_state.portfolio)

    # Robust price fetching function
    @st.cache_data
    def get_stock_price(ticker):
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1mo")
            if not hist.empty:
                return round(float(hist['Close'].iloc[-1]), 2)
        except Exception:
            pass
        return 0.0

    with st.spinner("正在取得最新股價..."):
        prices = [get_stock_price(ticker) for ticker in df_current["Stock"]]

    df_current["Current_Price"] = prices
    df_current["Total_Value"] = df_current["Shares"] * df_current["Current_Price"]

    # Show table
    df_display = df_current[["Name", "Stock", "Shares", "Current_Price", "Total_Value"]].copy()
    df_display.columns = ["名稱", "代號", "股數", "即時股價", "總市值"]
    st.dataframe(df_display, use_container_width=True)

    total_asset = df_current["Total_Value"].sum()
    st.metric(label="總股票市值 (TWD)", value=f"${total_asset:,.0f}")

    # Clear portfolio button
    if st.button("清空所有持股"):
        st.session_state.portfolio = []
        st.rerun()

    # 3. Simple insights
    st.subheader("🤖 資產配置建議")
    etf_mask = df_current["Category"].str.contains("ETF", na=False)
    etf_value = df_current[etf_mask]["Total_Value"].sum()
    etf_ratio = (etf_value / total_asset) * 100 if total_asset > 0 else 0
    
    st.info(f"目前的資產配置：**ETF 類佔 {etf_ratio:.1f}%**")
    if etf_ratio > 85:
        st.markdown("✅ **建議方向**：組合高度集中在穩定配息的 ETF，適合追求現金流的長期配置。")
    else:
        st.markdown("⚠️ **建議方向**：個股比例較高，波動可能較大，可視個人風險屬性調整。")
else:
    st.info("目前還沒有加入任何持股，請從上方選單選擇並加入！")
