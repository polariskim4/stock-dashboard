import streamlit as st
import yfinance as yf
import pandas as pd

# 페이지 기본 설정
st.set_page_config(page_title="Stock Dashboard", layout="wide")

st.title("📈 주식 벤치마크 및 분석 대시보드")

# 벤치마크 티커 목록
BENCHMARK_TICKERS = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'TSLA', 'NVDA', 'MU', 'PLTR', 'IREN', 'IONQ']

# 숫자 포맷팅 함수
def format_large_number(num):
    if pd.isna(num) or num == 'N/A':
        return "N/A"
    return f"${num / 1_000_000_000:,.2f}B" # 10억 달러(Billion) 단위로 변환

def format_percent(num):
    if pd.isna(num) or num == 'N/A':
        return "N/A"
    return f"{num * 100:.2f}%"

# 데이터 가져오기 함수 (캐싱 적용하여 속도 향상)
@st.cache_data(ttl=3600) # 1시간마다 데이터 갱신
def get_financial_data(tickers):
    data = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            data.append({
                "Ticker": ticker,
                "시총 (Market Cap)": format_large_number(info.get('marketCap', 'N/A')),
                "P/E": round(info.get('trailingPE', 'N/A'), 2) if isinstance(info.get('trailingPE'), (int, float)) else 'N/A',
                "PEG": info.get('pegRatio', 'N/A'),
                "매출액 (Revenue)": format_large_number(info.get('totalRevenue', 'N/A')),
                # yfinance에서 제공하는 기본 operating margin 등을 활용
                "영업이익 (Op Income)": format_large_number(info.get('operatingIncome', info.get('ebitda', 'N/A'))), 
                "마진 (Margin)": format_percent(info.get('operatingMargins', 'N/A')),
                "매출액 성장률": format_percent(info.get('revenueGrowth', 'N/A')),
                "영업이익 성장률": format_percent(info.get('earningsGrowth', 'N/A')) # EPS 성장률로 대체
            })
        except Exception:
            data.append({"Ticker": ticker, "시총 (Market Cap)": "Error"})
            
    return pd.DataFrame(data)

# 1. 벤치마크 테이블 출력
st.header("🏆 벤치마크 종목")
with st.spinner('벤치마크 데이터를 불러오는 중입니다...'):
    df_benchmark = get_financial_data(BENCHMARK_TICKERS)
    st.dataframe(df_benchmark, use_container_width=True, hide_index=True)

st.divider()

# 2. 개별 종목 검색 및 Finviz 차트
st.header("🔍 개별 종목 검색")
ticker_input = st.text_input("종목 티커를 입력하세요 (예: FNGS, SPY)", "").upper()

if ticker_input:
    st.subheader(f"[{ticker_input}] 재무 정보")
    with st.spinner(f'{ticker_input} 데이터를 불러오는 중입니다...'):
        # 개별 종목 데이터 테이블
        df_single = get_financial_data([ticker_input])
        st.dataframe(df_single, use_container_width=True, hide_index=True)
        
        # Finviz Monthly 차트 출력
        st.subheader(f"[{ticker_input}] Finviz Monthly Chart")
        # Finviz URL 구조: t=티커, ty=c(캔들), ta=0(기본), p=m(월봉)
        finviz_url = f"https://finviz.com/chart.ashx?t={ticker_input}&ty=c&ta=0&p=m"
        
        try:
            st.image(finviz_url, caption=f"{ticker_input} 월봉 차트", use_column_width=True)
        except Exception as e:
            st.warning("Finviz 서버에서 이미지를 직접 불러오는 것을 차단했거나, 유효하지 않은 티커입니다.")
            st.markdown(f"[여기 클릭하여 Finviz에서 직접 차트 보기](https://finviz.com/quote.ashx?t={ticker_input})")
