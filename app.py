import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 앱 설정
st.set_page_config(page_title="퇴직연금 매수 가이드", layout="centered")

# CSS: 가로 한 줄 배치를 위한 스타일 조정
st.markdown("""
    <style>
    .main .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    h1 {font-size: 1.2rem !important; margin-bottom: 0.5rem;}
    /* 메트릭 간격 및 폰트 크기 최적화 */
    [data-testid="column"] {text-align: center;}
    div[data-testid="stMetricValue"] {font-size: 1.1rem !important;}
    div[data-testid="stMetricLabel"] {font-size: 0.8rem !important;}
    </style>
    """, unsafe_allow_html=True)

st.title("💰 퇴직연금 매수 가이드")

# 2. 실시간 데이터 가져오기
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

# 3. 시장 지표 (가로 한 줄 배치)
# gap="small"로 설정하여 최대한 붙여서 한 화면에 들어오게 함
c1, c2, c3 = st.columns(3, gap="small")
c1.metric("VIX", f"{market['VIX']['current']:.1f}")
c2.metric("S&P500", f"{int(market['S&P500']['current']):,}", f"{market['S&P500']['drop']:.1f}%")
c3.metric("Nasdaq100", f"{int(market['Nasdaq100']['current']):,}", f"{market['Nasdaq100']['drop']:.1f}%")

# 4. 비중 및 기본 설정
with st.expander("⚙️ 설정 (비중/기본금)", expanded=False):
    base_total = st.number_input("주당 기본 총액 (만 원)", value=500, step=10)
    col_a, col_b = st.columns(2)
    with col_a:
        w_schd = st.number_input("SCHD (%)", 0, 100, 30)
        w_tdf = st.number_input("TDF 2045 (%)", 0, 100, 30)
    with col_b:
        w_sp500 = st.number_input("S&P 500 (%)", 0, 100, 20)
        w_nasdaq = st.number_input("나스닥 100 (%)", 0, 100, 20)
    
    if (w_schd + w_tdf + w_sp500 + w_nasdaq) != 100:
        st.error("비중 합계를 100%로 맞춰주세요.")

# 5. 배율 판단
vix, sp_drop, nd_drop = market['VIX']['current'], market['S&P500']['drop'], market['Nasdaq100']['drop']
multiplier = 1.0
status_style, status_msg = "success", "✅ 1배수 (평시)"

if vix >= 35 or sp_drop <= -15 or nd_drop <= -20:
    multiplier, status_style, status_msg = 2.0, "error", "🚨 2배수 (초공포)"
elif vix >= 30 or sp_drop <= -10 or nd_drop <= -15:
    multiplier, status_style, status_msg = 1.5, "warning", "⚠️ 1.5배수 (공포)"

getattr(st, status_style)(f"**{status_msg} (배율: {multiplier}x)**")

# 6. 매수 금액 표
names = ["SCHD", "TDF 2045", "S&P 500", "나스닥 100"]
weights = [w_schd, w_tdf, w_sp500, w_nasdaq]
buy_data = []
for name, weight in zip(names, weights):
    base_amt = int(base_total * (weight / 100))
    final_amt = int(base_amt * multiplier)
    buy_data.append({"종목": name, "비율": f"{weight}%", "기본": f"{base_amt}만", "매수액": f"**{final_amt}만**"})

st.table(pd.DataFrame(buy_data))

# 7. 하단 요약
st.subheader(f"💰 총 입금액: {int(base_total * multiplier)}만 원")
