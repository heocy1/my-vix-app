import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 앱 설정 (모바일 커스텀 레이아웃)
st.set_page_config(page_title="퇴직연금 가이드", layout="centered")

st.markdown("""
    <style>
    .main .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    h1 {font-size: 1.2rem !important; margin-bottom: 1.5rem; text-align: left;}
    
    /* 지표 섹션 스타일링 */
    .metric-label {font-size: 0.8rem; color: #888; margin-bottom: -5px;}
    .metric-value {font-size: 1.3rem; font-weight: bold; margin-bottom: 2px;}
    .metric-delta {font-size: 0.9rem; font-weight: bold;}
    
    /* 구분선 및 간격 */
    hr {margin: 10px 0;}
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

# 3. 사용자 요청 레이아웃 (왼쪽 VIX / 오른쪽 S&P500, Nasdaq100)
col_left, col_right = st.columns([1, 2.5]) # 왼쪽 1 : 오른쪽 2.5 비율

with col_left:
    st.markdown('<p class="metric-label">VIX</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="metric-value">{market["VIX"]["current"]:.1f}</p>', unsafe_allow_html=True)

with col_right:
    # S&P 500 (상단)
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.markdown('<p class="metric-label">S&P 500</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">{int(market["S&P500"]["current"]):,}</p>', unsafe_allow_html=True)
    with c2:
        color = "#ff4b4b" if market["S&P500"]["drop"] < 0 else "#00c853"
        st.markdown('<p class="metric-label">&nbsp;</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-delta" style="color:{color}">↓ {market["S&P500"]["drop"]:.1f}%</p>', unsafe_allow_html=True)
    
    st.markdown("<hr style='margin:5px 0; border:0.1px solid rgba(150,150,150,0.1);'>", unsafe_allow_html=True)
    
    # Nasdaq 100 (하단)
    c3, c4 = st.columns([1.5, 1])
    with c3:
        st.markdown('<p class="metric-label">Nasdaq 100</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-value">{int(market["Nasdaq100"]["current"]):,}</p>', unsafe_allow_html=True)
    with c4:
        color = "#ff4b4b" if market["Nasdaq100"]["drop"] < 0 else "#00c853"
        st.markdown('<p class="metric-label">&nbsp;</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="metric-delta" style="color:{color}">↓ {market["Nasdaq100"]["drop"]:.1f}%</p>', unsafe_allow_html=True)

st.write("") # 간격 띄우기

# 4. 설정부
with st.expander("⚙️ 기본 설정 (평시 기준)", expanded=False):
    base_total = st.number_input("주당 기본 총액 (만 원)", value=500, step=10)

# 5. 배율 및 비중 판단 로직
vix = market['VIX']['current']
sp_drop = market['S&P500']['drop']
nd_drop = market['Nasdaq100']['drop']

w_schd, w_tdf, w_sp500, w_nasdaq = 30, 30, 20, 20
multiplier = 1.0
status_style, status_msg = "success", "✅ 1.0x (평시)"

if vix >= 50 or sp_drop <= -35:
    multiplier, status_style, status_msg = 3.0, "error", "💀 3.0x (대공황급)"
    w_schd, w_nasdaq = 20, 30
elif vix >= 45 or sp_drop <= -25:
    multiplier, status_style, status_msg = 2.5, "error", "🚨 2.5x (초공포)"
    w_schd, w_nasdaq = 20, 30
elif vix >= 30 or sp_drop <= -15:
    multiplier, status_style, status_msg = 2.0, "error", "🔥 2.0x (공포)"
    w_schd, w_nasdaq = 25, 25
elif vix >= 25 or sp_drop <= -8:
    multiplier, status_style, status_msg = 1.2, "warning", "⚠️ 1.2x (주의)"

if nd_drop <= -30:
    w_schd, w_nasdaq = 20, 30
    status_msg += " (QQQ 특수대응)"

getattr(st, status_style)(f"**현재 적용 단계: {status_msg}**")

# 6. 매수 실행 표
names = ["SCHD", "TDF 2045", "S&P 500", "나스닥 100"]
weights = [w_schd, w_tdf, w_sp500, w_nasdaq]
buy_data = []

for name, weight in zip(names, weights):
    base_amt = int(base_total * (weight / 100))
    final_amt = int(base_amt * multiplier)
    buy_data.append({"종목": name, "비중": f"{weight}%", "매수액": f"**{final_amt}만**"})

st.table(pd.DataFrame(buy_data))

# 7. 하단 총액
st.subheader(f"💰 총 입금액: {int(base_total * multiplier)}만 원")
