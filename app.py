import streamlit as st
import yfinance as yf
import pandas as pd
import time

# 페이지 설정
st.set_page_config(page_title="Stock Analysis Dashboard", layout="wide")

st.title("📈 주식 벤치마크 및 상세 분석 대시보드")

# 벤치마크 대상 목록
DEFAULT_TICKERS = [
    'AAPL', 'MSFT', 'GOOG', 'AMZN', 'TSLA', 'NVDA', 'MU', 'PLTR', 'IREN', 'IONQ',
    'ANET', 'MRVL', 'VRT', 'VST'
]

def format_display_number(num):
    if pd.isna(num) or num == 0 or num is None: return "N/A"
    return f"${num / 1_000_000_000:,.1f}B"

def clean_peg(num):
    if pd.isna(num) or num is None: return "N/A"
    try:
        # 소수점 한자리 표시 통일
        return f"{float(num):.1f}"
    except:
        return "N/A"

@st.cache_data(ttl=3600)
def get_stock_data(tickers):
    results = []
    for t in tickers:
        try:
            s = yf.Ticker(t)
            time.sleep(0.1)
            info = s.info
            raw_market_cap = info.get('marketCap', 0)
            
            # 전고점 대비 등락률 계산 (현재가 / 52주 고가 - 1)
            current_price = info.get('currentPrice')
            high_52w = info.get('fiftyTwoWeekHigh')
            perf_from_high = "N/A"
            if current_price and high_52w:
                perf_val = (current_price / high_52w - 1) * 100
                perf_from_high = f"{perf_val:+.1f}%"

            results.append({
                "Ticker": t,
                "Market Cap (Raw)": raw_market_cap,
                "시총 (Market Cap)": format_display_number(raw_market_cap),
                "P/E": int(info.get('trailingPE')) if info.get('trailingPE') else "N/A",
                "PEG": clean_peg(info.get('pegRatio')),
                # 위치 변경: PEG와 매출액 성장률 사이
                "매출액(Revenue)": format_display_number(info.get('totalRevenue')),
                "영업이익(Op Income)": format_display_number(info.get('operatingCashflow')), # 대략적 영업현황 지표
                "매출액 성장률": f"{info.get('revenueGrowth', 0)*100:.1f}%" if info.get('revenueGrowth') else "N/A",
                "EPS 전망 (5Y)": f"{info.get('earningsQuarterlyGrowth', 0)*100:.1f}%" if info.get('earningsQuarterlyGrowth') else "N/A",
                "전고점 대비": perf_from_high
            })
        except:
            results.append({"Ticker": t, "Market Cap (Raw)": 0})
    
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values(by="Market Cap (Raw)", ascending=False).drop(columns=["Market Cap (Raw)"])
    return df

# --- 데이터 로드 ---
search_ticker = st.text_input("분석할 티커를 입력하세요:", value="ORCL").upper()

with st.spinner('실시간 데이터를 가져오는 중...'):
    df_main = get_stock_data(DEFAULT_TICKERS)
    if search_ticker and search_ticker not in DEFAULT_TICKERS:
        df_search = get_stock_data([search_ticker])
        df_final = pd.concat([df_main, df_search], ignore_index=True)
    else:
        df_final = df_main

# --- 1. 비교 분석 표 ---
st.header("📊 핵심 지표 비교")
def highlight_search(s):
    if search_ticker and s.Ticker == search_ticker:
        return ['background-color: #262730; font-weight: bold; color: #ff4b4b'] * len(s)
    return [''] * len(s)

st.dataframe(df_final.style.apply(highlight_search, axis=1), use_container_width=True, hide_index=True)

st.divider()

# --- 2. Finviz 상세 분석 섹션 ---
if search_ticker:
    st.header(f"🔍 {search_ticker} 상세 지표")
    
    col_chart, col_info = st.columns([1.8, 1])
    
    with col_chart:
        st.subheader("Monthly Chart")
        st.image(f"https://charts2.finviz.com/chart.ashx?t={search_ticker}&ty=c&ta=1&p=m", use_container_width=True)
        
    with col_info:
        st.subheader("Key Statistics")
        try:
            data = df_final[df_final['Ticker'] == search_ticker].iloc[0]
            st.markdown(f"""
            <div style="background-color: #161618; padding: 15px; border-radius: 8px; border: 1px solid #333; line-height: 2;">
                <table style="width: 100%; color: white;">
                    <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">Ticker</td><td style="text-align: right; font-weight: bold; color: #ff4b4b;">{data['Ticker']}</td></tr>
                    <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">시가총액</td><td style="text-align: right;">{data['시총 (Market Cap)']}</td></tr>
                    <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">전고점 대비 등락</td><td style="text-align: right; color: {'#ff4b4b' if '-' not in data['전고점 대비'] else '#0087ff'};">{data['전고점 대비']}</td></tr>
                    <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">P/E (Trailing)</td><td style="text-align: right;">{data['P/E']}</td></tr>
                    <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">PEG Ratio</td><td style="text-align: right;">{data['PEG']}</td></tr>
                    <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">Revenue Growth</td><td style="text-align: right;">{data['매출액 성장률']}</td></tr>
                    <tr><td style="color: #888;">EPS Next 5Y (Est.)</td><td style="text-align: right; color: #ffab00;">{data['EPS 전망 (5Y)']}</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            
            finviz_url = f"https://finviz.com/quote.ashx?t={search_ticker}"
            st.markdown(f'<br><a href="{finviz_url}" target="_blank"><button style="width: 100%; padding: 10px; background-color: #333; color: white; border: 1px solid #555; border-radius: 5px; cursor: pointer;">Finviz에서 상세 재무표 보기</button></a>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"데이터를 표시할 수 없습니다: {e}")
