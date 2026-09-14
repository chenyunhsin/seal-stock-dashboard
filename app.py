import streamlit as st
import pandas as pd
import yfinance as yf

st.title("💡 我的高股息與存股互動儀表板")
st.write("調整下方的持股數量，系統會即時為您分析資產配置與現金流！")

# 1. 讓使用者可以自己在網頁上調整持股（互動式輸入）
st.subheader("🛠️ 調整您的目前持股")
col1, col2, col3 = st.columns(3)

with col1:
    sh_878 = st.number_input("00878 (張)", value=10, min_num=0) * 1000
    sh_888 = st.number_input("00888 永豐ESG (張)", value=11, min_num=0) * 1000
with col2:
    sh_919 = st.number_input("00919 (張)", value=11, min_num=0) * 1000
    sh_2330 = st.number_input("台積電 (零股)", value=3, min_num=0)
with col3:
    sh_2454 = st.number_input("聯發科 (零股)", value=1, min_num=0)

portfolio_data = {
    "Stock": ["00878.TW", "00888.TW", "00919.TW", "2330.TW", "2454.TW"],
    "Name": ["國泰永續高股息", "永豐台灣ESG", "群益台灣精選高息", "台積電", "聯發科"],
    "Shares": [sh_878, sh_888, sh_919, sh_2330, sh_2454],
    "Category": ["高股息ETF", "ESG ETF", "高股息ETF", "半導體個股", "半導體個股"]
}

df_portfolio = pd.DataFrame(portfolio_data)

# 2. 抓取即時股價
@st.cache_data
def get_stock_prices(tickers):
    prices = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            todays_data = stock.history(period="1d")
            price = todays_data['Close'].iloc[0] if not todays_data.empty else 0
            prices[ticker] = round(price, 2)
        except Exception:
            prices[ticker] = 0
    return prices

with st.spinner("正在連線 Yahoo Finance 取得最新股價..."):
    current_prices = get_stock_prices(df_portfolio["Stock"].tolist())

df_portfolio["Current_Price"] = df_portfolio["Stock"].map(current_prices)
df_portfolio["Total_Value"] = df_portfolio["Shares"] * df_portfolio["Current_Price"]

# 3. 呈現總覽與圖表
st.subheader("📊 資產市值統計")
st.dataframe(df_portfolio[["Name", "Shares", "Current_Price", "Total_Value"]], use_container_width=True)

total_asset = df_portfolio["Total_Value"].sum()
st.metric(label="總股票市值 (TWD)", value=f"${total_asset:,.0f}")

# 4. 智慧建議與互動回饋 (AI 建議模組)
st.subheader("🤖 投資組合分析與建議")

etf_value = df_portfolio[df_portfolio["Category"].str.contains("ETF")]["Total_Value"].sum()
stock_value = df_portfolio[df_portfolio["Category"].str.contains("個股")]["Total_Value"].sum()

if total_asset > 0:
    etf_ratio = (etf_value / total_asset) * 100
    stock_ratio = (stock_value / total_asset) * 100
    
    st.info(f"目前的資產配置：**高股息/ETF 佔 {etf_ratio:.1f}%**，**個股(台積電/聯發科) 佔 {stock_ratio:.1f}%**")
    
    # 給予客製化建議
    if etf_ratio > 85:
        st.markdown("✅ **建議方向**：你的組合高度集中在高股息 ETF（00878、00888、00919），這能帶來非常穩定的季配息現金流，適合作為防守型配置。不過因為三檔屬性略有重疊，未來若要增加新資金，可考慮配置不同產業或美股 ETF 來分散風險。")
    else:
        st.markdown("⚠️ **建議方向**：你的個股比例相對較高，雖然成長潛力大，但波動也會隨之增加。若追求穩健現金流，可以持續以月月配高股息 ETF 為核心加碼。")
else:
    st.warning("目前尚無有效市值資料，請檢查網路連線或代號是否正確。")