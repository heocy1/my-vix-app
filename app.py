import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 앱 설정
st.set_page_config(page_title="퇴직연금 인내심 매수기", layout="centered")

st.markdown("""
    <style>
    .main .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    h1 {font-size: 1.2rem !important; margin-bottom: 1rem; text-align: center;}
    div[data-testid="stMetricValue"] {font-size: 1.0rem !important;}
    div[data-testid="stMetricLabel"] {font-size: 0.75rem !important;}
    .compact-table {font-size: 0.75rem !important; line-height: 1.2;}
    /* 버튼 스타일 커스텀 */
    .stButton>button {width: 100%; border-radius: 5px; height: 3em; background-color: #2e7d32; color: white;}
    </style>
    """, unsafe_allow_html=True)

st.title("📉 퇴직연금 인내심 매수 가이드")

# 2. 데이터 가져오기
@st.cache_data(ttl=3600)
def get_market_data():
    tickers = {"VIX": "^VIX", "S&P500": "^GSPC", "Nasdaq100": "^NDX"}
    data = {}
    for name, symbol in tickers.items():
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1y")
        current = hist['Close'].iloc[-1]
        high = hist['High'].max()
        drop = ((current - high) / high) * 100
        data[name] = {"current": current, "drop": drop}
    return data

market = get_market_data()

# 3. 시장 지표 (가로 3열)
c1, c2, c3 = st.columns(3, gap="small")
c1.metric("VIX", f"{market['VIX']['current']:.1f}")
c2.metric("S&P 500", f"{int(market['S&P500']['current']):,}", f"{market['S&P500']['drop']:.1f}%")
c3.metric("Nasdaq 100", f"{int(market['Nasdaq100']['current']):,}", f"{market['Nasdaq100']['drop']:.1f}%")

# 4. 설정부 (비중 커스텀)
with st.expander("⚙️ 기본 설정 및 전체 예산", expanded=False):
    # 전체 예산 설정 (기본값 2.6억 등 사용자 상황에 맞게 수정 가능)
    full_budget = st.number_input("전체 투자 예산 (만 원)", value=26000, step=1000)
    base_total = st.number_input("주당 기본 총액 (만 원)", value=500, step=10)
    
    st.write("**평시(1.0x) 기준 비중 설정 (%)**")
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        u_schd = st.number_input("SCHD", 0, 100, 30)
        u_tdf = st.number_input("TDF 2045", 0, 100, 30)
    with col_w2:
        u_sp500 = st.number_input("S&P 500", 0, 100, 20)
        u_nasdaq = st.number_input("나스닥 100", 0, 100, 20)

# 5. 배율 및 비중 판단 로직
vix = market['VIX']['current']
sp_drop = market['S&P500']['drop']
nd_drop = market['Nasdaq100']['drop']

w_schd, w_tdf, w_sp500, w_nasdaq = u_schd, u_tdf, u_sp500, u_nasdaq
multiplier = 1.0
status_style, status_msg = "success", "✅ 1.0x (평시)"

if vix >= 50 or sp_drop <= -35:
    multiplier, status_style, status_msg = 3.0, "error", "💀 3.0x (위기)"
    w_schd, w_nasdaq = 20, 30
elif vix >= 45 or sp_drop <= -25:
    multiplier, status_style, status_msg = 2.5, "error", "🚨 2.5x (초공포)"
    w_schd, w_nasdaq = 20, 30
elif vix >= 30 or sp_drop <= -15:
    multiplier, status_style, status_msg = 2.0, "error", "🔥 2.0x (공포)"
    w_schd, w_nasdaq = 25, 25
elif vix >= 25 or sp_drop <= -8:
    multiplier, status_style, status_msg = 1.2, "warning", "⚠️ 1.2x (주의)"

if nd_drop <= -30:
    w_schd, w_nasdaq = 20, 30
    status_msg += " (QQQ 대응 ON)"

getattr(st, status_style)(f"**현재 적용 단계: {status_msg}**")

# 6. 매수 실행 표
names = ["SCHD", "TDF 2045", "S&P 500", "나스닥 100"]
weights = [w_schd, w_tdf, w_sp500, w_nasdaq]
buy_data = []

for name, weight in zip(names, weights):
    base_amt = int(base_total * (weight / 100))
    final_amt = int(base_amt * multiplier)
    buy_data.append({"종목": name, "비중": f"{weight}%", "매수액": f"**{final_amt}만**"})

st.table(pd.DataFrame(buy_data))

# 7. [신규] 누적 금액 및 잔액 확인 섹션
st.markdown("---")
if 'total_invested' not in st.session_state:
    st.session_state.total_invested = 0

weekly_total = int(base_total * multiplier)

col_summary, col_action = st.columns([2, 1])

with col_summary:
    st.write(f"💰 **이번 주 총 매수액: {weekly_total}만 원**")
    remaining = full_budget - st.session_state.total_invested
    st.write(f"📊 **누적 매수액:** {st.session_state.total_invested}만 / **잔액:** {remaining}만")

with col_action:
    if st.button("매수 완료 기록"):
        st.session_state.total_invested += weekly_total
        st.rerun()

# 진행률 바 표시
progress = min(st.session_state.total_invested / full_budget, 1.0)
st.progress(progress)
