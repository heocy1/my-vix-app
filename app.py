import streamlit as st
import yfinance as yf
import pandas as pd

# 앱 설정 (여백 최소화)
st.set_page_config(page_title="투자 비서", layout="centered")

# CSS를 이용해 화면 여백 더 줄이기
st.markdown("""
    <style>
    .main .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    div[data-testid="stExpander"] {border: none;}
    </style>
    """, unsafe_allow_html=True)

# 1. 실시간 데이터 가져오기 (캐시 처리)
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

# 2. 시장 지표 (3열 배치)
st.caption("🌐 시장 지표 (고점 대비 하락률)")
c1, c2, c3 = st.columns(3)
c1.metric("VIX", f"{market['VIX']['current']:.1f}")
c2.metric("S&P500", f"{market['S&P500']['drop']:.1f}%")
c3.metric("나스닥100", f"{market['Nasdaq100']['drop']:.1f}%")

# 3. 매수 배율 판단 로직
vix = market['VIX']['current']
sp_drop = market['S&P500']['drop']
nd_drop = market['Nasdaq100']['drop']

multiplier = 1.0
status_info = ("success", "✅ 1배수 적립")

if vix >= 35 or sp_drop <= -15 or nd_drop <= -20:
    multiplier = 2.0
    status_info = ("error", "🚨 2배수 공격 매수")
elif vix >= 30 or sp_drop <= -10 or nd_drop <= -15:
    multiplier = 1.5
    status_info = ("warning", "⚠️ 1.5배수 확대 매수")

# 상태 메시지 출력
getattr(st, status_info[0])(f"**현재 단계: {status_info[1]} (배율: {multiplier}x)**")

# 4. 매수 금액 표 (주 500만 기준)
base_data = {
    "종목명": ["SCHD", "TDF2045", "S&P500", "Nasdaq100"],
    "기본(만)": [150, 150, 100, 100]
}
df = pd.DataFrame(base_data)
df['이번주 매수액'] = (df['기본(만)'] * multiplier).astype(int)
df['이번주 매수액'] = df['이번주 매수액'].apply(lambda x: f"{x}만 원")

st.table(df)

# 5. 하단 요약 및 설정 기준 (접어두기)
total = int(500 * multiplier)
st.subheader(f"💰 총 입금액: {total}만 원")

with st.expander("📝 배율 기준 확인"):
    st.write("- **1.5배**: VIX 30↑ / S&P -10%↓ / 나스닥 -15%↓")
    st.write("- **2.0배**: VIX 35↑ / S&P -15%↓ / 나스닥 -20%↓")
