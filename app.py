import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 앱 설정
st.set_page_config(page_title="퇴직연금 매수기", layout="centered")

st.markdown("""
    <style>
    .main .block-container {padding-top: 1.5rem; padding-bottom: 1rem;}
    
    /* 제목 크기를 적절하게 조절 (이전보다 작게) */
    .main-title {
        font-size: 1.6rem !important; 
        font-weight: 700; 
        text-align: center; 
        margin-bottom: 1.5rem;
        color: #ffffff;
    }
    
    /* 지수 폰트 크기 및 스타일 (가로 배치를 위해 최적화) */
    div[data-testid="stMetricValue"] {
        font-size: 1.2rem !important; 
        font-weight: 700 !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem !important; 
        font-weight: 500 !important;
        margin-bottom: 2px;
    }
    
    /* 컬럼 간격 조정 */
    [data-testid="column"] {
        padding: 0 5px !important;
    }

    .compact-table {font-size: 0.85rem !important; line-height: 1.3;}
    .stButton>button {width: 100%; border-radius: 8px; height: 3.5em; background-color: #2e7d32; color: white; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

# 2. 앱 화면 타이틀 (크기 축소 적용)
st.markdown('<p class="main-title">📉 퇴직연금 매수 가이드</p>', unsafe_allow_html=True)

# 3. 데이터 가져오기
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

# 4. 시장 지표 (완전한 가로 3열 배치)
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("VIX 지수", f"{market['VIX']['current']:.1f}")
with c2:
    st.metric("S&P 500", f"{int(market['S&P500']['current']):,}", f"{market['S&P500']['drop']:.1f}%")
with c3:
    st.metric("Nasdaq 100", f"{int(market['Nasdaq100']['current']):,}", f"{market['Nasdaq100']['drop']:.1f}%")

st.markdown("<br>", unsafe_allow_html=True)

# 5. 설정부 (예산 2.49억)
with st.expander("⚙️ 기본 설정 및 전체 예산", expanded=False):
    full_budget = st.number_input("전체 투자 예산 (만 원)", value=24900, step=100) 
    base_total = st.number_input("주당 기본 총액 (만 원)", value=500, step=10)
    
    st.write("**평시(1.0x) 기준 비중 설정 (%)**")
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        u_schd = st.number_input("SCHD", 0, 100, 30)
        u_tdf = st.number_input("TDF 2045", 0, 100, 30)
    with col_w2:
        u_sp500 = st.number_input("S&P 500", 0, 100, 20)
        u_nasdaq = st.number_input("나스닥 100", 0, 100, 20)

# 6. 배율 및 비중 판단 로직
vix = market['VIX']['current']
sp_drop = market['S&P500']['drop']
nd_drop = market['Nasdaq100']['drop']

w_schd, w_tdf, w_sp500, w_nasdaq = u_schd, u_tdf, u_sp500, u_nasdaq
multiplier = 1.0
status_style, status_msg = "success", "✅ 1.0x (평시)"

if vix >= 45 or sp_drop <= -25:
    multiplier, status_style, status_msg = 2.5, "error", "🚨 2.5x (초공포)"
    w_schd, w_nasdaq = 20, 30
elif vix >= 30 or sp_drop <= -15:
    multiplier, status_style, status_msg = 2.0, "error", "🔥 2.0x (공포)"
    w_schd, w_nasdaq = 25, 25
elif vix >= 25 or sp_drop <= -8:
    multiplier, status_style, status_msg = 1.2, "warning", "⚠️ 1.2x (주의)"

if nd_drop <= -30:
    w_schd, w_nasdaq = 20, 30
    status_msg += " (QQQ 대응 ON)"

getattr(st, status_style)(f"**현재 적용 단계: {status_msg}**")

# 7. 매수 실행 표
names = ["SCHD", "TDF 2045", "S&P 500", "나스닥 100"]
weights = [w_schd, w_tdf, w_sp500, w_nasdaq]
buy_data = []

for name, weight in zip(names, weights):
    base_amt = int(base_total * (weight / 100))
    final_amt = int(base_amt * multiplier)
    buy_data.append({"종목": name, "비중": f"{weight}%", "매수액": f"**{final_amt}만**"})

st.table(pd.DataFrame(buy_data))

# 8. 누적 금액 및 잔액 확인
st.markdown("---")
if 'total_invested' not in st.session_state:
    st.session_state.total_invested = 0

weekly_total = int(base_total * multiplier)
col_summary, col_action = st.columns([1.8, 1.2])

with col_summary:
    st.markdown(f"#### 💰 금주 매수: **{weekly_total}만**")
    remaining = full_budget - st.session_state.total_invested
    st.write(f"📊 누적: {st.session_state.total_invested}만 / 잔액: {remaining}만")

with col_action:
    if st.button("매수 완료 기록"):
        st.session_state.total_invested += weekly_total
        st.rerun()

st.progress(min(st.session_state.total_invested / full_budget, 1.0))

# 9. 상세 기준표
with st.expander("ℹ️ 보정안 상세 기준", expanded=False):
    st.markdown(f"""
    <div class="compact-table">

    | 단계 | 배율 | 조건 | 비중 전략 |
    | :--- | :---: | :--- | :--- |
    | **평시** | 1.0x | 기본 적립 | 사용자 설정 |
    | **주의** | 1.2x | VIX 25↑ / S&P -8%↓ | 사용자 설정 |
    | **공포** | 2.0x | VIX 30↑ / S&P -15%↓ | 나스닥 25% |
    | **초공포**| 2.5x | VIX 45↑ / S&P -25%↓ | 나스닥 30% |

    **※ 특수:** 나스닥 100 **-30%** 돌파 시 비중 **30%** 고정.
    </div>
    """, unsafe_allow_html=True)
