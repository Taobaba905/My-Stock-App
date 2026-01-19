import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="北美34只精选股看板", layout="wide")

st.title("📊 实时行情综合看板")
st.caption(f"更新时间: {datetime.now().strftime('%H:%M:%S')} | 柱状图说明：向右绿(涨)，向左红(跌)，中心灰")

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
                
                # 成交量单位转换
                vol = fast['last_volume']
                vol_str = f"{vol/1e6:.2f}M" if vol >= 1e6 else f"{vol/1e3:.2f}K"

                data_results.append({
                    "代码": t,
                    "价格": round(current_p, 2),
                    "涨跌幅": round(change, 2), # 这里存数值，用于绘制表格内进度条
                    "PE": stock.info.get('forwardPE', 'N/A'),
                    "成交量": vol_str,
                    "MACD状态": "↗️" if change > 0 else "↘️" # 简化展示
                })
            except: continue

    if data_results:
        df = pd.DataFrame(data_results).sort_values("涨跌幅", ascending=False)

        # --- 核心：表格呈现 ---
        st.subheader("📋 34只股票实时数据清单")

        # 使用 column_config 在表格内嵌入柱状图
        st.data_editor(
            df,
            column_config={
                "代码": st.column_config.TextColumn("代码", help="股票代码", width="small"),
                "价格": st.column_config.NumberColumn("价格", format="$%.2f"),
                "涨跌幅": st.column_config.ProgressColumn(
                    "当日涨跌分布",
                    help="向右绿为涨，向左红为跌",
                    format="%.2f%%",
                    min_value=-5, # 最小值（对应最左侧/红色）
                    max_value=5,  # 最大值（对应最右侧/绿色）
                ),
                "PE": st.column_config.NumberColumn("PE", format="%.2f"),
                "成交量": st.column_config.TextColumn("成交量"),
            },
            hide_index=True,
            use_container_width=True,
            height=1000
        )
        
        st.info("💡 提示：'当日涨跌分布'列中的进度条会自动根据 0 轴左右分布。")
    else:
        st.error("未获取到数据。")
