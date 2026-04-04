import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 앱 설정
st.set_page_config(page_title="퇴직연금 가이드", layout="centered")

st.markdown("""
    <style>
    .main .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    h1 {font-size: 1.2rem !important; margin-bottom: 1rem;}
    div[data-testid="stMetricValue"] {font-size: 1.1rem !important;}
    div[data-testid="stMetricLabel"] {font-size: 0.8rem !important;}
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

# 3. 시장 지표
c1, c2, c3 = st.columns(3, gap="small")
c1.metric("VIX", f"{market['VIX']['current']:.1f}")
c2.metric("S&P 500", f"{int(market['S&P500']['current']):,}", f"{market['S&P500']['drop']:.1f}%")
c3.metric("Nasdaq 100", f"{int(market['Nasdaq100']['current']):,}", f"{market['Nasdaq100']['drop']:.1f}%")

# 4. 설정부 (기본값 설정)
with st.expander("⚙️ 기본 설정 (평시 기준)", expanded=False):
    base_total = st.number_input("주당 기본 총액 (만 원)", value=500, step=10)
    st.caption("※ 공포/초공포 단계 진입 시 설정된 비중으로 자동 전환됩니다.")

# 5. 배율 판단 및 비중 자동 결정 로직
vix = market['VIX']['current']
sp_drop = market['S&P500']['drop']

# 기본 비중 (평시/주의)
w_schd, w_tdf, w_sp500, w_nasdaq = 30, 30, 20, 20
multiplier = 1.0
status_style, status_msg = "success", "✅ 1.0x (평시)"

# 조건 판단 및 비중 변경
if vix >= 40 or sp_drop <= -20:
    multiplier, status_style, status_msg = 2.5, "error", "🚨 2.5x (초공포)"
    w_schd, w_nasdaq = 20, 30  # 요청 사항 반영
elif vix >= 30 or sp_drop <= -10:
    multiplier, status_style, status_msg = 2.0, "error", "🔥 2.0x (공포)"
    w_schd, w_nasdaq = 25, 25  # 요청 사항 반영
elif vix >= 25 or sp_drop <= -5:
    multiplier, status_style, status_msg = 1.2, "warning", "⚠️ 1.2x (주의)"

getattr(st, status_style)(f"**현재 적용 단계: {status_msg}**")

# 6. 매수 실행 표 계산
names = ["SCHD", "TDF 2045", "S&P 500", "나스닥 100"]
weights = [w_schd, w_tdf, w_sp500, w_nasdaq]
buy_data = []

for name, weight in zip(names, weights):
    # 각 단계별 비중을 적용한 1배수 기준 금액 계산
    base_amt = int(base_total * (weight / 100))
    # 배율 적용 최종 금액
    final_amt = int(base_amt * multiplier)
    buy_data.append({
        "종목": name,
        "비중": f"{weight}%",
        "금액": f"**{final_amt}만 원**"
    })

st.table(pd.DataFrame(buy_data))

# 7. 하단 요약
final_total = int(base_total * multiplier)
st.subheader(f"💰 총 입금액: {final_total}만 원")

with st.expander("ℹ️ 단계별 비중/배율 기준", expanded=False):
    st.markdown("""
    <div class="compact-table">

    | 단계 | 배율 | S&P 500 조건 | SCHD : 나스닥 비중 |
    | :--- | :---: | :--- | :--- |
    | **평시** | **1.0x** | 전고점 부근 | 30% : 20% |
    | **주의** | **1.2x** | -5%↓ (VIX 25↑) | 30% : 20% |
    | **공포** | **2.0x** | -10%↓ (VIX 30↑) | **25% : 25%** |
    | **초공포**| **2.5x** | -20%↓ (VIX 40↑) | **20% : 30%** |

    </div>
    """, unsafe_allow_html=True)
