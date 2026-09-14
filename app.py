import streamlit as st
import pandas as pd
import yfinance as yf

st.title("💡 我的自訂高股息與存股互動儀表板")
st.write("你可以直接在下方的表格中修改股數、新增或刪除任何持股！")

# Initial portfolio data for dynamic editing
initial_data = {
    "Stock": ["00878.TW", "00888.TW", "00919.TW", "2330.TW", "2454.TW"],
    "Name": ["國泰永續高股息", "永豐台灣ESG", "群益台灣精選高息", "台積電", "聯發科"],
    "Shares": [10000, 11000, 11000, 3, 1],
    "Category": ["高股息ETF", "ESG ETF", "高股息ETF", "半導體個股", "半導體個股"]
}

df_initial = pd.DataFrame(initial_data)

# 1. Allow users to dynamically edit, add, or delete rows
st.subheader("🛠️ 動態持股編輯器")
edited_df = st.data_editor(df_initial, num_rows="dynamic", use_container_width=True)

# 2. Fetch stock prices using a more robust method (fast_info with history fallback)
@st.cache_data
def get_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        # Try fast_info first for reliable current price
        if hasattr(stock, "fast_info") and "lastPrice" in stock.fast_info:
            price = stock.fast_info["lastPrice"]
            if price:
                return round(float(price), 2)
        
        # Fallback to history if fast_info is unavailable
        hist = stock.history(period="5d")
        if not hist.empty:
            return round(float(hist['Close'].iloc[-1]), 2)
    except Exception:
        pass
    return 0.0

# Calculate prices and total values based on user input
with st.spinner("正在向 Yahoo Finance 取得最新股價..."):
    prices = [get_stock_price(ticker) for ticker in edited_df["Stock"]]

edited_df["Current_Price"] = prices
edited_df["Total_Value"] = edited_df["Shares"] * edited_df["Current_Price"]

# 3. Display summary table
st.subheader("📊 即時資產市值統計")
df_display = edited_df[["Name", "Stock", "Shares", "Current_Price", "Total_Value"]].copy()
df_display.columns = ["股票名稱", "代號", "持有股數", "即時股價", "總市值"]
st.dataframe(df_display, use_container_width=True)

total_asset = edited_df["Total_Value"].sum()
st.metric(label="總股票市值 (TWD)", value=f"${total_asset:,.0f}")

# 4. Investment insights
st.subheader("🤖 資產配置建議")
if total_asset > 0:
    etf_mask = edited_df["Category"].str.contains("ETF", na=False)
    etf_value = edited_df[etf_mask]["Total_Value"].sum()
    etf_ratio = (etf_value / total_asset) * 100
    
    st.info(f"目前的資產配置：**ETF 類佔 {etf_ratio:.1f}%**")
    
    if etf_ratio > 85:
        st.markdown("✅ **建議方向**：組合高度集中在穩定配息的 ETF，現金流表現優秀，適合長期存股。")
    else:
        st.markdown("⚠️ **建議方向**：個股比例較高，波動可能較大，可視個人風險屬性調整。")
else:
    st.warning("目前尚無有效市值資料，請檢查股票代號是否正確（台股需加上 .TW，例如 00888.TW）。")