import streamlit as st
import yfinance as yf
import pandas as pd

# 앱 설정 및 제목
st.set_page_config(page_title="퇴직연금 무한매수 비서", layout="wide")
st.title("📈 VIX & 하락률 연동 투자 시스템 (주 500만 플랜)")

# 1. 실시간 데이터 가져오기 (VIX, S&P500, 나스닥100)
@st.cache_data(ttl=3600)
def get_market_data():
    tickers = {"VIX": "^VIX", "S&P500": "^GSPC", "Nasdaq100": "^NDX"}
    data = {}
    for name, symbol in tickers.items():
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1y") # 최근 1년 고점 대비 계산
        current = hist['Close'].iloc[-1]
        high = hist['High'].max()
        drop = ((current - high) / high) * 100
        data[name] = {"current": current, "high": high, "drop": drop}
    return data

market = get_market_data()

# 2. 시장 현황 대시보드
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("VIX 지수", f"{market['VIX']['current']:.2f}")
with col2:
    st.metric("S&P 500 하락률", f"{market['S&P500']['drop']:.2f}%")
with col3:
    st.metric("나스닥 100 하락률", f"{market['Nasdaq100']['drop']:.2f}%")

# 3. 매수 배율 결정 로직 (사용자 지정 조건)
vix = market['VIX']['current']
sp500_drop = market['S&P500']['drop']
nasdaq_drop = market['Nasdaq100']['drop']

multiplier = 1.0
status_text = "✅ 평시: 정기 적립 (1배수)"

# 2배수 조건
if vix >= 35 or sp500_drop <= -15 or nasdaq_drop <= -20:
    multiplier = 2.0
    status_text = "🚨 초공포 단계: 공격적 매수 (2배수)!"
# 1.5배수 조건
elif vix >= 30 or sp500_drop <= -10 or nasdaq_drop <= -15:
    multiplier = 1.5
    status_text = "⚠️ 공포 단계: 비중 확대 매수 (1.5배수)"

st.divider()
st.subheader(status_text)

# 4. 매수 금액 계산 (기본 주 500만 원 기준)
# 비중: SCHD 30%, TDF 30%, S&P500 20%, 나스닥 20%
base_data = {
    "종목": ["SCHD (30%)", "TDF 2045 (30%)", "S&P 500 (20%)", "나스닥 100 (20%)"],
    "기본 금액(만)": [150, 150, 100, 100]  # 합계 500만 원
}

df = pd.DataFrame(base_data)
df['이번 주 매수액(만)'] = (df['기본 금액(만)'] * multiplier).astype(int)

# 5. 결과 출력
st.table(df)

total_buy = df['이번 주 매수액(만)'].sum()
st.metric("💰 이번 주 총 매수 합계", f"{total_buy}만 원")

st.info(f"💡 설정 기준: 주간 기본 500만 원 | 현재 배율: {multiplier}배")
