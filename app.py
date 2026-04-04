import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 앱 설정 (모바일 최적화)
st.set_page_config(page_title="퇴직연금 가이드", layout="centered")

# CSS: 표 디자인 및 여백 최적화
st.markdown("""
    <style>
    .main .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    h1 {font-size: 1.2rem !important; margin-bottom: 0.8rem;}
    .stTable {font-size: 0.85rem !important;}
    /* 다크모드에서도 표 테두리가 잘 보이도록 설정 */
    table {border: 1px solid rgba(150, 150, 150, 0.3) !important;}
    </style>
    """, unsafe_allow_html=True)

st.title("💰 퇴직연금 매수 가이드")

# 2. 실시간 데이터 가져오기
@st.cache_data(ttl=3600)
def get_market_data():
    tickers = {"VIX": "^VIX", "S&P500": "^GSPC", "Nasdaq100": "^NDX"}
    data = []
    market_raw = {}
    for name, symbol in tickers.items():
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1y")
        current = hist['Close'].iloc[-1]
        high = hist['High'].max()
        drop = ((current - high) / high) * 100
        
        # 표 구성을 위한 데이터 정리
        val_display = f"{current:.1f}" if name == "VIX" else f"{int(current):,}"
        data.append({
            "지수명": name,
            "현재가": val_display,
            "하락률": f"{drop:.1f}%"
        })
        market_raw[name] = {"current": current, "drop": drop}
    return pd.DataFrame(data), market_raw

df_indices, market_raw = get_market_data()

# 3. 시장 지표 통합 표 (VIX, S&P500, 나스닥 한눈에)
st.caption("🌐 실시간 시장 현황")
st.table(df_indices)

# 4. 배율 판단 및 표시
vix = market_raw['VIX']['current']
sp_drop = market_raw['S&P500']['drop']
nd_drop = market_raw['Nasdaq100']['drop']

multiplier = 1.0
status_style, status_msg = "success", "✅ 1.0x (평시)"

if vix >= 35 or sp_drop <= -15 or nd_drop <= -20:
    multiplier, status_style, status_msg = 2.0, "error", "🚨 2.0x (초공포)"
elif vix >= 30 or sp_drop <= -10 or nd_drop <= -15:
    multiplier, status_style, status_msg = 1.5, "warning", "⚠️ 1.5x (공포)"

getattr(st, status_style)(f"**적용 배율: {status_msg}**")

# 5. 설정부 (비중 및 기본금)
with st.expander("⚙️ 설정 (비중/기본금)", expanded=False):
    base_total = st.number_input("주당 기본 총액 (만 원)", value=500, step=10)
    col_a, col_b = st.columns(2)
    with col_a:
        w_schd = st.number_input("SCHD (%)", 0, 100, 30)
        w_tdf = st.number_input("TDF 2045 (%)", 0, 100, 30)
    with col_b:
        w_sp500 = st.number_input("S&P 500 (%)", 0, 100, 20)
        w_nasdaq = st.number_input("나스닥 100 (%)", 0, 100, 20)

# 6. 이번 주 매수 실행 표
names = ["SCHD", "TDF 2045", "S&P 500", "나스닥 100"]
weights = [w_schd, w_tdf, w_sp500, w_nasdaq]
buy_data = []
for name, weight in zip(names, weights):
    base_amt = int(base_total * (weight / 100))
    final_amt = int(base_amt * multiplier)
    buy_data.append({
        "종목": name,
        "비율": f"{weight}%",
        "기본금": f"{base_amt}만",
        "매수액": f"**{final_amt}만**"
    })

st.table(pd.DataFrame(buy_data))

# 7. 최종 요약
st.subheader(f"💰 총 입금액: {int(base_total * multiplier)}만 원")
