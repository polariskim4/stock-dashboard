import streamlit as st
import yfinance as yf
import pandas as pd
import time  # time 모듈 추가

# 페이지 기본 설정
st.set_page_config(page_title="Stock Dashboard", layout="wide")

st.title("📈 주식 벤치마크 및 분석 대시보드")

# 벤치마크 티커 목록 (FNGS 추가)
BENCHMARK_TICKERS = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'TSLA', 'NVDA', 'MU', 'PLTR', 'IREN', 'IONQ', 'FNGS']

# 숫자 포맷팅 함수
def format_large_number(num):
    if pd.isna(num) or num == 'N/A' or num is None:
        return "N/A"
    try:
        return f"${float(num) / 1_000_000_000:,.2f}B"
    except (ValueError, TypeError):
        return "N/A"

def format_percent(num):
    if pd.isna(num) or num == 'N/A' or num is None:
        return "N/A"
    try:
        return f"{float(num) * 100:.2f}%"
    except (ValueError, TypeError):
        return "N/A"

# 데이터 가져오기 함수 (캐싱 및 에러 디버깅 적용)
@st.cache_data(ttl=3600)
def get_financial_data(tickers):
    data = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            # 야후 파이낸스 차단 방지를 위해 0.5초 대기
            time.sleep(0.5) 
            info = stock.info
            
            data.append({
                "Ticker": ticker,
                "시총 (Market Cap)": format_large_number(info.get('marketCap')),
                "P/E": round(info.get('trailingPE'), 2) if isinstance(info.get('trailingPE'), (int, float)) else 'N/A',
                "PEG": info.get('pegRatio', 'N/A'),
                "매출액 (Revenue)": format_large_number(info.get('totalRevenue')),
                "영업이익 (Op Income)": format_large_number(info.get('operatingIncome', info.get('ebitda'))), 
                "마진 (Margin)": format_percent(info.get('operatingMargins')),
                "매출액 성장률": format_percent(info.get('revenueGrowth')),
                "영업이익 성장률": format_percent(info.get('earningsGrowth'))
            })
        except Exception as e:
            # 단순 'Error' 대신 실제 발생한 에러 메시지를 출력하여 원인 파악
            data.append({
                "Ticker": ticker, 
                "시총 (Market Cap)": f"Error: {str(e)}"
            })
            
    return pd.DataFrame(data)

# --- 이하 코드는 이전과 동일하게 유지 ---
# 1. 벤치마크 테이블 출력
st.header("🏆 벤치마크 종목")
with st.spinner('벤치마크 데이터를 불러오는 중입니다...'):
    df_benchmark = get_financial_data(BENCHMARK_TICKERS)
    st.dataframe(df_benchmark, use_container_width=True, hide_index=True)

# ... (나머지 코드)
