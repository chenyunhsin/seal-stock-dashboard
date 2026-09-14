import streamlit as st
import pandas as pd
import yfinance as yf

st.title("💡 全台股/ETF 智慧存股計算機")
st.write("直接在下方框框輸入代號或名稱（例如：台積電、00888、聯發科），系統會自動搜尋提示！")

# Initialize session state for portfolio
if "portfolio" not in st.session_state:
    st.session_state.portfolio = []

# Comprehensive list of popular Taiwan stocks and ETFs for autocomplete search
# Format: "Display Name (Code)" -> Code
stock_database = {
    "0050 元大台灣50": "0050",
    "0056 元大高股息": "0056",
    "00713 元大台灣高息低波": "00713",
    "00878 國泰永續高股息": "00878",
    "00888 富邦台灣優質高息": "00888",
    "00919 群益台灣精選高息": "00919",
    "00929 復華台灣科技優息": "00929",
    "00940 元大台灣價值高息": "00940",
    "2330 台積電": "2330",
    "2454 聯發科": "2454",
    "2317 鴻海": "2317",
    "2412 中華電": "2412",
    "2881 富邦金": "2881",
    "2882 國泰金": "2882",
    "2891 中信金": "2891",
    "3037 欣興": "3037",
    "2308 台達電": "2308",
    "3711 日月光投控": "3711"
}

# Helper function to fetch price and validate suffix (.TW / .TWO)
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

# 1. Autocomplete Search Selection Interface
st.subheader("➕ 新增持股")
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    # st.selectbox acts as an autocomplete search box when typing inside it
    selected_option = st.selectbox(
        "搜尋股票名稱或代號",
        options=list(stock_database.keys()),
        index=0,
        help="您可以直接在此輸入中文名稱或 4 碼代號進行搜尋"
    )
    raw_ticker = stock_database[selected_option]
    stock_name = selected_option.split(" ", 1)[1] # Extract stock name

with col2:
    input_shares = st.number_input("持有股數 (或零股數)", min_value=1, value=1000, step=1)

with col3:
    st.write("")
    st.write("")
    add_btn = st.button("加入清單")

if add_btn:
    # Validate market data before adding to portfolio
    valid_ticker, test_price = get_stock_price(raw_ticker)
    
    if not valid_ticker or test_price == 0.0:
        st.error(f"無法取得代號 「{raw_ticker}」 的市場資料，請確認代號是否正確！")
    else:
        category = "ETF" if raw_ticker.startswith(('00', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9')) else "個股"
        
        existing_item = next((item for item in st.session_state.portfolio if item["Stock"] == valid_ticker), None)
        if existing_item:
            existing_item["Shares"] += input_shares
        else:
            st.session_state.portfolio.append({
                "Stock": valid_ticker,
                "Name": stock_name,
                "Shares": input_shares,
                "Category": category
            })
        st.success(f"成功加入 {stock_name}！")
        st.rerun()

# 2. Display portfolio and real-time prices
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

    # 3. Portfolio Insights & Suggestions
    st.subheader("🤖 資產配置與現金流建議")
    if total_asset > 0:
        etf_mask = df_current["Category"].str.contains("ETF", na=False)
        etf_value = df_current[etf_mask]["Total_Value"].sum()
        etf_ratio = (etf_value / total_asset) * 100
        
        st.info(f"目前的資產配置：**ETF 類佔 {etf_ratio:.1f}%**")
        
        if etf_ratio > 85:
            st.markdown("✅ **建議方向**：組合高度集中在高股息或市值型 ETF，現金流與穩定度表現優秀，非常適合長期存股與抗波動。")
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
    st.info("目前還沒有加入任何持股，請從上方搜尋框選擇並加入！")
