import streamlit as st
import pandas as pd
import yfinance as yf

# 網頁標題
st.title("我的高股息 ETF 與存股資產分析儀表板")

# 1. 建立你的持股資料
# 台灣 ETF 在 Yahoo Finance 的代號通常是 4碼數字加上 .TW (例如 00878.TW)
portfolio_data = {
    "Stock": ["00878", "00888", "00919", "2330", "2454"],
    "Name": ["國泰永續高股息", "富邦台灣優質高息", "群益台灣精選高息", "台積電", "聯發科"],
    "Shares": [10000, 11000, 11000, 3, 1], # 10張=10000股，零股直接填股數
    "Type": ["ETF (季配)", "ETF (季配)", "ETF (季配)", "個股", "個股"]
}

df_portfolio = pd.DataFrame(portfolio_data)

# 2. 抓取即時股價
@st.cache_data
def get_stock_prices(tickers):
    prices = {}
    for ticker in tickers:
        try:
            # 加上 .TW 抓取台股資料
            stock = yf.Ticker(f"{ticker}.TW")
            # 取得最新收盤價
            todays_data = stock.history(period="1d")
            price = todays_data['Close'].iloc[0] if not todays_data.empty else 0
            prices[ticker] = round(price, 2)
        except Exception:
            prices[ticker] = 0
    return prices

# 取得目前股價字典
with st.spinner("正在取得最新股價數據..."):
    current_prices = get_stock_prices(df_portfolio["Stock"].tolist())

# 將股價對應回 DataFrame
df_portfolio["Current_Price"] = df_portfolio["Stock"].map(current_prices)
df_portfolio["Total_Value"] = df_portfolio["Shares"] * df_portfolio["Current_Price"]

# 3. 呈現持股總覽表格
st.subheader("📊 目前持股市值總覽")
st.dataframe(df_portfolio, use_container_width=True)

# 4. 計算總資產
total_asset = df_portfolio["Total_Value"].sum()
st.metric(label="總股票市值 (TWD)", value=f"${total_asset:,.0f}")

# 5. 簡單的月月配組合視覺化提示
st.subheader("💡 組合亮點")
st.markdown("""
- **00878**、**00888**、**00919** 皆為台股熱門的季配息 ETF，透過錯開除息月份，確實能有效達到**「季季配 / 組合月月配」**的現金流效果。
- 搭配少數的**台積電**與**聯發科**零股，可以在賺取高股息現金流的同時，兼顧半導體權值股的成長潛力。
""")