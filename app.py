import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="北美34只精选股看板", layout="wide")

st.title("📊 实时行情综合看板")
st.caption(f"更新时间: {datetime.now().strftime('%H:%M:%S')} | 配色：涨(绿) / 跌(红) / 平(灰)")

# 1. 侧边栏
default_tickers = "AQN.TO, BCE.TO, CEMX.TO, COIN.NE, CRM.NE, CU.TO, ILLM.TO, LIF.NE, XSP.TO, VGRO.TO, UNH.NE, SHOP.TO, T.TO, MSTR.NE, NOWS.NE, AMD, AMZN, AVGO, COIN, COST, CRM, GOOG, LULU, META, MSFT, MSTR, NFLX, NOW, NVDA, PLTR, SHOP, SMCI, TSLA, UNH"
tickers_raw = st.sidebar.text_area("监控名单:", default_tickers, height=150)

if st.sidebar.button("🚀 刷新数据"):
    tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]
    data_results = []
    
    with st.spinner('正在同步数据...'):
        for t in tickers:
            try:
                stock = yf.Ticker(t)
                hist = stock.history(period="2d")
                if hist.empty: continue
                
                current_p = hist['Close'].iloc[-1]
                prev_p = hist['Close'].iloc[-2]
                change = ((current_p - prev_p) / prev_p) * 100
                
                # 统一成交量单位
                vol = stock.fast_info['last_volume']
                vol_str = f"{vol/1e6:.2f}M" if vol >= 1e6 else f"{vol/1e3:.2f}K"

                data_results.append({
                    "代码": t,
                    "价格": round(current_p, 2),
                    "涨跌幅": round(change, 2),
                    "PE": stock.info.get('forwardPE', 'N/A'),
                    "成交量": vol_str
                })
            except: continue

    if data_results:
        df = pd.DataFrame(data_results).sort_values("涨跌幅", ascending=False)

        # --- 第一部分：手动分配颜色的柱状热力图 ---
        st.subheader("🔥 今日涨跌幅分布")
        
        # 核心配色逻辑：根据数值正负直接指定颜色
        # 涨(>0.2%): 绿色 | 跌(<-0.2%): 红色 | 平(-0.2%到0.2%): 深灰色
        colors = []
        for val in df['涨跌幅']:
            if val > 0.2: colors.append('#00FF00') # 绿色
            elif val < -0.2: colors.append('#FF0000') # 红色
            else: colors.append('#404040') # 深灰色基准

        fig = go.Figure(data=[go.Bar(
            x=df['代码'],
            y=df['涨跌幅'],
            marker_color=colors, # 强制应用我们定义的颜色列表
            text=df['涨跌幅'].apply(lambda x: f"{x}%"),
            textposition='outside'
        )])

        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            yaxis_title="涨跌幅 (%)",
            xaxis_tickangle=-45,
            height=400,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # --- 第二部分：实时数据清单 ---
        st.subheader("📋 详细行情数据表")
        
        # 表格颜色函数
        def style_change(val):
            if isinstance(val, (int, float)):
                if val > 0.2: return 'background-color: rgba(0, 255, 0, 0.2); color: #00FF00'
                if val < -0.2: return 'background-color: rgba(255, 0, 0, 0.2); color: #FF0000'
            return 'color: #808080'

        st.dataframe(
            df.style.applymap(style_change, subset=['涨跌幅']),
            use_container_width=True,
            height=800
        )
    else:
        st.error("未获取到数据，请重试。") 
