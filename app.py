import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 앱 설정
st.set_page_config(page_title="퇴직연금 가이드", layout="centered")

st.markdown("""
    <style>
    .main .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    h1 {font-size: 1.2rem !important; margin-bottom: 1rem; text-align: center;}
    div[data-testid="stMetricValue"] {font-size: 1.0rem !important;}
    div[data-testid="stMetricLabel"] {font-size: 0.75rem !important;}
    .compact-table {font-size: 0.75rem !important; line-height: 1.2;}
    </style>
    """, unsafe_allow_html=True)

st.title("💰 퇴직연금 매수 가이드")

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

# 4. 설정부 (종목별 비중 조정 기능 추가)
with st.expander("⚙️ 기본 설정 (평시 비중 직접 수정)", expanded=False):
    base_total = st.number_input("주당 기본 총액 (만 원)", value=500, step=10)
    
    st.write("**평시(1.0x) 기준 비중 설정 (%)**")
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        u_schd = st.number_input("SCHD", 0, 100, 30)
        u_tdf = st.number_input("TDF 2045", 0, 100, 30)
    with col_w2:
        u_sp500 = st.number_input("S&P 500", 0, 100, 20)
        u_nasdaq = st.number_input("나스닥 100", 0, 100, 20)
    
    total_w = u_schd + u_tdf + u_sp500 + u_nasdaq
    if total_w != 100:
        st.error(f"비중 합계가 {total_w}%입니다. 100%로 맞춰주세요!")
    st.caption("※ 하락장 진입 시 나스닥 비중이 자동으로 강화되도록 설계되어 있습니다.")

# 5. 배율 및 비중 판단 로직
vix = market['VIX']['current']
sp_drop = market['S&P500']['drop']
nd_drop = market['Nasdaq100']['drop']

# 기본 비중은 사용자가 입력한 값으로 시작
w_schd, w_tdf, w_sp500, w_nasdaq = u_schd, u_tdf, u_sp500, u_nasdaq
multiplier = 1.0
status_style, status_msg = "success", "✅ 1.0x (평시)"

# 단계별 조건 판단 및 자동 비중 조정
if vix >= 50 or sp_drop <= -35:
    multiplier, status_style, status_msg = 3.0, "error", "💀 3.0x (대공황급)"
    w_schd, w_nasdaq = 20, 30 # 초폭락 시 기술주 집중
elif vix >= 45 or sp_drop <= -25:
    multiplier, status_style, status_msg = 2.5, "error", "🚨 2.5x (초공포)"
    w_schd, w_nasdaq = 20, 30
elif vix >= 30 or sp_drop <= -15:
    multiplier, status_style, status_msg = 2.0, "error", "🔥 2.0x (공포)"
    w_schd, w_nasdaq = 25, 25
elif vix >= 25 or sp_drop <= -8:
    multiplier, status_style, status_msg = 1.2, "warning", "⚠️ 1.2x (주의)"

# 나스닥 -30% 특수 대응
if nd_drop <= -30:
    w_schd, w_nasdaq = 20, 30
    status_msg += " (QQQ 대응)"

getattr(st, status_style)(f"**현재 적용 단계: {status_msg}**")

# 6. 매수 실행 표
names = ["SCHD", "TDF 2045", "S&P 500", "나스닥 100"]
weights = [w_schd, w_tdf, w_sp500, w_nasdaq]
buy_data = []

for name, weight in zip(names, weights):
    base_amt = int(base_total * (weight / 100))
    final_amt = int(base_amt * multiplier)
    buy_data.append({
        "종목": name,
        "비중": f"{weight}%",
        "매수액": f"**{final_amt}만**"
    })

st.table(pd.DataFrame(buy_data))

# 7. 하단 총액
st.subheader(f"💰 총 입금액: {int(base_total * multiplier)}만 원")

with st.expander("ℹ️ 상세 배율 및 비중 기준", expanded=False):
    st.markdown("""
    <div class="compact-table">

    | 단계 | 배율 | S&P 500 조건 | 비중 전략 |
    | :--- | :---: | :--- | :--- |
    | **평시** | **1.0x** | 전고점 부근 | 사용자 설정 비중 |
    | **주의** | **1.2x** | -8%↓ (VIX 25↑) | 사용자 설정 비중 |
    | **공포** | **2.0x** | -15%↓ (VIX 30↑) | 나스닥 비중 강화 (25%) |
    | **초공포**| **2.5x** | -25%↓ (VIX 45↑) | 나스닥 집중 매수 (30%) |
    | **위기** | **3.0x** | -35%↓ (VIX 50↑) | 나스닥 집중 매수 (30%) |

    </div>
    """, unsafe_allow_html=True)
