import streamlit as st
import yfinance as yf
import pandas as pd
import time

# 페이지 설정
st.set_page_config(page_title="Advanced Stock Dashboard", layout="wide")

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
    """PEG 소수점 둘째자리 이하 0 제거 (1.200000 -> 1.2)"""
    if pd.isna(num) or num == "N/A" or num is None: return "N/A"
    try:
        val = float(num)
        return f"{val:g}" # g 포맷팅은 불필요한 0을 자동으로 제거함
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
            
            results.append({
                "Ticker": t,
                "Market Cap (Raw)": raw_market_cap,
                "시총 (Market Cap)": format_display_number(raw_market_cap),
                "P/E": int(info.get('trailingPE')) if info.get('trailingPE') else "N/A",
                "PEG": clean_peg(info.get('pegRatio')), # 소수점 0 제거 반영
                "매출액 (Revenue)": format_display_number(info.get('totalRevenue')),
                "영업이익 (Op Income)": format_display_number(info.get('operatingIncome', info.get('ebitda'))),
                "마진 (Margin)": f"{info.get('operatingMargins', 0)*100:.1f}%" if info.get('operatingMargins') else "N/A",
                "매출액 성장률": f"{info.get('revenueGrowth', 0)*100:.1f}%" if info.get('revenueGrowth') else "N/A",
                "영업이익 성장률": f"{info.get('earningsGrowth', 0)*100:.1f}%" if info.get('earningsGrowth') else "N/A",
                # 전망 데이터 추가
                "EPS 전망 (5Y)": f"{info.get('earningsQuarterlyGrowth', 0)*100:.1f}%" if info.get('earningsQuarterlyGrowth') else "N/A",
                "수익 전망 (Next Year)": f"{info.get('revenueQuarterlyGrowth', 0)*100:.1f}%" if info.get('revenueQuarterlyGrowth') else "N/A"
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

st.dataframe(
    df_final.style.apply(highlight_search, axis=1),
    use_container_width=True,
    hide_index=True
)

st.divider()

# --- 2. Finviz 차트 및 상세 분석 (Key Statistics 확장) ---
if search_ticker:
    st.header(f"🔍 {search_ticker} 상세 분석")
    
    col_chart, col_info = st.columns([1.8, 1])
    
    with col_chart:
        st.subheader("Monthly Chart (Finviz)")
        chart_url = f"https://charts2.finviz.com/chart.ashx?t={search_ticker}&ty=c&ta=1&p=m"
        st.image(chart_url, use_container_width=True)
        
    with col_info:
        st.subheader("Key Statistics (Detailed)")
        try:
            target_data = df_final[df_final['Ticker'] == search_ticker].iloc[0]
            
            # HTML 테이블을 이용해 요청하신 항목(영업이익 성장률, 전망치) 추가 반영
            st.markdown(f"""
            <div style="background-color: #161618; padding: 15px; border-radius: 5px; border: 1px solid #333; line-height: 1.6;">
                <table style="width: 100%; color: white;">
                    <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">Ticker</td><td style="text-align: right; font-weight: bold;">{target_data['Ticker']}</td></tr>
                    <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">Market Cap</td><td style="text-align: right;">{target_data['시총 (Market Cap)']}</td></tr>
                    <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">P/E | PEG</td><td style="text-align: right;">{target_data['P/E']} | {target_data['PEG']}</td></tr>
                    <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">Revenue</td><td style="text-align: right;">{target_data['매출액 (Revenue)']}</td></tr>
                    <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">Operating Margin</td><td style="text-align: right; color: #00ff00;">{target_data['마진 (Margin)']}</td></tr>
                    <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">Revenue Growth (YoY)</td><td style="text-align: right; color: #00ff00;">{target_data['매출액 성장률']}</td></tr>
                    <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">Earnings Growth (YoY)</td><td style="text-align: right; color: #00ff00;">{target_data['영업이익 성장률']}</td></tr>
                    <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">Revenue Est. (Next Q)</td><td style="text-align: right; color: #ffab00;">{target_data['수익 전망 (Next Year)']}</td></tr>
                    <tr><td style="color: #888;">EPS Est. (5Y Target)</td><td style="text-align: right; color: #ffab00;">{target_data['EPS 전망 (5Y)']}</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"데이터 표시 중 오류 발생: {e}")

    st.caption("Data source: Yahoo Finance (yfinance) & Finviz.com")
