import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import json

# Set page configuration for better mobile display
st.set_page_config(page_title="存股現金流與資產儀表板", page_icon="📈", layout="centered")

st.title("📈 高股息存股與現金流儀表板")
st.markdown("專為存股族打造的行動版資產管理工具，支援資料匯入/匯出與即時分析。")

# Initialize session state for portfolio
if "portfolio" not in st.session_state:
    st.session_state.portfolio = []

# Stock database for search autocomplete
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
    "2891 中信金": "2891"
}

# Robust price fetching function (.TW / .TWO fallback)
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

# --- Section 1: Backup & Restore (Fixing re-entry hassle) ---
with st.expander("💾 資料存檔與快速還原 (免重新輸入)"):
    col_exp, col_imp = st.columns(2)
    with col_exp:
        if len(st.session_state.portfolio) > 0:
            # Export portfolio to JSON
            portfolio_json = json.dumps(st.session_state.portfolio, ensure_ascii=False)
            st.download_button(
                label="📥 下載目前持股備份",
                data=portfolio_json,
                file_name="my_portfolio.json",
                mime="application/json"
            )
        else:
            st.info("目前無資料可備份")
            
    with col_imp:
        # Import portfolio from JSON
        uploaded_file = st.file_uploader("📤 上傳備份檔案還原", type=["json"])
        if uploaded_file is not None:
            try:
                loaded_data = json.load(uploaded_file)
                st.session_state.portfolio = loaded_data
                st.success("資料還原成功！")
                st.rerun()
            except Exception as e:
                st.error("檔案格式錯誤，無法讀取。")

st.markdown("---")

# --- Section 2: Add Holdings ---
st.subheader("➕ 新增持股")
selected_option = st.selectbox(
    "搜尋股票名稱或代號",
    options=list(stock_database.keys()),
    help="點擊並輸入關鍵字即可快速搜尋"
)
raw_ticker = stock_database[selected_option]
stock_name = selected_option.split(" ", 1)[1]

input_shares = st.number_input("持有股數 (或零股數)", min_value=1, value=1000, step=1)

if st.button("加入 / 更新至清單", type="primary", use_container_width=True):
    valid_ticker, test_price = get_stock_price(raw_ticker)
    
    if not valid_ticker or test_price == 0.0:
        st.error(f"無法取得代號 「{raw_ticker}」 的市場資料，請確認！")
    else:
        category = "高股息/ETF" if raw_ticker.startswith(('00', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9')) and int(raw_ticker[:2]) < 20 else "個股"
        
        existing_item = next((item for item in st.session_state.portfolio if item["Stock"] == valid_ticker), None)
        if existing_item:
            existing_item["Shares"] = input_shares # Update to exact input
        else:
            st.session_state.portfolio.append({
                "Stock": valid_ticker,
                "Name": stock_name,
                "Shares": input_shares,
                "Category": category
            })
        st.success(f"已成功更新 {stock_name}！")
        st.rerun()

st.markdown("---")

# --- Section 3: Portfolio Overview & Charts ---
st.subheader("📊 資產總覽與分佈")

if len(st.session_state.portfolio) > 0:
    df_current = pd.DataFrame(st.session_state.portfolio)

    with st.spinner("正在連線取得最新即時股價..."):
        prices = []
        for raw_item in df_current["Stock"]:
            code = raw_item.split(".")[0]
            _, p = get_stock_price(code)
            prices.append(p)

    df_current["Current_Price"] = prices
    df_current["Total_Value"] = df_current["Shares"] * df_current["Current_Price"]

    # Display clean table
    df_display = df_current[["Name", "Stock", "Shares", "Current_Price", "Total_Value"]].copy()
    df_display.columns = ["名稱", "代號", "股數", "即時股價", "總市值"]
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    total_asset = df_current["Total_Value"].sum()
    st.metric(label="總股票市值 (TWD)", value=f"${total_asset:,.0f}")

    # Rich Visualizations: Plotly Pie Chart
    if total_asset > 0:
        fig = px.pie(
            df_current, 
            values="Total_Value", 
            names="Name", 
            title="資產配置比例圓餅圖",
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- Section 4: Enhanced Insights & Dividend Estimation ---
    st.subheader("🤖 智能分析與現金流預估")
    if total_asset > 0:
        etf_mask = df_current["Category"].str.contains("ETF", na=False)
        etf_value = df_current[etf_mask]["Total_Value"].sum()
        etf_ratio = (etf_value / total_asset) * 100
        
        # Rough estimated annual dividend simulation (assuming average 6% yield for high-dividend ETFs, 2.5% for stocks)
        estimated_annual_dividend = 0
        for _, row in df_current.iterrows():
            yield_rate = 0.065 if "ETF" in row["Category"] else 0.03
            estimated_annual_dividend += row["Total_Value"] * yield_rate

        col_inf1, col_inf2 = st.columns(2)
        with col_inf1:
            st.metric("預估年度總股息", f"${estimated_annual_dividend:,.0f}")
        with col_inf2:
            st.metric("預估平均每月現金流", f"${estimated_annual_dividend / 12:,.0f}")

        st.info(f"目前的資產配置：**高股息/ETF 佔 {etf_ratio:.1f}%**")
        
        if etf_ratio >= 80:
            st.markdown("✅ **現金流策略**：高度聚焦高股息資產，具備極佳的被動收入防禦力與季配現金流。")
        else:
            st.markdown("⚖️ **平衡策略**：兼顧成長股與高股息，資產抗震與成長動能兼具。")

    if st.button("🗑️ 清空所有持股紀錄", use_container_width=True):
        st.session_state.portfolio = []
        st.rerun()
else:
    st.info("目前尚無持股，請透過上方選單搜尋並加入股票！")
