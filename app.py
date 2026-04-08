import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 앱 설정 및 스타일 (제목 줄바꿈 방지)
st.set_page_config(page_title="퇴직연금 매수기", layout="centered")

st.markdown("""
    <style>
    .main .block-container {padding-top: 1.5rem; padding-bottom: 1rem;}
    /* 제목 크기 최적화 및 줄바꿈 방지 */
    .main-title {
        font-size: 1.3rem !important; 
        font-weight: 700; 
        text-align: center; 
        margin-bottom: 1.2rem;
        color: #ffffff;
        white-space: nowrap; 
        overflow: hidden;
        text-overflow: ellipsis;
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
        font-size: 0.8rem;
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
    .stButton>button {
        width: 100%; border-radius: 8px; height: 3.5em; 
        background-color: #2e7d32; color: white; font-weight: bold; border: none;
    }
    .weekly-total-text {
        font-size: 1.4rem; font-weight: 700; margin-top: 1rem; margin-bottom: 0.8rem; color: #f1f1f1;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 메인 타이틀
st.markdown('<p class="main-title">📉 퇴직연금 실속형 매수 가이드</p>', unsafe_allow_html=True)

# 3. 실시간 시장 데이터 로직 보강 (nan 오류 방지)
@st.cache_data(ttl=3600)
def get_market_data():
    # 지수 기호: VIX(^VIX), S&P500(^GSPC), Nasdaq100(^NDX)
    tickers = {"VIX": "^VIX", "S&P500": "^GSPC", "Nasdaq100": "^NDX"}
    data = {}
    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y")
            
            if hist.empty or len(hist) < 15:
                data[name] = {"current": 0.0, "drop": 0.0, "rsi": 50.0}
                continue
            
            current = hist['Close'].iloc[-1]
            # 최고점 계산 시 종가 기준 최대값 사용 (안정성)
            high = hist['Close'].max()
            drop = ((current - high) / high) * 100 if high > 0 else 0.0
            
            # RSI 계산
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss.replace(0, 1e-9)
            rsi = 100 - (100 / (1 + rs))
            
            data[name] = {
                "current": current,
                "drop": drop if not pd.isna(drop) else 0.0,
                "rsi": rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0
            }
        except:
            data[name] = {"current": 0.0, "drop": 0.0, "rsi": 50.0}
            
    return data

try:
    market = get_market_data()
except:
    st.error("데이터 로드 중 치명적 오류가 발생했습니다.")
    st.stop()

# 4. 상단 지수 현황
st.markdown(f"""
<table class="metric-table">
    <tr>
        <th>VIX 지수</th>
        <th>S&P 500 하락률</th>
        <th>S&P 500 RSI</th>
        <th>Nasdaq 100 하락률</th>
    </tr>
    <tr>
        <td>{market['VIX']['current']:.2f}</td>
        <td class="drop-val">{market['S&P500']['drop']:.1f}%</td>
        <td class="rsi-val">{market['S&P500']['rsi']:.1f}</td>
        <td class="drop-val">{market['Nasdaq100']['drop']:.1f}%</td>
    </tr>
</table>
""", unsafe_allow_html=True)

# 5. 세션 상태 초기화 및 보정 로직 (기존 동일)
for key, val in [('f_budget', 24900), ('b_total', 500), ('u_schd', 30), ('u_tdf', 30), ('u_sp500', 20), ('u_nasdaq', 20)]:
    if key not in st.session_state: st.session_state[key] = val

vix, sp_drop, sp_rsi, nd_drop = market['VIX']['current'], market['S&P500']['drop'], market['S&P500']['rsi'], market['Nasdaq100']['drop']
multiplier = 1.0
status_style, status_msg = "success", "✅ 1.0x (평시)"
w_schd, w_tdf, w_sp500, w_nasdaq = st.session_state.u_schd, st.session_state.u_tdf, st.session_state.u_sp500, st.session_state.u_nasdaq

if vix >= 50 or sp_drop <= -30 or sp_rsi <= 28:
    multiplier, status_style, status_msg = 3.0, "error", "💀 3.0x (위기)"
    w_schd, w_nasdaq = 20, 30
elif vix >= 35 or sp_drop <= -15 or sp_rsi <= 32:
    multiplier, status_style, status_msg = 2.0, "error", "🔥 2.0x (공포)"
    w_schd, w_nasdaq = 25, 25
elif vix >= 28 or sp_drop <= -10 or sp_rsi <= 40:
    multiplier, status_style, status_msg = 1.2, "warning", "⚠️ 1.2x (주의)"

if nd_drop <= -25:
    w_schd, w_nasdaq = 20, 30
    if multiplier < 1.5: multiplier = 1.5; status_msg += " (나스닥 대응)"

getattr(st, status_style)(f"**현재 시장 진단: {status_msg}**")

# 6. 매수 실행 테이블
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

# 7~8. 자산 관리 및 설정
st.markdown("---")
def get_invested(base):
    start = datetime(2026, 5, 5, 14, 0, 0)
    now = datetime.now()
    if now < start: return 0
    weeks = ((now - start).total_seconds() // (7 * 24 * 3600)) + 1
    return int(weeks * base)

invested = get_invested(st.session_state.b_total)
rem = st.session_state.f_budget - invested
col1, col2 = st.columns([1.8, 1.2])
with col1:
    st.markdown(f"#### 📊 누적 매수: **{invested}만**")
    st.write(f"📉 잔액: {rem}만 / 전체: {st.session_state.f_budget}만")
with col2:
    st.progress(min(invested / st.session_state.f_budget, 1.0))

with st.expander("⚙️ 기본 설정 및 비중 관리", expanded=False):
    st.session_state.f_budget = st.number_input("전체 예산 (만)", value=st.session_state.f_budget, step=100)
    st.session_state.b_total = st.number_input("주당 기본 매수액 (만)", value=st.session_state.b_total, step=10)
    st.write("---")
    st.write("**평시(1.0x) 기준 비중 설정 (%)**")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.u_schd = st.number_input("SCHD", 0, 100, st.session_state.u_schd)
        st.session_state.u_tdf = st.number_input("TDF 2045", 0, 100, st.session_state.u_tdf)
    with c2:
        st.session_state.u_sp500 = st.number_input("S&P 500", 0, 100, st.session_state.u_sp500)
        st.session_state.u_nasdaq = st.number_input("나스닥 100", 0, 100, st.session_state.u_nasdaq)
    if st.button("설정 저장"): st.rerun()

# 9~10. 기준표 및 시나리오 (4% 추가됨)
with st.expander("📋 매수 기준표", expanded=False):
    st.table(pd.DataFrame({
        "단계": ["평시", "주의", "공포", "위기"],
        "배율": ["1.0x", "1.2x", "2.0x", "3.0x"],
        "조건": ["정상", "VIX 28↑/S&P -10%↓/RSI 40↓", "VIX 35↑/S&P -15%↓/RSI 32↓", "VIX 50↑/S&P -30%↓/RSI 28↓"]
    }))

with st.expander("📈 [성장 시나리오] 은퇴까지 연도별 시뮬레이션", expanded=False):
    growth_data = {
        "경과 연도": [str(y) for y in range(2026, 2040)],
        "예상 연령": [str(47 + i) for i in range(14)],
        "연 4%": ["2.6억", "2.8억", "3.0억", "3.1억", "3.3억", "3.5억", "3.7억", "4.0억", "4.2억", "4.5억", "4.7억", "5.0억", "5.3억", "5.6억"],
        "연 8%": ["2.6억", "3.0억", "3.3억", "3.7억", "4.2억", "4.6억", "5.2억", "5.7억", "6.3억", "7.0억", "7.7억", "8.5억", "9.4억", "10.3억"],
        "연 10%": ["2.7억", "3.0억", "3.5억", "4.0억", "4.5억", "5.1억", "5.8억", "6.5억", "7.3억", "8.2억", "9.2억", "10.3억", "11.5억", "12.9억"]
    }
    st.table(pd.DataFrame(growth_data))
