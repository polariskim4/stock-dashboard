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
    try: return f"{float(num):g}"
    except: return "N/A"

@st.cache_data(ttl=3600)
def get_stock_data(tickers):
    results = []
    for t in tickers:
        try:
            s = yf.Ticker(t)
            time.sleep(0.1)
            info = s.info
            raw_market_cap = info.get('marketCap', 0)
            
            results.append({
                "Ticker": t,
                "Market Cap (Raw)": raw_market_cap,
                "시총 (Market Cap)": format_display_number(raw_market_cap),
                "P/E": int(info.get('trailingPE')) if info.get('trailingPE') else "N/A",
                "PEG": clean_peg(info.get('pegRatio')),
                "매출액 성장률": f"{info.get('revenueGrowth', 0)*100:.1f}%" if info.get('revenueGrowth') else "N/A",
                "영업이익 성장률": f"{info.get('earningsGrowth', 0)*100:.1f}%" if info.get('earningsGrowth') else "N/A",
                "EPS 전망 (5Y)": f"{info.get('earningsQuarterlyGrowth', 0)*100:.1f}%" if info.get('earningsQuarterlyGrowth') else "N/A"
            })
        except:
            results.append({"Ticker": t, "Market Cap (Raw)": 0})
    
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values(by="Market Cap (Raw)", ascending=False).drop(columns=["Market Cap (Raw)"])
    return df

# --- 데이터 준비 ---
search_ticker = st.text_input("분석할 티커를 입력하세요:", value="ORCL").upper()

with st.spinner('데이터 로드 중...'):
    df_main = get_stock_data(DEFAULT_TICKERS)
    if search_ticker and search_ticker not in DEFAULT_TICKERS:
        df_search = get_stock_data([search_ticker])
        df_final = pd.concat([df_main, df_search], ignore_index=True)
    else:
        df_final = df_main

# --- 1. 종목 비교 분석 표 ---
st.header("📊 종목 비교 분석")
def highlight_search(s):
    if search_ticker and s.Ticker == search_ticker:
        return ['background-color: #262730; font-weight: bold; color: #ff4b4b'] * len(s)
    return [''] * len(s)

st.dataframe(df_final.style.apply(highlight_search, axis=1), use_container_width=True, hide_index=True)

st.divider()

# --- 2. Finviz 차트 및 상세 정보 섹션 ---
if search_ticker:
    st.header(f"🔍 {search_ticker} Finviz 상세 분석")
    
    # Finviz 웹사이트 바로가기 버튼 추가
    finviz_url = f"https://finviz.com/quote.ashx?t={search_ticker}"
    st.markdown(f'<a href="{finviz_url}" target="_blank"><button style="padding: 10px; background-color: #ff4b4b; color: white; border: none; border-radius: 5px; cursor: pointer;">Finviz에서 전체 재무표 보기</button></a>', unsafe_allow_html=True)
    
    col_chart, col_info = st.columns([1.8, 1])
    
    with col_chart:
        st.subheader("Monthly Chart")
        st.image(f"https://charts2.finviz.com/chart.ashx?t={search_ticker}&ty=c&ta=1&p=m", use_container_width=True)
        
    with col_info:
        st.subheader("Key Statistics")
        try:
            target_data = df_final[df_final['Ticker'] == search_ticker].iloc[0]
            st.markdown(f"""
            <div style="background-color: #161618; padding: 15px; border-radius: 5px; border: 1px solid #333;">
                <table style="width: 100%; color: white;">
                    <tr style="border-bottom: 1px solid #333;"><td style="color: #888; padding: 8px 0;">Ticker</td><td style="text-align: right; font-weight: bold;">{target_data['Ticker']}</td></tr>
                    <tr style="border-bottom: 1px solid #333;"><td style="color: #888; padding: 8px 0;">P/E</td><td style="text-align: right;">{target_data['P/E']}</td></tr>
                    <tr style="border-bottom: 1px solid #333;"><td style="color: #888; padding: 8px 0;">PEG</td><td style="text-align: right;">{target_data['PEG']}</td></tr>
                    <tr style="border-bottom: 1px solid #333;"><td style="color: #888; padding: 8px 0;">Rev Growth</td><td style="text-align: right; color: #00ff00;">{target_data['매출액 성장률']}</td></tr>
                    <tr style="border-bottom: 1px solid #333;"><td style="color: #888; padding: 8px 0;">EPS Growth (YoY)</td><td style="text-align: right; color: #00ff00;">{target_data['영업이익 성장률']}</td></tr>
                    <tr><td style="color: #888; padding: 8px 0;">EPS Next 5Y</td><td style="text-align: right; color: #ffab00;">{target_data['EPS 전망 (5Y)']}</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
        except:
            st.error("상세 데이터를 불러올 수 없습니다.")

    st.caption("차트 하단의 상세 재무 정보는 Finviz 웹사이트 버튼을 클릭하여 확인하실 수 있습니다.")
