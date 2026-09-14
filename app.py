import streamlit as st
import pandas as pd
import yfinance as yf

st.title("💡 全台股/ETF 智慧存股計算機")
st.write("你可以從常用清單選擇，或直接輸入任意 4 碼台股代號來查詢與計算！")

# Initialize session state
if "portfolio" not in st.session_state:
    st.session_state.portfolio = []

# Popular stock choices for quick selection
stock_options = {
    "00878 國泰永續高股息": "00878",
    "00888 富邦台灣優質高息": "00888",
    "00919 群益台灣精選高息": "00919",
    "2330 台積電": "2330",
    "2454 聯發科": "2454",
    "0050 元大台灣50": "0050",
    "0056 元大高股息": "0056"
}

# 1. Selection interface supporting both preset and custom 4-digit code
st.subheader("➕ 新增持股")
input_mode = st.radio("選擇輸入方式", ["從常用清單選擇", "自行輸入 4 碼代號"], horizontal=True)

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    if input_mode == "從常用清單選擇":
        selected_label = st.selectbox("選擇股票 / ETF", list(stock_options.keys()))
        raw_ticker = stock_options[selected_label]
        stock_name = selected_label.split(" ")[1]
    else:
        raw_ticker = st.text_input("輸入台股 4 碼代號 (例如 00888, 2330)", value="").strip()
        stock_name = f"代號 {raw_ticker}"

with col2:
    input_shares = st.number_input("持有股數 (或零股數)", min_value=1, value=1000, step=1)

with col3:
    st.write("")
    st.write("")
    add_btn = st.button("加入清單")

if add_btn and raw_ticker:
    # Format ticker for Yahoo Finance with fallback handling (.TW / .TWO)
    ticker = f"{raw_ticker}.TW"
    
    existing_item = next((item for item in st.session_state.portfolio if item["Stock"] == ticker), None)
    if existing_item:
        existing_item["Shares"] += input_shares
    else:
        category = "ETF" if raw_ticker.startswith(('00', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9')) else "個股"
        st.session_state.portfolio.append({
            "Stock": ticker,
            "Name": stock_name,
            "Shares": input_shares,
            "Category": category
        })
    st.rerun()

# 2. Display portfolio and robust price fetching
st.subheader("📊 目前持股清單")

if len(st.session_state.portfolio) > 0:
    df_current = pd.DataFrame(st.session_state.portfolio)

    @st.cache_data
    def get_stock_price(ticker):
        try:
            # Try .TW first
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            if not hist.empty:
                return round(float(hist['Close'].iloc[-1]), 2)
            
            # Fallback to .TWO if .TW returns empty (fixes 00888 issue)
            alt_ticker = ticker.replace(".TW", ".TWO")
            stock_alt = yf.Ticker(alt_ticker)
            hist_alt = stock_alt.history(period="5d")
            if not hist_alt.empty:
                return round(float(hist_alt['Close'].iloc[-1]), 2)
        except Exception:
            pass
        return 0.0

    with st.spinner("正在取得最新股價（含 00888 專屬修正）..."):
        prices = [get_stock_price(ticker) for ticker in df_current["Stock"]]

    df_current["Current_Price"] = prices
    df_current["Total_Value"] = df_current["Shares"] * df_current["Current_Price"]

    df_display = df_current[["Name", "Stock", "Shares", "Current_Price", "Total_Value"]].copy()
    df_display.columns = ["名稱", "代號", "股數", "即時股價", "總市值"]
    st.dataframe(df_display, use_container_width=True)

    total_asset = df_current["Total_Value"].sum()
    st.metric(label="總股票市值 (TWD)", value=f"${total_asset:,.0f}")

    if st.button("清空所有持股"):
        st.session_state.portfolio = []
        st.rerun()
else:
    st.info("目前還沒有加入任何持股，請從上方選擇或輸入代號加入！")
