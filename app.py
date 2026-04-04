 import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 앱 설정 및 스타일 (컴팩트 레이아웃)
st.set_page_config(page_title="퇴직연금 분할매수 비서", layout="centered")
st.markdown("""
    <style>
    .main .block-container {padding-top: 1.5rem; padding-bottom: 1rem;}
    stMetric {background-color: #f0f2f6; padding: 10px; border-radius: 10px;}
    </style>
    """, unsafe_allow_html=True)

st.title("💰 DC 퇴직연금 매수 가이드")

# 2. 실시간 데이터 가져오기 (캐시 처리)
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

# 3. 시장 지표 표시
c1, c2, c3 = st.columns(3)
c1.metric("VIX 지수", f"{market['VIX']['current']:.1f}")
c2.metric("S&P500 하락률", f"{market['S&P500']['drop']:.1f}%")
c3.metric("나스닥100 하락률", f"{market['Nasdaq100']['drop']:.1f}%")

# 4. 비중 및 배율 설정 (사이드바 또는 상단 에디터)
st.divider()
with st.expander("⚙️ 종목별 매수 비중 설정 (합계 100%)", expanded=False):
    col_a, col_b = st.columns(2)
    with col_a:
        w_schd = st.slider("SCHD 비중 (%)", 0, 100, 30)
        w_tdf = st.slider("TDF 2045 비중 (%)", 0, 100, 30)
    with col_b:
        w_sp500 = st.slider("S&P 500 비중 (%)", 0, 100, 20)
        w_nasdaq = st.slider("나스닥 100 비중 (%)", 0, 100, 20)
    
    total_w = w_schd + w_tdf + w_sp500 + w_nasdaq
    if total_w != 100:
        st.error(f"⚠️ 현재 비중 합계가 {total_w}%입니다. 100%가 되도록 조정해주세요.")

# 5. 매수 배율 판단
vix = market['VIX']['current']
sp_drop = market['S&P500']['drop']
nd_drop = market['Nasdaq100']['drop']

multiplier = 1.0
status_style = "success"
status_msg = "✅ 1배수 (평시 적립)"

if vix >= 35 or sp_drop <= -15 or nd_drop <= -20:
    multiplier = 2.0
    status_style = "error"
    status_msg = "🚨 2배수 (초공포 매수)"
elif vix >= 30 or sp_drop <= -10 or nd_drop <= -15:
    multiplier = 1.5
    status_style = "warning"
    status_msg = "⚠️ 1.5배수 (비중 확대)"

# 상태 알림창
if status_style == "success": st.success(f"**{status_msg}**")
elif status_style == "warning": st.warning(f"**{status_msg}**")
else: st.error(f"**{status_msg}**")

# 6. 매수 금액 계산 및 표 출력
base_total = 500 # 기본 주당 500만원
weights = [w_schd, w_tdf, w_sp500, w_nasdaq]
names = ["SCHD", "TDF 2045", "S&P 500", "나스닥 100"]

buy_data = []
for name, weight in zip(names, weights):
    base_amt = base_total * (weight / 100)
    final_amt = int(base_amt * multiplier)
    buy_data.append({"종목명": name, "설정비중": f"{weight}%", "매수금액": f"{final_amt}만 원"})

df = pd.DataFrame(buy_data)
st.table(df)

# 7. 하단 요약
final_total = int(base_total * multiplier)
st.subheader(f"💰 이번 주 총 입금액: {final_total}만 원")
st.caption(f"기준: 주간 {base_total}만원 × {multiplier}배수 적용")
