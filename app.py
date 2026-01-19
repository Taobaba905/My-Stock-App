import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="北美34只精选股看板", layout="wide")

st.title("📊 股票实时看板 (自定义热力渐变版)")

# 1. 侧边栏配置
default_tickers = "AQN.TO, BCE.TO, CEMX.TO, COIN.NE, CRM.NE, CU.TO, ILLM.TO, LIF.NE, XSP.TO, VGRO.TO, UNH.NE, SHOP.TO, T.TO, MSTR.NE, NOWS.NE, AMD, AMZN, AVGO, COIN, COST, CRM, GOOG, LULU, META, MSFT, MSTR, NFLX, NOW, NVDA, PLTR, SHOP, SMCI, TSLA, UNH"
tickers_raw = st.sidebar.text_area("监控名单:", default_tickers, height=150)

if st.sidebar.button("🚀 刷新数据"):
    tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]
    data_results = []
    
    with st.spinner('正在同步 34 只股票数据...'):
        for t in tickers:
            try:
                stock = yf.Ticker(t)
                fast = stock.fast_info
                hist = stock.history(period="2d")
                if hist.empty: continue
                
                # 计算涨跌
                current_p = hist['Close'].iloc[-1]
                prev_p = hist['Close'].iloc[-2]
                change = ((current_p - prev_p) / prev_p) * 100
                
                # 成交量
                vol = fast['last_volume']
                vol_str = f"{vol/1e6:.2f}M" if vol >= 1e6 else f"{vol/1e3:.2f}K"

                data_results.append({
                    "代码": t,
                    "当前价格": round(current_p, 2),
                    "涨跌幅(%)": round(change, 2),
                    "PE": stock.info.get('forwardPE', 'N/A'),
                    "成交量": vol_str
                })
            except: continue

    if data_results:
        df = pd.DataFrame(data_results).sort_values("涨跌幅(%)", ascending=False)

        # --- 第一部分：自定义颜色热力柱状图 ---
        st.subheader("🔥 今日涨跌幅分布热力图")
        
        # 核心配色：[0%位置, 红色] -> [50%位置(即0轴), 深灰] -> [100%位置, 绿色]
        # range_color=[-3, 3] 意味着 -3% 是全红，0% 是深灰，3% 是全绿
        custom_color_scale = [
            [0.0, "#FF0000"],    # 跌深：红色
            [0.5, "#404040"],    # 零轴：深灰色
            [1.0, "#00FF00"]     # 涨深：绿色
        ]

        fig = px.bar(
            df, x="代码", y="涨跌幅(%)", color="涨跌幅(%)",
            color_continuous_scale=custom_color_scale,
            range_color=[-3, 3], 
            text_auto='.2f'
        )
        
        # 美化图表
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_tickangle=-45,
            coloraxis_showscale=False, # 隐藏旁边的颜色条，让界面更干净
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # --- 第二部分：实时数据清单 (紧跟在图表下方) ---
        st.subheader("📋 详细行情数据表")
        
        # 表格里的数字也加上颜色逻辑
        def color_df(val):
            if isinstance(val, (int, float)):
                if val > 0: return 'color: #00FF00'
                if val < 0: return 'color: #FF0000'
                return 'color: #808080'
            return ''

        st.dataframe(
            df.style.applymap(color_df, subset=['涨跌幅(%)']),
            use_container_width=True,
            height=600
        )
    else:
        st.error("未获取到数据，请重试。")
