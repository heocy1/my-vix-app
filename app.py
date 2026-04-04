import streamlit as st
import yfinance as yf
import pandas as pd

# 제목 및 VIX 지수 가져오기
st.title("📈 나의 52주 투자 비서")
vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
st.metric("현재 VIX 지수", f"{vix:.2f}")

# 설정 (슬라이더로 조절 가능)
st.sidebar.header("⚙️ VIX 설정")
v1 = st.sidebar.slider("주의 단계 VIX", 15, 25, 20)
p1 = st.sidebar.number_input("주의시 추가 매수(%)", value=10)
v2 = st.sidebar.slider("공포 단계 VIX", 25, 45, 30)
p2 = st.sidebar.number_input("공포시 추가 매수(%)", value=20)

# 배수 결정 로직
mul = 1.0
if vix >= v2:
    mul = 1 + (p2/100)
    st.error(f"🔥 공포! 지수 종목 {p2}% 추가 매수")
elif vix >= v1:
    mul = 1 + (p1/100)
    st.warning(f"⚠️ 주의! 지수 종목 {p1}% 추가 매수")
else:
    st.success("✅ 평시! 정기 적립 유지")

# 매수 리스트 계산
base = {"종목": ["SCHD", "TDF 2045", "S&P 500", "나스닥 100"], "기본": [136, 136, 90, 90]}
df = pd.DataFrame(base)
df['최종 매수액(만)'] = df.apply(lambda x: int(x['기본'] * mul) if x['종목'] in ['S&P 500', '나스닥 100'] else x['기본'], axis=1)
st.table(df)
