import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, time

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
        margin-bottom: 20px;
        text-align: center;
        background-color: #1e1e1e;
        border-radius: 10px;
    }
    .metric-table th {
        background-color: #333;
        padding: 10px;
        font-size: 0.85rem;
        color: #bbb;
    }
    .metric-table td {
        padding: 15px;
        font-size: 1.3rem;
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
        border: none;
    }
    /* 금주 매수 총액 글씨 크기 조절 */
    .weekly-total-text {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 메인 타이틀
st.markdown('<p class="main-title">📉 퇴직연금 매수 가이드</p>', unsafe_allow_html=True)

# 3. 실시간 시장 데이터 호출
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

try:
    market = get_market_data()
except:
    st.error("데이터를 불러오지 못했습니다.")
    st.stop()

# 4. 상단 지수 현황
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

# --- [로직용 기본값 설정 (UI 표시 전 계산)] ---
# 세션 상태 등을 사용하지 않고 input 값을 받기 위해 초기 변수 설정
if 'f_budget' not in st.session_state: st.session_state.f_budget = 24900
if 'b_total' not in st.session_state: st.session_state.b_total = 500
if 'u_schd' not in st.session_state: st.session_state.u_schd = 30
if 'u_tdf' not in st.session_state: st.session_state.u_tdf = 30
if 'u_sp500' not in st.session_state: st.session_state.u_sp500 = 20
if 'u_nasdaq' not in st.session_state: st.session_state.u_nasdaq = 20

# 5. 보정안 로직 엔진
vix, sp_drop, nd_drop = market['VIX']['current'], market['S&P500']['drop'], market['Nasdaq100']['drop']
multiplier = 1.0
status_style, status_msg = "success", "✅ 1.0x (평시)"
w_schd, w_tdf, w_sp500, w_nasdaq = st.session_state.u_schd, st.session_state.u_tdf, st.session_state.u_sp500, st.session_state.u_nasdaq

if vix >= 50 or sp_drop <= -35:
    multiplier, status_style, status_msg = 3.0, "error", "💀 3.0x (위기)"; w_schd, w_nasdaq = 20, 30
elif vix >= 45 or sp_drop <= -25:
    multiplier, status_style, status_msg = 2.5, "error", "🚨 2.5x (초공포)"; w_schd, w_nasdaq = 20, 30
elif vix >= 30 or sp_drop <= -15:
    multiplier, status_style, status_msg = 2.0, "error", "🔥 2.0x (공포)"; w_schd, w_nasdaq = 25, 25
elif vix >= 25 or sp_drop <= -8:
    multiplier, status_style, status_msg = 1.2, "warning", "⚠️ 1.2x (주의)"

if nd_drop <= -30:
    w_schd, w_nasdaq = 20, 30
    status_msg += " (QQQ 특수 대응)"

getattr(st, status_style)(f"**현재 시장 단계: {status_msg}**")

# 6. 이번 주 매수 실행 테이블
weekly_total = int(st.session_state.b_total * multiplier)
st.markdown(f'<p class="weekly-total-text">💰 금주 매수 총액: {weekly_total}만 원</p>', unsafe_allow_html=True)

names = ["SCHD", "TDF 2045", "S&P 500", "나스닥 100"]
weights = [w_schd, w_tdf, w_sp500, w_nasdaq]
buy_list = []

for name, weight in zip(names, weights):
    base_amt = int(st.session_state.b_total * (weight / 100))
    final_amt = int(base_amt * multiplier)
    buy_list.append({"종목": name, "비중": f"{weight}%", "기본매수액": f"{base_amt}만", "최종매수액": f"**{final_amt}만**"})

st.table(pd.DataFrame(buy_list))

# 7. 자산 관리 대시보드
st.markdown("---")
def calculate_auto_invested(base_total):
    start_date = datetime(2026, 5, 5, 14, 0, 0)
    now = datetime.now()
    if now < start_date: return 0
    weeks_passed = ((now - start_date).total_seconds() // (7 * 24 * 3600)) + 1
    return int(weeks_passed * base_total)

auto_total_invested = calculate_auto_invested(st.session_state.b_total)
remaining = st.session_state.f_budget - auto_total_invested

col_info, col_btn = st.columns([1.8, 1.2])
with col_info:
    st.markdown(f"#### 📊 누적 매수: **{auto_total_invested}만**")
    st.write(f"📉 잔액: {remaining}만 / 전체 예산: {st.session_state.f_budget}만")

with col_btn:
    st.caption("※ 매주 화요일 14시 자동 갱신")
    st.progress(min(auto_total_invested / st.session_state.f_budget, 1.0))

# 8. 설정 및 예산 관리 (맨 밑으로 이동)
with st.expander("⚙️ 기본 설정 및 예산 관리 (비중/금액 수정 가능)", expanded=False):
    st.session_state.f_budget = st.number_input("전체 투자 예산 (만 원)", value=st.session_state.f_budget, step=100) 
    st.session_state.b_total = st.number_input("주당 기본 매수액 (만 원)", value=st.session_state.b_total, step=10)
    
    st.write("---")
    st.write("**평시(1.0x) 기준 기본 비중 (%)**")
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        st.session_state.u_schd = st.number_input("SCHD 비중", 0, 100, st.session_state.u_schd)
        st.session_state.u_tdf = st.number_input("TDF 2045 비중", 0, 100, st.session_state.u_tdf)
    with col_w2:
        st.session_state.u_sp500 = st.number_input("S&P 500 비중", 0, 100, st.session_state.u_sp500)
        st.session_state.u_nasdaq = st.number_input("나스닥 100 비중", 0, 100, st.session_state.u_nasdaq)
    if st.button("설정값 적용"): st.rerun()

# 9. 전체 비중 및 배율 설정 기준표 (가장 하단)
with st.expander("📋 전체 비중 및 배율 설정 기준표 확인 (클릭)", expanded=False):
    rules_data = {
        "단계": ["평시", "주의", "공포", "초공포", "위기"],
        "배율": ["1.0x", "1.2x", "2.0x", "2.5x", "3.0x"],
        "조건 (VIX/하락률)": ["-8% 미만", "VIX 25↑ / S&P -8%↓", "VIX 30↑ / S&P -15%↓", "VIX 45↑ / S&P -25%↓", "VIX 50↑ / S&P -35%↓"],
        "비중 (SCHD/NDX)": ["30% / 20%", "30% / 20%", "25% / 25%", "20% / 30%", "20% / 30%"]
    }
    st.table(pd.DataFrame(rules_data))
    st.info("💡 나스닥 100 하락률이 -30%를 넘을 경우, 단계와 상관없이 나스닥 비중은 30%로 강제 고정됩니다.")
