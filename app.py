import streamlit as st
import yfinance as yf
import pandas as pd

# 앱 설정
st.set_page_config(page_title="퇴직연금 52주 전략 비서", layout="wide")
st.title("📈 VIX & MDD 연동 투자 시스템 (주 500만)")

# 1. 데이터 가져오기 함수 (VIX, S&P 500, 나스닥 100)
@st.cache_data(ttl=3600)
def get_market_data():
    tickers = {"VIX": "^VIX", "S&P 500": "^GSPC", "Nasdaq 100": "^NDX"}
    data = {}
    charts = {}
    for name, symbol in tickers.items():
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1y") # 1년치 데이터
        current = hist['Close'].iloc[-1]
        high = hist['High'].max()
        drop = ((current - high) / high) * 100
        data[name] = {"current": current, "high": high, "drop": drop}
        charts[name] = hist['Close']
    return data, charts

market, charts = get_market_data()

# 2. 시장 현황 대시보드 및 실시간 차트
st.subheader("🌐 실시간 시장 지표 및 1년 흐름")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("VIX 지수 (공포지수)", f"{market['VIX']['current']:.2f}")
    st.line_chart(charts['VIX'], height=250, use_container_width=True)
    st.caption("VIX가 높을수록 시장이 불안하며, 매수 기회일 확률이 높습니다.")

with col2:
    st.metric("S&P 500 하락률", f"{market['S&P 500']['drop']:.2f}%")
    st.line_chart(charts['S&P 500'], height=250, use_container_width=True)

with col3:
    st.metric("나스닥 100 하락률", f"{market['Nasdaq 100']['drop']:.2f}%")
    st.line_chart(charts['Nasdaq 100'], height=250, use_container_width=True)

# 3. 매매 배수 설정 기준 (시각적 표시)
st.divider()
st.subheader("🛠 매매 배수 결정 기준")
c1, c2, c3 = st.columns(3)

# 기준값 안내 카드
with c1:
    st.info("### **1배수 (평시)**\n- 기본 적립 상황")
with c2:
    st.warning("### **1.5배수 (공포)**\n- VIX 30 이상\n- S&P500 -10% 이하\n- 나스닥 -15% 이하")
with c3:
    st.error("### **2배수 (초공포)**\n- VIX 35 이상\n- S&P500 -15% 이하\n- 나스닥 -20% 이하")

# 4. 현재 배율 결정 및 상태 출력
vix = market['VIX']['current']
sp500_drop = market['S&P 500']['drop']
nasdaq_drop = market['Nasdaq 100']['drop']

multiplier = 1.0
status_msg = "✅ 현재는 **[정기 적립 1배수]** 단계입니다."
status_type = "success"

if vix >= 35 or sp500_drop <= -15 or nasdaq_drop <= -20:
    multiplier = 2.0
    status_msg = "🚨 현재는 **[공격적 매수 2배수]** 단계입니다!"
    status_type = "error"
elif vix >= 30 or sp500_drop <= -10 or nasdaq_drop <= -15:
    multiplier = 1.5
    status_msg = "⚠️ 현재는 **[비중 확대 1.5배수]** 단계입니다."
    status_type = "warning"

if status_type == "success": st.success(status_msg)
elif status_type == "warning": st.warning(status_msg)
else: st.error(status_msg)

# 5. 이번 주 매수 실행 표 (주 500만 원 기준)
st.divider()
st.subheader(f"🗓 이번 주 매수 실행 금액 (배율: {multiplier}배)")

base_data = {
    "종목명": ["SCHD (배당성장)", "TDF 2045 (자산배분)", "S&P 500 (시장평균)", "나스닥 100 (기술성장)"],
    "기본 금액(만)": [150, 150, 100, 100],
    "비중": ["30%", "30%", "20%", "20%"]
}

df = pd.DataFrame(base_data)
df['이번 주 매수금액(만)'] = (df['기본 금액(만)'] * multiplier).astype(int)

# 표 출력
st.table(df[['종목명', '비중', '기본 금액(만)', '이번 주 매수금액(만)']])

# 최종 합계 표시
total_buy = df['이번 주 매수금액(만)'].sum()
st.metric("💰 이번 주 입금 총액", f"{total_buy}만 원", 
          delta=f"기본 대비 +{total_buy-500}만" if total_buy > 500 else None)

st.caption("Tip: 매주 목요일 오전 10시 알람이 울리면, 이 앱을 열어 실시간 배수를 확인하고 매수하세요!")
