import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, time

# 1. 앱 설정 및 고급 스타일링
st.set_page_config(page_title="퇴직연금 매수기", layout="centered")

st.markdown("""
    <style>
    .main .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    /* 제목 스타일 조절 (살짝 작게) */
    .main-title {
        font-size: 1.4rem !important; 
        font-weight: 800; 
        text-align: center; 
        margin-bottom: 1.5rem;
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    /* 지표 테이블 디자인 */
    .metric-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin-bottom: 25px;
        background-color: #1e1e1e;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #333;
    }
    .metric-table th {
        background-color: #262626;
        padding: 12px;
        font-size: 0.8rem;
        color: #999;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .metric-table td {
        padding: 18px;
        font-size: 1.25rem;
        font-weight: 700;
        border-top: 1px solid #333;
    }
    .drop-val { color: #ff4b4b; }
    .rsi-val { color: #4bafff; }
    /* 버튼 및 강조 텍스트 */
    .stButton>button {
        width: 100%; 
        border-radius: 10px; 
        height: 3em; 
        background: linear-gradient(45deg, #2e7d32, #43a047);
        color: white; 
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .weekly-total-text {
        font-size: 1.3rem;
        font-weight: 700;
        padding: 10px 0;
        border-bottom: 2px solid #333;
        margin-bottom: 15px;
        color: #ffffff;
    }
    /* 카드형 섹션 디자인 */
    div[data-testid="stExpander"] {
        border-radius: 10px !important;
        border: 1px solid #333 !important;
        background-color: #161616 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 메인 타이틀
st.markdown('<p class="main-title">STALWART RETIREMENT MASTER</p>', unsafe_allow_html=True)

# 3. 실시간 시장 데이터 및 RSI 계산
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
    st.error("⚠️ 데이터를 불러오는 중 오류가 발생했습니다.")
    st.stop()

# 4. 상단 지수 현황 대시보드
st.markdown(f"""
<table class="metric-table">
    <tr>
        <th>VIX (Volatility)</th>
        <th>S&P 500 Drop</th>
        <th>S&P 500 RSI</th>
        <th>Nasdaq 100 Drop</th>
    </tr>
    <tr>
        <td>{market['VIX']['current']:.2f}</td>
        <td class="drop-val">{market['S&P500']['drop']:.1f}%</td>
        <td class="rsi-val">{market['S&P500']['rsi']:.1f}</td>
        <td class="drop-val">{market['Nasdaq100']['drop']:.1f}%</td>
    </tr>
</table>
""", unsafe_allow_html=True)

# --- [세션 상태 관리] ---
for key, val in [('f_budget', 24900), ('b_total', 500), ('u_schd', 30), ('u_tdf', 30), ('u_sp500', 20), ('u_nasdaq', 20)]:
    if key not in st.session_state: st.session_state[key] = val

# 5. [실속형] 보정안 로직 엔진
vix, sp_drop, sp_rsi, nd_drop = market['VIX']['current'], market['S&P500']['drop'], market['S&P500']['rsi'], market['Nasdaq100']['drop']
multiplier = 1.0
status_style, status_msg = "success", "✅ 1.0x (안정적 흐름)"
w_schd, w_tdf, w_sp500, w_nasdaq = st.session_state.u_schd, st.session_state.u_tdf, st.session_state.u_sp500, st.session_state.u_nasdaq

if vix >= 50 or sp_drop <= -30 or sp_rsi <= 28:
    multiplier, status_style, status_msg = 3.0, "error", "💀 3.0x (위기: 적극 매수)"
    w_schd, w_nasdaq = 20, 30
elif vix >= 35 or sp_drop <= -15 or sp_rsi <= 32:
    multiplier, status_style, status_msg = 2.0, "error", "🔥 2.0x (공포: 비중 확대)"
    w_schd, w_nasdaq = 25, 25
elif vix >= 28 or sp_drop <= -10 or sp_rsi <= 40:
    multiplier, status_style, status_msg = 1.2, "warning", "⚠️ 1.2x (주의: 조정 시작)"

if nd_drop <= -25:
    w_schd, w_nasdaq = 20, 30
    if multiplier < 1.5:
        multiplier, status_msg = 1.5, status_msg + " + 나스닥 특수대응"

getattr(st, status_style)(f"**진단 결과: {status_msg}**")

# 6. 매수 실행 가이드
weekly_total = int(st.session_state.b_total * multiplier)
st.markdown(f'<p class="weekly-total-text">💰 이번 주 매수 총액: {weekly_total:,}만 원</p>', unsafe_allow_html=True)

buy_df = pd.DataFrame({
    "Asset": ["SCHD", "TDF 2045", "S&P 500", "Nasdaq 100"],
    "Ratio": [f"{w_schd}%", f"{w_tdf}%", f"{w_sp500}%", f"{w_nasdaq}%"],
    "Base Amt": [f"{int(st.session_state.b_total * (w/100))}만" for w in [w_schd, w_tdf, w_sp500, w_nasdaq]],
    "Final Buy": [f"**{int(st.session_state.b_total * (w/100) * multiplier)}만**" for w in [w_schd, w_tdf, w_sp500, w_nasdaq]]
})
st.table(buy_df)

# 7. 예산 모니터링
st.markdown("---")
def get_invested_amt(base):
    start = datetime(2026, 5, 5, 14, 0, 0)
    now = datetime.now()
    if now < start: return 0
    weeks = ((now - start).total_seconds() // (7 * 24 * 3600)) + 1
    return int(weeks * base)

invested = get_invested_amt(st.session_state.b_total)
rem = st.session_state.f_budget - invested

c1, c2 = st.columns([1, 1])
with c1: st.metric("누적 매수액", f"{invested:,}만")
with c2: st.metric("남은 예산", f"{rem:,}만")
st.progress(min(invested / st.session_state.f_budget, 1.0))

# 8. 설정 관리 (종목 비중 수정 포함)
with st.expander("⚙️ 예산 및 종목별 비중 설정", expanded=False):
    st.session_state.f_budget = st.number_input("전체 예산 (만)", value=st.session_state.f_budget, step=100)
    st.session_state.b_total = st.number_input("기본 주당 매수액 (만)", value=st.session_state.b_total, step=10)
    st.write("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.session_state.u_schd = st.number_input("SCHD 비중 (%)", 0, 100, st.session_state.u_schd)
        st.session_state.u_tdf = st.number_input("TDF 비중 (%)", 0, 100, st.session_state.u_tdf)
    with col_b:
        st.session_state.u_sp500 = st.number_input("S&P500 비중 (%)", 0, 100, st.session_state.u_sp500)
        st.session_state.u_nasdaq = st.number_input("Nasdaq100 비중 (%)", 0, 100, st.session_state.u_nasdaq)
    
    total_w = st.session_state.u_schd + st.session_state.u_tdf + st.session_state.u_sp500 + st.session_state.u_nasdaq
    if total_w != 100: st.warning(f"현재 합계: {total_w}% (100%를 맞춰주세요)")
    if st.button("설정값 저장 및 적용"): st.rerun()

# 9. 기준표
with st.expander("📋 매수 배율 판단 기준표", expanded=False):
    st.table(pd.DataFrame({
        "단계": ["평시", "주의", "공포", "위기"],
        "배율": ["1.0x", "1.2x", "2.0x", "3.0x"],
        "Condition": ["Normal", "VIX 28↑ / S&P -10% / RSI 40", "VIX 35↑ / S&P -15% / RSI 32", "VIX 50↑ / S&P -30% / RSI 28"]
    }))

# 10. 연도별 자산 성장 시나리오 (상세 버전)
with st.expander("📈 60세 은퇴까지 연도별 자산 성장 예측", expanded=False):
    years = [str(y) for y in range(2026, 2040)]
    ages = [str(47 + i) for i in range(14)]
    # 단순 가산 방식 시뮬레이션 (원금 2.6억 기준 예시 데이터)
    s8 = ["2.6억", "3.0억", "3.3억", "3.7억", "4.2억", "4.6억", "5.2억", "5.7억", "6.3억", "7.0억", "7.7억", "8.5억", "9.4억", "10.3억"]
    s10 = ["2.7억", "3.0억", "3.5억", "4.0억", "4.5억", "5.1억", "5.8억", "6.5억", "7.3억", "8.2억", "9.2억", "10.3억", "11.5억", "12.9억"]
    
    growth_df = pd.DataFrame({"연도": years, "나이": ages, "연 8%": s8, "연 10%": s10})
    st.dataframe(growth_df, use_container_width=True)
