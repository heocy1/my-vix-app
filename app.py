import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 앱 설정 (다크 모드 가독성 보강)
st.set_page_config(page_title="퇴직연금 매수 가이드", layout="centered")

# CSS: 다크 모드와 라이트 모드 모두에서 글자가 잘 보이도록 설정
st.markdown("""
    <style>
    /* 메인 컨테이너 여백 조절 */
    .main .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    
    /* 제목 크기 및 색상 */
    h1 {font-size: 1.5rem !important;}
    
    /* 메트릭 박스 스타일 (다크모드 대응) */
    [data-testid="stMetric"] {
        background-color: rgba(150, 150, 150, 0.1); /* 반투명 배경 */
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(150, 150, 150, 0.2);
    }
    
    /* 메트릭 글자색 강제 설정 (어떤 테마에서도 잘 보이게) */
    [data-testid="stMetricLabel"] {color: var(--text-color) !important;}
    [data-testid="stMetricValue"] {color: var(--text-color) !important;}
    
    /* 테이블 가독성 보강 */
    .stTable {font-size: 0.9rem !important;}
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

# 3. 시장 지표 (가독성 높은 배치)
st.caption("🌐 실시간 시장 지표")
c1, c2, c3 = st.columns(3)
c1.metric("VIX (공포)", f"{market['VIX']['current']:.2f}")
# 하락률(delta)의 색상은 Streamlit이 자동으로 빨강/초록으로 처리합니다.
c2.metric("S&P 500", f"{int(market['S&P500']['current']):,}", f"{market['S&P500']['drop']:.1f}%", delta_color="inverse")
c3.metric("Nasdaq 100", f"{int(market['Nasdaq100']['current']):,}", f"{market['Nasdaq100']['drop']:.1f}%", delta_color="inverse")

# 4. 비중 및 기본 설정
with st.expander("⚙️ 투자 비중 및 기본금 설정", expanded=False):
    base_total = st.number_input("주당 기본 매수 총액 (만 원)", value=500, step=10)
    st.write("---")
    col_a, col_b = st.columns(2)
    with col_a:
        w_schd = st.number_input("SCHD (%)", 0, 100, 30)
        w_tdf = st.number_input("TDF 2045 (%)", 0, 100, 30)
    with col_b:
        w_sp500 = st.number_input("S&P 500 (%)", 0, 100, 20)
        w_nasdaq = st.number_input("나스닥 100 (%)", 0, 100, 20)
    
    total_w = w_schd + w_tdf + w_sp500 + w_nasdaq
    if total_w != 100:
        st.error(f"비중 합계: {total_w}% (100%로 맞춰주세요)")

# 5. 배율 판단 로직
vix = market['VIX']['current']
sp_drop = market['S&P500']['drop']
nd_drop = market['Nasdaq100']['drop']

multiplier = 1.0
status_style = "success"
status_msg = "✅ 1배수 (평시)"

if vix >= 35 or sp_drop <= -15 or nd_drop <= -20:
    multiplier = 2.0
    status_style = "error"
    status_msg = "🚨 2배수 (초공포)"
elif vix >= 30 or sp_drop <= -10 or nd_drop <= -15:
    multiplier = 1.5
    status_style = "warning"
    status_msg = "⚠️ 1.5배수 (공포)"

# 상태 알림 (배경색이 있는 박스라 다크모드에서도 잘 보임)
getattr(st, status_style)(f"**{status_msg} 적용 중 (배율: {multiplier}x)**")

# 6. 매수 금액 계산 및 표 출력
names = ["SCHD", "TDF 2045", "S&P 500", "나스닥 100"]
weights = [w_schd, w_tdf, w_sp500, w_nasdaq]

buy_data = []
for name, weight in zip(names, weights):
    base_amt = int(base_total * (weight / 100))
    final_amt = int(base_amt * multiplier)
    buy_data.append({
        "종목명": name,
        "비율": f"{weight}%",
        "기본가": f"{base_amt}만",
        "매수액": f"**{final_amt}만**"
    })

st.table(pd.DataFrame(buy_data))

# 7. 하단 요약
final_total = int(base_total * multiplier)
st.subheader(f"💰 총 입금액: {final_total}만 원")
