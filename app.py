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

# Helper function to fetch price with validation (.TW / .TWO)
@st.cache_data
def get_stock_price(raw_ticker):
    tickers_to_try = [f"{raw_ticker}.TW", f"{raw_ticker}.TWO"]
    for ticker in tickers_to_try:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            if not hist.empty:
                price = float(hist['Close'].iloc[-1])
                if price > 0:
                    return ticker, round(price, 2)
        except Exception:
            continue
    return None, 0.0

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
    # Validate ticker and get correct suffix before adding
    valid_ticker, test_price = get_stock_price(raw_ticker)
    
    if not valid_ticker or test_price == 0.0:
        st.error(f"找不到代號 「{raw_ticker}」 的市場資料，請確認代號是否正確！")
    else:
        # If user used custom input, try to get a cleaner name if possible or use default
        if input_mode == "自行輸入 4 碼代號":
            stock_name = f"台股 {raw_ticker}"
            
        existing_item = next((item for item in st.session_state.portfolio if item["Stock"] == valid_ticker), None)
        if existing_item:
            existing_item["Shares"] += input_shares
        else:
            category = "ETF" if raw_ticker.startswith(('00', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9')) else "個股"
            st.session_state.portfolio.append({
                "Stock": valid_ticker,
                "Name": stock_name,
                "Shares": input_shares,
                "Category": category
            })
        st.success(f"成功加入 {stock_name}！")
        st.rerun()

# 2. Display portfolio and robust price fetching
st.subheader("📊 目前持股清單")

if len(st.session_state.portfolio) > 0:
    df_current = pd.DataFrame(st.session_state.portfolio)

    with st.spinner("正在取得最新股價..."):
        prices = []
        for raw_item in df_current["Stock"]:
            code = raw_item.split(".")[0]
            _, p = get_stock_price(code)
            prices.append(p)

    df_current["Current_Price"] = prices
    df_current["Total_Value"] = df_current["Shares"] * df_current["Current_Price"]

    df_display = df_current[["Name", "Stock", "Shares", "Current_Price", "Total_Value"]].copy()
    df_display.columns = ["名稱", "代號", "股數", "即時股價", "總市值"]
    st.dataframe(df_display, use_container_width=True)

    total_asset = df_current["Total_Value"].sum()
    st.metric(label="總股票市值 (TWD)", value=f"${total_asset:,.0f}")

    # 3. Restored Portfolio Insights & Suggestions
    st.subheader("🤖 資產配置與現金流建議")
    if total_asset > 0:
        etf_mask = df_current["Category"].str.contains("ETF", na=False)
        etf_value = df_current[etf_mask]["Total_Value"].sum()
        etf_ratio = (etf_value / total_asset) * 100
        
        st.info(f"目前的資產配置：**ETF 類佔 {etf_ratio:.1f}%**")
        
        if etf_ratio > 85:
            st.markdown("✅ **建議方向**：你的組合高度集中在高股息或市值型 ETF，現金流與穩定度表現優秀，非常適合長期存股與抗波動。")
        elif etf_ratio >= 50:
            st.markdown("⚖️ **建議方向**：組合兼具 ETF 的穩定配息與個股的成長潛力，配置均衡。")
        else:
            st.markdown("⚠️ **建議方向**：個股比例較高，雖然成長爆發力強，但波動相對較大，若追求穩健現金流可考慮適度增加 ETF 比重。")
    else:
        st.warning("目前持股市值為 0，請檢查股價資料或股數。")

    if st.button("清空所有持股"):
        st.session_state.portfolio = []
        st.rerun()
else:
    st.info("目前還沒有加入任何持股，請從上方選擇或輸入代號加入！")
