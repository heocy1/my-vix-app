import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. 앱 설정
st.set_page_config(page_title="퇴직연금 매수기", layout="centered")

st.markdown("""
    <style>
    .main .block-container {padding-top: 1.5rem; padding-bottom: 1rem;}
    .main-title {
        font-size: 1.6rem !important; 
        font-weight: 700; 
        text-align: center; 
        margin-bottom: 1.2rem;
        color: #ffffff;
    }
    .metric-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 10px;
        text-align: center;
        background-color: #1e1e1e;
        border-radius: 10px;
    }
    .metric-table th {
        background-color: #333;
        padding: 8px;
        font-size: 0.8rem;
        color: #bbb;
    }
    .metric-table td {
        padding: 12px;
        font-size: 1.2rem;
        font-weight: 700;
        border-bottom: 1px solid #444;
    }
    .drop-val { color: #ff4b4b; }
    .stButton>button {
        width: 100%; 
        border-radius: 8px; 
        height: 3.5em; 
        background-color: #2e7d32; 
        color: white; 
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">📉 퇴직연금 매수 가이드</p>', unsafe_allow_html=True)

# 2. 데이터 가져오기 (실시간 지표 + 3개월 히스토리)
@st.cache_data(ttl=3600)
def get_market_data():
    tickers = {"VIX": "^VIX", "S&P500": "^GSPC", "Nasdaq100": "^NDX"}
    data = {}
    charts = {}
    for name, symbol in tickers.items():
        ticker = yf.Ticker(symbol)
        # 실시간용 (1년치로 고점 계산)
        hist_1y = ticker.history(period="1y")
        current = hist_1y['Close'].iloc[-1]
        high = hist_1y['High'].max()
        drop = ((current - high) / high) * 100
        data[name] = {"current": current, "drop": drop}
        
        # 차트용 (최근 3개월)
        charts[name] = ticker.history(period="3mo")
    return data, charts

market, charts = get_market_data()

# 3. 상단 지수 표
st.markdown(f"""
<table class="metric-table">
    <tr>
        <th>VIX 지수</th>
        <th>S&P 500 하락률</th>
        <th>Nasdaq 100 하락률</th>
    </tr>
    <tr>
        <td>{market['VIX']['current']:.2f}</td>
        <td class="drop-val">{market['S&P500']['drop']:.1f}%</td>
        <td class="drop-val">{market['Nasdaq100']['drop']:.1f}%</td>
    </tr>
</table>
""", unsafe_allow_html=True)

# 4. [신규] 3개월 차트 섹션
with st.expander("📈 지수별 3개월 흐름 보기", expanded=False):
    tab1, tab2 = st.tabs(["S&P 500", "Nasdaq 100"])
    
    def create_chart(df, title):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name=title, line=dict(color='#00ff88', width=2)))
        fig.update_layout(
            height=250, margin=dict(l=0, r=0, t=20, b=0),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, font=dict(size=10)),
            yaxis=dict(showgrid=True, gridcolor='#333', font=dict(size=10)),
        )
        return fig

    with tab1:
        st.plotly_chart(create_chart(charts['S&P500'], "S&P 500"), use_container_width=True)
    with tab2:
        st.plotly_chart(create_chart(charts['Nasdaq100'], "Nasdaq 100"), use_container_width=True)

# 5. 설정 및 예산 (2.49억)
if 'total_invested' not in st.session_state:
    st.session_state.total_invested = 0

with st.expander("⚙️ 기본 설정 및 전체 예산 관리", expanded=False):
    full_budget = st.number_input("전체 투자 예산 (만 원)", value=24900, step=100) 
    base_total = st.number_input("주당 기본 매수액 (만 원)", value=500, step=10)
    st.write("**평시 비중 (%)**")
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        u_schd = st.number_input("SCHD", 0, 100, 30); u_tdf = st.number_input("TDF 2045", 0, 100, 30)
    with col_w2:
        u_sp500 = st.number_input("S&P 500", 0, 100, 20); u_nasdaq = st.number_input("나스닥 100", 0, 100, 20)

# 6. 보정안 로직
vix, sp_drop, nd_drop = market['VIX']['current'], market['S&P500']['drop'], market['Nasdaq100']['drop']
w_schd, w_tdf, w_sp500, w_nasdaq = u_schd, u_tdf, u_sp500, u_nasdaq
multiplier, status_style, status_msg = 1.0, "success", "✅ 1.0x (평시)"

if vix >= 45 or sp_drop <= -25:
    multiplier, status_style, status_msg = 2.5, "error", "🚨 2.5x (초공포)"; w_schd, w_nasdaq = 20, 30
elif vix >= 30 or sp_drop <= -15:
    multiplier, status_style, status_msg = 2.0, "error", "🔥 2.0x (공포)"; w_schd, w_nasdaq = 25, 25
elif vix >= 25 or sp_drop <= -8:
    multiplier, status_style, status_msg = 1.2, "warning", "⚠️ 1.2x (주의)"

if nd_drop <= -30:
    w_schd, w_nasdaq = 20, 30
    status_msg += " (QQQ 특수 대응)"

getattr(st, status_style)(f"**현재 시장 단계: {status_msg}**")

# 7. 매수 테이블
names = ["SCHD", "TDF 2045", "S&P 500", "나스닥 100"]
weights = [w_schd, w_tdf, w_sp500, w_nasdaq]
buy_list = []
for name, weight in zip(names, weights):
    amt = int(base_total * (weight / 100) * multiplier)
    buy_list.append({"종목": name, "비중": f"{weight}%", "매수액": f"**{amt}만**"})
st.table(pd.DataFrame(buy_list))

# 8. 하단 자산 관리
st.markdown("---")
weekly_total = int(base_total * multiplier)
col_info, col_btn = st.columns([1.8, 1.2])
with col_info:
    st.markdown(f"#### 💰 금주 총액: **{weekly_total}만**")
    remaining = full_budget - st.session_state.total_invested
    st.write(f"📊 누적: {st.session_state.total_invested}만 / 잔액: {remaining}만")
with col_btn:
    if st.button("매수 완료 기록"):
        st.session_state.total_invested += weekly_total
        st.rerun()
st.progress(min(st.session_state.total_invested / full_budget, 1.0))
