import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 앱 설정 및 스타일 개선
st.set_page_config(page_title="퇴직연금 매수기", layout="centered")

st.markdown("""
    <style>
    .main .block-container {padding-top: 1.5rem; padding-bottom: 1rem;}
    /* 제목이 한 줄로 나오도록 폰트 크기 조정 및 줄바꿈 방지 */
    .main-title {
        font-size: 1.3rem !important; 
        font-weight: 700; 
        text-align: center; 
        margin-bottom: 1.2rem;
        color: #ffffff;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
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
        font-size: 0.8rem;
        color: #bbb;
    }
    .metric-table td {
        padding: 15px;
        font-size: 1.2rem;
        font-weight: 700;
        border-bottom: 1px solid #444;
    }
    .drop-val { color: #ff4b4b; }
    .rsi-val { color: #4bafff; }
    </style>
    """, unsafe_allow_html=True)

# 2. 메인 타이틀 (줄바꿈 방지 스타일 적용)
st.markdown('<p class="main-title">📉 퇴직연금 실속형 매수 가이드</p>', unsafe_allow_html=True)

# 3. 데이터 로직 보완 (nan 방지)
@st.cache_data(ttl=3600)
def get_market_data():
    # 지수 기호 확인: S&P500(^GSPC), Nasdaq100(^NDX)
    tickers = {"VIX": "^VIX", "S&P500": "^GSPC", "Nasdaq100": "^NDX"}
    data = {}
    for name, symbol in tickers.items():
        ticker = yf.Ticker(symbol)
        # 1년치 데이터를 충분히 가져옴
        hist = ticker.history(period="1y")
        
        if hist.empty:
            data[name] = {"current": 0.0, "drop": 0.0, "rsi": 0.0}
            continue
            
        current = hist['Close'].iloc[-1]
        # nan 방지를 위해 값이 있는 데이터 중 최대값 추출
        high = hist['Close'].max() 
        
        # 하락률 계산 (분모가 0이거나 high가 없는 경우 방어 로직)
        if high > 0:
            drop = ((current - high) / high) * 100
        else:
            drop = 0.0
            
        # RSI 계산
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        # 분모가 0이 되는 경우 처리
        rs = gain / loss.replace(0, 1e-9) 
        rsi = 100 - (100 / (1 + rs))
        
        data[name] = {
            "current": current, 
            "drop": drop if not pd.isna(drop) else 0.0, 
            "rsi": rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0
        }
    return data

try:
    market = get_market_data()
except:
    st.error("데이터를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.")
    st.stop()

# 4. 상단 지수 현황 (하락률 표시 보완)
st.markdown(f"""
<table class="metric-table">
    <tr>
        <th>VIX 지수</th>
        <th>S&P 500 하락률</th>
        <th>S&P 500 RSI</th>
        <th>Nasdaq 100 하락률</th>
    </tr>
    <tr>
        <td>{market['VIX']['current']:.2f}</td>
        <td class="drop-val">{market['S&P500']['drop']:.1f}%</td>
        <td class="rsi-val">{market['S&P500']['rsi']:.1f}</td>
        <td class="drop-val">{market['Nasdaq100']['drop']:.1f}%</td>
    </tr>
</table>
""", unsafe_allow_html=True)

# 이후 섹션(5~10)은 기존 코드를 그대로 유지하시면 됩니다.
