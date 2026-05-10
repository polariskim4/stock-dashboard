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
    if pd.isna(num) or num is None: return "N/A"
    try:
        return f"{float(num):g}"
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
            
            # 현재가와 목표가 대비 상승 여력 계산
            current_price = info.get('currentPrice', 1)
            target_price = info.get('targetMedianPrice')
            upside = f"{(target_price/current_price - 1)*100:.1f}%" if target_price else "N/A"

            results.append({
                "Ticker": t,
                "Market Cap (Raw)": raw_market_cap,
                "시총 (Market Cap)": format_display_number(raw_market_cap),
                "P/E": int(info.get('trailingPE')) if info.get('trailingPE') else "N/A",
                "Forward P/E": round(info.get('forwardPE', 0), 1) if info.get('forwardPE') else "N/A",
                "PEG": clean_peg(info.get('pegRatio')),
                "매출액 성장률": f"{info.get('revenueGrowth', 0)*100:.1f}%" if info.get('revenueGrowth') else "N/A",
                "이익 성장률(YoY)": f"{info.get('earningsGrowth', 0)*100:.1f}%" if info.get('earningsGrowth') else "N/A",
                # 대체된 실질적 전망 지표
                "내년 매출 성장 전망": f"{info.get('revenueQuarterlyGrowth', 0)*100:.1f}%" if info.get('revenueQuarterlyGrowth') else "N/A",
                "애널리스트 목표가 대비": upside
            })
        except:
            results.append({"Ticker": t, "Market Cap (Raw)": 0})
    
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values(by="Market Cap (Raw)", ascending=False).drop(columns=["Market Cap (Raw)"])
    return df

# --- 데이터 로드 및 검색 ---
search_ticker = st.text_input("분석할 티커를 입력하세요:", value="ORCL").upper()
with st.spinner('실시간 분석 데이터를 가져오는 중...'):
    df_main = get_stock_data(DEFAULT_TICKERS)
    df_final = pd.concat([df_main, get_stock_data([search_ticker])], ignore_index=True) if search_ticker not in DEFAULT_TICKERS else df_main

# --- 1. 비교 분석 표 ---
st.header("📊 핵심 지표 비교")
def highlight_search(s):
    return ['background-color: #262730; font-weight: bold; color: #ff4b4b'] * len(s) if s.Ticker == search_ticker else [''] * len(s)

st.dataframe(df_final.style.apply(highlight_search, axis=1), use_container_width=True, hide_index=True)

st.divider()

# --- 2. 상세 분석 (Key Statistics) ---
if search_ticker:
    st.header(f"🔍 {search_ticker} 향후 전망 및 분석")
    col_chart, col_info = st.columns([1.8, 1])
    
    with col_chart:
        st.subheader("Monthly Chart (Finviz)")
        st.image(f"https://charts2.finviz.com/chart.ashx?t={search_ticker}&ty=c&ta=1&p=m", use_column_width=True)
        
    with col_info:
        st.subheader("Future Guidance")
        data = df_final[df_final['Ticker'] == search_ticker].iloc[0]
        st.markdown(f"""
        <div style="background-color: #161618; padding: 15px; border-radius: 5px; border: 1px solid #333; line-height: 1.8;">
            <table style="width: 100%; color: white;">
                <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">Ticker</td><td style="text-align: right; font-weight: bold;">{data['Ticker']}</td></tr>
                <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">Forward P/E (내년 예상)</td><td style="text-align: right; color: #ffab00;">{data['Forward P/E']}</td></tr>
                <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">PEG Ratio (성장성 대비 저평가)</td><td style="text-align: right;">{data['PEG']}</td></tr>
                <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">Revenue Growth (최근)</td><td style="text-align: right;">{data['매출액 성장률']}</td></tr>
                <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">Earnings Growth (최근)</td><td style="text-align: right;">{data['이익 성장률(YoY)']}</td></tr>
                <tr style="border-bottom: 1px solid #333;"><td style="color: #888;">Revenue Growth Est. (다음 분기)</td><td style="text-align: right; color: #00ff00;">{data['내년 매출 성장 전망']}</td></tr>
                <tr><td style="color: #888;">Target Price Upside (목표가 대비)</td><td style="text-align: right; color: #00ff00;">{data['애널리스트 목표가 대비']}</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        st.info("💡 **Forward P/E**가 현재 P/E보다 낮으면 내년 이익이 늘어날 것으로 시장이 예상한다는 뜻입니다.")
