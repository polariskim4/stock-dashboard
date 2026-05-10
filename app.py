import streamlit as st
import yfinance as yf
import pandas as pd
import time

# 페이지 설정
st.set_page_config(page_title="Stock Analysis Dashboard", layout="wide")

st.title("📈 주식 벤치마크 및 분석 대시보드")

# 벤치마크 대상 목록
BENCHMARK_TICKERS = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'TSLA', 'NVDA', 'MU', 'PLTR', 'IREN', 'IONQ']

def format_large_number(num):
    if pd.isna(num) or num is None: return "N/A"
    return f"${num / 1_000_000_000:,.2f}B"

def format_percent(num):
    if pd.isna(num) or num is None: return "N/A"
    return f"{num * 100:.2f}%"

@st.cache_data(ttl=3600)
def get_stock_info(tickers):
    results = []
    for t in tickers:
        try:
            s = yf.Ticker(t)
            time.sleep(0.2) # API 차단 방지
            info = s.info
            results.append({
                "Ticker": t,
                "시총 (Market Cap)": format_large_number(info.get('marketCap')),
                "P/E": round(info.get('trailingPE', 0), 2) if info.get('trailingPE') else "N/A",
                "PEG": info.get('pegRatio', 'N/A'),
                "매출액 (Revenue)": format_large_number(info.get('totalRevenue')),
                "영업이익 (Op Income)": format_large_number(info.get('operatingIncome', info.get('ebitda'))),
                "마진 (Margin)": format_percent(info.get('operatingMargins')),
                "매출액 성장률": format_percent(info.get('revenueGrowth')),
                "영업이익 성장률": format_percent(info.get('earningsGrowth'))
            })
        except:
            results.append({"Ticker": t, "시총 (Market Cap)": "Error"})
    return pd.DataFrame(results)

# --- 1. 벤치마크 섹션 ---
st.header("🏆 벤치마크 종목")
df_bench = get_stock_info(BENCHMARK_TICKERS)
st.dataframe(df_bench, use_container_width=True, hide_index=True)

st.divider()

# --- 2. 개별 종목 분석 섹션 ---
st.header("🔍 개별 종목 상세 분석")
col1, col2 = st.columns([1, 3])

with col1:
    search_ticker = st.text_input("분석할 티커를 입력하세요:", value="FNGS").upper()
    if search_ticker:
        with st.spinner(f'{search_ticker} 데이터 로드 중...'):
            df_target = get_stock_info([search_ticker])
            # 세로 형태로 보기 좋게 변환
            st.write(f"### {search_ticker} 재무 지표")
            st.table(df_target.iloc[0].drop("Ticker"))

with col2:
    if search_ticker:
        st.write(f"### {search_ticker} Monthly Chart (Finviz)")
        # Finviz 월봉(Monthly) 차트 URL
        # ty=c (Candle), ta=1 (Technical Analysis), p=m (Monthly)
        chart_url = f"https://charts2.finviz.com/chart.ashx?t={search_ticker}&ty=c&ta=1&p=m"
        
        # 이미지 태그를 사용하여 직접 렌더링 (가장 확실한 방법)
        st.markdown(
            f'<img src="{chart_url}" style="width:100%;">', 
            unsafe_allow_html=True
        )
        
        st.caption(f"출처: Finviz.com - {search_ticker} 월봉 기술적 분석 차트")
