import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, date, timedelta

# 1. 앱 설정
st.set_page_config(page_title="퇴직연금 매수기", layout="centered")

# 2. 스타일 설정 (기존 동일)
st.markdown("""
    <style>
    .main-title { font-size: 1.6rem; font-weight: 700; text-align: center; margin-bottom: 1.2rem; }
    .metric-table { width: 100%; text-align: center; background-color: #1e1e1e; border-radius: 10px; margin-bottom: 20px; }
    .metric-table th { padding: 10px; color: #bbb; font-size: 0.85rem; }
    .metric-table td { padding: 15px; font-size: 1.3rem; font-weight: 700; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #2e7d32; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">📉 퇴직연금 자동 매수 가이드</p>', unsafe_allow_html=True)

# 3. 시장 데이터 가져오기
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

# 4. 상단 지수 현황 표
st.markdown(f"""
<table class="metric-table">
    <tr><th>VIX 지수</th><th>S&P 500 하락률</th><th>Nasdaq 100 하락률</th></tr>
    <tr><td>{market['VIX']['current']:.2f}</td><td style="color:#ff4b4b">{market['S&P500']['drop']:.1f}%</td><td style="color:#ff4b4b">{market['Nasdaq100']['drop']:.1f}%</td></tr>
</table>
""", unsafe_allow_html=True)

# --- [5. 자동 날짜 및 누적 로직] ---
START_DATE = date(2026, 5, 1)  # 시작 기준일
# 시작일 이후 첫 번째 화요일 찾기 (5월 5일)
first_tuesday = START_DATE + timedelta(days=(1 - START_DATE.weekday() + 7) % 7)
if first_tuesday < START_DATE: first_tuesday += timedelta(days=7)

today = date.today()
# 오늘까지 경과한 화요일 횟수 계산 (자동 누적용)
if today < first_tuesday:
    weeks_passed = 0
else:
    weeks_passed = ((today - first_tuesday).days // 7) + 1

# 6. 설정값 (하단 expander와 연결됨)
full_budget_val = 24900
base_total_val = 500
u_schd_val, u_tdf_val, u_sp500_val, u_nasdaq_val = 30, 30, 20, 20

# 7. 보정안 및 매수 테이블 계산
vix, sp_drop, nd_drop = market['VIX']['current'], market['S&P500']['drop'], market['Nasdaq100']['drop']
multiplier = 1.0
# (기존 보정안 로직 동일하게 적용...)
if vix >= 30 or sp_drop <= -15: multiplier = 2.0 # 예시

# 이번 주 매수 목록 생성
buy_list = []
for name, weight in zip(["SCHD", "TDF 2045", "S&P 500", "나스닥 100"], [u_schd_val, u_tdf_val, u_sp500_val, u_nasdaq_val]):
    base_amt = int(base_total_val * (weight / 100))
    final_amt = int(base_amt * multiplier)
    buy_list.append({"종목": name, "비중": f"{weight}%", "기본매수액": f"{base_amt}만", "최종매수액": f"**{final_amt}만**"})

st.table(pd.DataFrame(buy_list))

# 8. 자산 관리 대시보드 (자동 계산 포함)
st.markdown("---")
weekly_total = int(base_total_val * multiplier)

# 세션 상태 초기화 (수동 기록용)
if 'manual_invested' not in st.session_state:
    st.session_state.manual_invested = 0

col_info, col_btn = st.columns([1.8, 1.2])
with col_info:
    st.info(f"📅 **매수 시작일:** {first_tuesday} (매주 화요일)")
    st.markdown(f"#### 💰 금주 매수액: **{weekly_total}만**")
    
    # 자동 계산: (지나온 주차 * 기본매수액) + 이번 주 보정액
    # ※ 주의: 과거 보정배율을 모두 저장하지 않으므로, 과거는 1.0x로 가정하거나 수동기록 사용 권장
    auto_estimated = weeks_passed * base_total_val 
    remaining = full_budget_val - st.session_state.manual_invested
    
    st.write(f"📊 **실제 누적 매수:** {st.session_state.manual_invested}만")
    st.write(f"📉 **남은 예산:** {remaining}만 / {full_budget_val}만")

with col_btn:
    if st.button("이번 주 매수 완료"):
        st.session_state.manual_invested += weekly_total
        st.success("기록되었습니다!")
        st.rerun()

st.progress(min(st.session_state.manual_invested / full_budget_val, 1.0))

# 9. 설정 및 가이드 (하단 배치)
with st.expander("⚙️ 설정 및 보정안 기준", expanded=False):
    # (기존 설정 코드...)
    st.write("매주 화요일 14:00에 맞춰 앱을 확인하세요.")
