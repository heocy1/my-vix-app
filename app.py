import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 앱 설정
st.set_page_config(page_title="퇴직연금 매수기", layout="centered")

st.markdown("""
    <style>
    .main .block-container {padding-top: 1.5rem; padding-bottom: 1rem;}
    .main-title {
        font-size: 1.6rem !important; 
        font-weight: 700; 
        text-align: center; 
        margin-bottom: 1.2rem;
        color: #ffffff;
    }
    .metric-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 20px;
        text-align: center;
        background-color: #1e1e1e;
        border-radius: 10px;
    }
    .metric-table th {
        background-color: #333;
        padding: 10px;
        font-size: 0.85rem;
        color: #bbb;
    }
    .metric-table td {
        padding: 15px;
        font-size: 1.3rem;
        font-weight: 700;
        border-bottom: 1px solid #444;
    }
    .drop-val { color: #ff4b4b; }
    .compact-table {font-size: 0.85rem !important; line-height: 1.3;}
    .stButton>button {
        width: 100%; 
        border-radius: 8px; 
        height: 3.5em; 
        background-color: #2e7d32; 
        color: white; 
        font-weight: bold;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 메인 타이틀
st.markdown('<p class="main-title">📉 퇴직연금 매수 가이드</p>', unsafe_allow_html=True)

# 3. 실시간 시장 데이터 호출
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

try:
    market = get_market_data()
except:
    st.error("데이터를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.")
    st.stop()

# 4. 상단 지수 현황
st.markdown(f"""
<table class="metric-table">
    <tr>
        <th>VIX 지수</th>
        <th>S&P 500 하락률</th>
        <th>Nasdaq 100 하락률</th>
    </tr>
    <tr>
        <td>{market['VIX']['current']:.2f}</td>
        <td class="drop-val">{market['S&P500']['drop']:.1f}%</td>
        <td class="drop-val">{market['Nasdaq100']['drop']:.1f}%</td>
    </tr>
</table>
""", unsafe_allow_html=True)

# --- [로직 처리를 위한 초기값 설정] ---
if 'total_invested' not in st.session_state:
    st.session_state.total_invested = 0

# 기본값 설정
full_budget_val = 24900
base_total_val = 500
u_schd_val, u_tdf_val, u_sp500_val, u_nasdaq_val = 30, 30, 20, 20

# 6. 보정안 로직 엔진 (화면 표시 전 계산)
vix, sp_drop, nd_drop = market['VIX']['current'], market['S&P500']['drop'], market['Nasdaq100']['drop']
multiplier = 1.0
status_style, status_msg = "success", "✅ 1.0x (평시)"
w_schd, w_tdf, w_sp500, w_nasdaq = u_schd_val, u_tdf_val, u_sp500_val, u_nasdaq_val

if vix >= 50 or sp_drop <= -35:
    multiplier, status_style, status_msg = 3.0, "error", "💀 3.0x (위기)"
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
    status_msg += " (QQQ 특수 대응)"

# 상태바 출력
getattr(st, status_style)(f"**현재 시장 단계: {status_msg}**")

# 7. 이번 주 매수 실행 테이블 (기본매수액 추가)
names = ["SCHD", "TDF 2045", "S&P 500", "나스닥 100"]
weights = [w_schd, w_tdf, w_sp500, w_nasdaq]
buy_list = []

for name, weight in zip(names, weights):
    # 배율 적용 전 기본 금액
    base_amt = int(base_total_val * (weight / 100))
    # 배율 적용 후 최종 금액
    final_amt = int(base_amt * multiplier)
    
    buy_list.append({
        "종목": name, 
        "비중": f"{weight}%", 
        "기본매수액": f"{base_amt}만", 
        "최종매수액": f"**{final_amt}만**"
    })

# 데이터프레임 생성 및 출력
df_buy = pd.DataFrame(buy_list)
st.table(df_buy)

# 8. 자산 관리 대시보드
st.markdown("---")
weekly_total = int(base_total_val * multiplier)
col_info, col_btn = st.columns([1.8, 1.2])

with col_info:
    st.markdown(f"#### 💰 이번 주 총액: **{weekly_total}만**")
    remaining = full_budget_val - st.session_state.total_invested
    st.write(f"📊 누적: {st.session_state.total_invested}만 / 잔액: {remaining}만")

with col_btn:
    if st.button("매수 완료 기록"):
        st.session_state.total_invested += weekly_total
        st.rerun()

st.progress(min(st.session_state.total_invested / full_budget_val, 1.0))

# 5. 설정 및 예산 관리 섹션
with st.expander("⚙️ 기본 설정 및 전체 예산 관리 (비중/금액 수정)", expanded=False):
    st.info("이곳에서 수정한 값은 다음 계산에 반영됩니다.")
    full_budget_val = st.number_input("전체 투자 예산 (만 원)", value=24900, step=100) 
    base_total_val = st.number_input("주당 기본 매수액 (만 원)", value=500, step=10)
    
    st.write("---")
    st.write("**평시(1.0x) 기준 기본 비중 (%)**")
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        u_schd_val = st.number_input("SCHD", 0, 100, 30)
        u_tdf_val = st.number_input("TDF 2045", 0, 100, 30)
    with col_w2:
        u_sp500_val = st.number_input("S&P 500", 0, 100, 20)
        u_nasdaq_val = st.number_input("나스닥 100", 0, 100, 20)

# 9. 보정안 상세 기준 가이드
with st.expander("ℹ️ 보정안 상세 기준표", expanded=False):
    st.markdown(f"""
    <div class="compact-table">

    | 단계 | 배율 | 조건 (하나라도 해당 시) | 비중 전략 |
    | :--- | :---: | :--- | :--- |
    | **평시** | 1.0x | 하락률 -8% 미만 | 사용자 설정 |
    | **주의** | 1.2x | VIX 25↑ 또는 S&P -8%↓ | 사용자 설정 |
    | **공포** | 2.0x | VIX 30↑ 또는 S&P -15%↓ | 나스닥 25% |
    | **초공포**| 2.5x | VIX 45↑ 또는 S&P -25%↓ | 나스닥 30% |
    | **위기** | 3.0x | VIX 50↑ 또는 S&P -35%↓ | 나스닥 30% |

    **※ 특수 규칙:** 나스닥 100 **-30%** 돌파 시 비중 **30%** 강제 고정.
    </div>
    """, unsafe_allow_html=True)
