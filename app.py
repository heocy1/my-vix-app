import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 앱 설정 및 커스텀 스타일
st.set_page_config(page_title="퇴직연금 마스터 매수기", layout="centered")

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
        font-size: 1.2rem;
        font-weight: 700;
        border-bottom: 1px solid #444;
    }
    .drop-val { color: #ff4b4b; }
    .rsi-val { color: #4bafff; }
    .weekly-total-text {
        font-size: 1.4rem;
        font-weight: 700;
        margin-top: 1rem;
        margin-bottom: 0.8rem;
        color: #f1f1f1;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 메인 타이틀
st.markdown('<p class="main-title">🚀 퇴직연금 마스터 매수 가이드</p>', unsafe_allow_html=True)

# 3. 4대 지표 실시간 데이터 호출 (RSI 포함)
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
        
        # RSI 14 계산
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        data[name] = {"current": current, "drop": drop, "rsi": rsi.iloc[-1]}
    return data

try:
    market = get_market_data()
except:
    st.error("데이터 로딩 실패")
    st.stop()

# 4. 상단 4대 지표 현황판
st.markdown(f"""
<table class="metric-table">
    <tr>
        <th>VIX 지수</th>
        <th>S&P500 낙폭</th>
        <th>S&P500 RSI</th>
        <th>Nasdaq 낙폭</th>
    </tr>
    <tr>
        <td>{market['VIX']['current']:.2f}</td>
        <td class="drop-val">{market['S&P500']['drop']:.1f}%</td>
        <td class="rsi-val">{market['S&P500']['rsi']:.1f}</td>
        <td class="drop-val">{market['Nasdaq100']['drop']:.1f}%</td>
    </tr>
</table>
""", unsafe_allow_html=True)

# --- [로직용 기본값 설정] ---
if 'f_budget' not in st.session_state: st.session_state.f_budget = 24900
if 'b_total' not in st.session_state: st.session_state.b_total = 500
if 'u_schd' not in st.session_state: st.session_state.u_schd = 30
if 'u_tdf' not in st.session_state: st.session_state.u_tdf = 30
if 'u_sp500' not in st.session_state: st.session_state.u_sp500 = 20
if 'u_nasdaq' not in st.session_state: st.session_state.u_nasdaq = 20

# 5. 4대 지표 통합 마스터 엔진 (핵심 로직)
vix = market['VIX']['current']
sp_drop = market['S&P500']['drop']
nd_drop = market['Nasdaq100']['drop']
sp_rsi = market['S&P500']['rsi']

# 기본 비중 복사
w_schd, w_tdf, w_sp500, w_nasdaq = st.session_state.u_schd, st.session_state.u_tdf, st.session_state.u_sp500, st.session_state.u_nasdaq
multiplier = 1.0
status_style, status_msg = "success", "✅ 1.0x (평시)"

# [배율 및 비중 조정 조건문 - OR 연산 활용]
# 단계 4: 위기 (3.0x)
if vix >= 45 or sp_drop <= -25 or nd_drop <= -30 or sp_rsi <= 25:
    multiplier, status_style, status_msg = 3.0, "error", "💀 3.0x (역사적 기회)"
    w_schd, w_nasdaq = 20, 30
# 단계 3: 공포 (2.0x)
elif vix >= 30 or sp_drop <= -15 or nd_drop <= -20 or sp_rsi <= 35:
    multiplier, status_style, status_msg = 2.0, "error", "🔥 2.0x (공포 구간)"
    w_schd, w_nasdaq = 25, 25
# 단계 2: 주의 (1.2x)
elif vix >= 25 or sp_drop <= -8 or nd_drop <= -10 or sp_rsi <= 45:
    multiplier, status_style, status_msg = 1.2, "warning", "⚠️ 1.2x (조정 주의)"

getattr(st, status_style)(f"**현재 시장 진단: {status_msg}**")

# 6. 이번 주 매수 실행 테이블
weekly_total = int(st.session_state.b_total * multiplier)
st.markdown(f'<p class="weekly-total-text">💰 금주 매수 총액: {weekly_total}만 원</p>', unsafe_allow_html=True)

buy_list = []
for name, weight in zip(["SCHD", "TDF 2045", "S&P 500", "나스닥 100"], [w_schd, w_tdf, w_sp500, w_nasdaq]):
    base_amt = int(st.session_state.b_total * (weight / 100))
    final_amt = int(base_amt * multiplier)
    buy_list.append({"종목": name, "비중": f"{weight}%", "기본(만)": base_amt, "최종매수(만)": f"**{final_amt}만**"})

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

# 8. 하단 설정 및 기준표
with st.expander("⚙️ 기본 설정 및 예산 관리", expanded=False):
    st.session_state.f_budget = st.number_input("전체 예산(만)", value=st.session_state.f_budget)
    st.session_state.b_total = st.number_input("주당 기본액(만)", value=st.session_state.b_total)
    # 비중 설정 생략 가능 (로직이 자동 계산하므로 기본 비중만 유지)
    if st.button("설정 저장"): st.rerun()

with st.expander("📈 [자산 성장 시나리오] 보기", expanded=False):
    growth_data = {
        "예상 연령": ["47세", "50세", "55세", "60세(은퇴)"],
        "연 8% 수익": ["2.6억", "3.7억", "7.0억", "10.3억"],
        "연 10% 수익": ["2.6억", "3.9억", "8.2억", "12.8억"]
    }
    st.table(pd.DataFrame(growth_data))
