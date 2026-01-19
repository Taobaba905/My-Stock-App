import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 页面配置
st.set_page_config(page_title="北美股票多维度看板", layout="wide")

st.title("📊 北美股票全能自动看板 (US & CA)")
st.caption(f"数据实时更新 | 包含 P/E, MACD, 统一成交量 | 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 1. 侧边栏配置
st.sidebar.header("⚙️ 配置中心")
# 你可以将下方的默认值替换为你那 34 只股票的代码
default_list = "AAPL, NVDA, TSLA, MSFT, SHOP.TO, TD.TO, RY.TO, BN.NE, CDR.NE, WEED.TO"
ticker_input = st.sidebar.text_area("输入 34 只股票代码 (逗号分隔):", default_list, height=150)
tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

# 2. 工具函数：单位统一化
def format_volume(volume):
    if volume >= 1e6:
        return f"{volume/1e6:.2f} M"
    elif volume >= 1e3:
        return f"{volume/1e3:.2f} K"
    return str(volume)

# 3. 核心计算函数
@st.cache_data(ttl=600)  # 10分钟更新一次
def get_comprehensive_data(ticker_list):
    all_data = []
    progress_bar = st.progress(0)
    
    for idx, t in enumerate(ticker_list):
        try:
            stock = yf.Ticker(t)
            
            # A. 获取基本信息和实时价格 (用于价格、PE、成交量)
            info = stock.info
            fast = stock.fast_info
            
            current_price = fast['last_price']
            prev_close = fast['previous_close']
            change_pct = ((current_price - prev_close) / prev_close) * 100
            
            # B. 计算 MACD (需要获取历史数据)
            # 获取最近 60 天的数据确保 EMA 计算准确
            hist = stock.history(period="60d")
            exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
            exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            
            last_macd = macd.iloc[-1]
            last_signal = signal.iloc[-1]
            macd_status = "🔴 看多 (Bullish)" if last_macd > last_signal else "🟢 看空 (Bearish)"

            # C. 识别市场
            if ".TO" in t or ".V" in t or ".NE" in t:
                market, currency = "🇨🇦 CA", "CAD"
            else:
                market, currency = "🇺🇸 US", "USD"

            all_data.append({
                "代码": t,
                "市场": market,
                "最新价": round(current_price, 2),
                "涨跌幅(%)": round(change_pct, 2),
                "P/E (市盈率)": info.get('forwardPE', 'N/A'),
                "MACD 状态": macd_status,
                "MACD值": round(last_macd, 3),
                "成交量": fast['last_volume'], # 存数值用于排序
                "成交量(格式化)": format_volume(fast['last_volume']),
                "货币": currency
            })
        except:
            continue
        
        progress_bar.progress((idx + 1) / len(ticker_list))
    
    progress_bar.empty()
    return pd.DataFrame(all_data)

# 4. 界面逻辑
if tickers:
    df = get_comprehensive_data(tickers)
    
    if not df.empty:
        # --- 第一部分：涨跌幅热力图 (Treemap) ---
        st.subheader("🔥 市场热力图 (按涨跌幅和成交量大小)")
        fig = px.treemap(df, path=['市场', '代码'], values='成交量',
                         color='涨跌幅(%)', 
                         color_continuous_scale='RdYlGn',
                         color_continuous_midpoint=0,
                         hover_data=['最新价', 'P/E (市盈率)', 'MACD 状态'])
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # --- 第二部分：详细数据列表 ---
        st.subheader("📋 34 只股票详细行情清单")
        
        # 排序功能
        sort_col = st.selectbox("选择排序方式:", ["涨跌幅(%)", "成交量", "P/E (市盈率)"], index=0)
        df_display = df.sort_values(by=sort_col, ascending=False)

        # 表格美化
        def style_positive_negative(v):
            if isinstance(v, (int, float)):
                color = '#ff4b4b' if v > 0 else '#09ab3b'
                return f'color: {color}; font-weight: bold'
            return ''

        st.dataframe(
            df_display.style.applymap(style_positive_negative, subset=['涨跌幅(%)', 'MACD值']),
            column_config={
                "成交量": None, # 隐藏原始数值列
                "最新价": st.column_config.NumberColumn(format="%.2f"),
                "涨跌幅(%)": st.column_config.NumberColumn(format="%.2f%%"),
                "P/E (市盈率)": st.column_config.NumberColumn(format="%.2f"),
            },
            use_container_width=True,
            height=800
        )
    else:
        st.info("请输入正确的股票代码。")
