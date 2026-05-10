import streamlit as st
import yfinance as yf
import pandas as pd
import time

# 페이지 설정 (전체 화면 활용 및 제목 설정)
st.set_page_config(page_title="Advanced Stock Dashboard", layout="wide")

# CSS를 이용해 스크롤바 제거 및 테이블 가독성 향상
st.markdown("""
    <style>
    .main .block-container { max-width: 100%; }
    div[data-testid="stDataFrame"] > div { height: auto !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 주식 벤치마크 및 상세 분석 대시보드")

# 벤치마크 대상 목록
DEFAULT_TICKERS = [
    'AAPL', 'MSFT', 'GOOG', 'AMZN', 'TSLA', 'NVDA', 'MU', 'PLTR', 'IREN', 'IONQ',
    'ANET', 'MRVL', 'VRT', 'VST'
]

def format_display_number(num):
    if pd.isna(num) or num == 0 or num is None: return "N/A"
    return f"${num / 1_000_000_000:,.1f}B"

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
                "P/E": int(info.get('trailingPE')) if info.get('trailingPE') else "N/A", # 소수점 제거
                "PEG": round(info.get('pegRatio', 0), 1) if info.get('pegRatio') else "N/A", # 소수점 한자리
                "매출액 (Revenue)": format_display_number(info.get('totalRevenue')),
                "영업이익 (Op Income)": format_display_number(info.get('operatingIncome', info.get('ebitda'))),
                "마진 (Margin)": f"{info.get('operatingMargins', 0)*100:.1f}%" if info.get('operatingMargins') else "N/A",
                "매출액 성장률": f"{info.get('revenueGrowth', 0)*100:.1f}%" if info.get('revenueGrowth') else "N/A",
                "영업이익 성장률": f"{info.get('earningsGrowth', 0)*100:.1f}%" if info.get('earningsGrowth') else "N/A"
            })
        except:
            results.append({"Ticker": t, "Market Cap (Raw)": 0, "Ticker": t})
    
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values(by="Market Cap (Raw)", ascending=False).drop(columns=["Market Cap (Raw)"])
    return df

# --- 데이터 준비 및 테이블 출력 ---
st.header("📊 종목 비교 분석")
search_ticker = st.text_input("분석할 티커를 입력하세요:", value="ORCL").upper()

with st.spinner('데이터를 불러오는 중입니다...'):
    df_main = get_stock_data(DEFAULT_TICKERS)
    if search_ticker and search_ticker not in DEFAULT_TICKERS:
        df_search = get_stock_data([search_ticker])
        df_final = pd.concat([df_main, df_search], ignore_index=True)
    else:
        df_final = df_main

# 강조 스타일 정의
def highlight_search(s):
    if search_ticker and s.Ticker == search_ticker:
        return ['background-color: #262730; font-weight: bold; border: 1px solid #ff4b4b'] * len(s)
    return [''] * len(s)

# st.dataframe의 height=None 설정을 통해 스크롤바 없이 전체 행 표시
st.dataframe(
    df_final.style.apply(highlight_search, axis=1),
    use_container_width=True,
    hide_index=True,
    height=None 
)

st.divider()

# --- 4. Finviz 차트 및 상세 지표 섹션 ---
if search_ticker:
    st.header(f"🔍 {search_ticker} 상세 분석 현황")
    
    col_chart, col_info = st.columns([1.8, 1])
    
    with col_chart:
        st.subheader("Monthly Chart (Finviz)")
        chart_url = f"https://charts2.finviz.com/chart.ashx?t={search_ticker}&ty=c&ta=1&p=m"
        st.markdown(f'<img src="{chart_url}" style="width:100%; border-radius: 5px;">', unsafe_allow_html=True)
        
    with col_info:
        st.subheader("Key Statistics")
        # 해당 종목의 데이터를 표 형태로 예쁘게 출력
        target_data = df_final[df_final['Ticker'] == search_ticker].iloc[0]
        
        # Finviz 느낌의 재무제표 레이아웃을 HTML로 직접 구현
        html_table = f"""
        <div style="background-color: #161618; padding: 20px; border-radius: 5px; border: 1px solid #333;">
            <table style="width: 100%; color: white; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #333;"><td style="padding: 10px; color: #888;">Ticker</td><td style="text-align: right; font-weight: bold;">{target_data['Ticker']}</td></tr>
                <tr style="border-bottom: 1px solid #333;"><td style="padding: 10px; color: #888;">Market Cap</td><td style="text-align: right;">{target_data['시총 (Market Cap)']}</td></tr>
                <tr style="border-bottom: 1px solid #333;"><td style="padding: 10px; color: #888;">P/E</td><td style="text-align: right;">{target_data['P/E']}</td></tr>
                <tr style="border-bottom: 1px solid #333;"><td style="padding: 10px; color: #888;">PEG</td><td style="text-align: right;">{target_data['PEG']}</td></tr>
                <tr style="border-bottom: 1px solid #333;"><td style="padding: 10px; color: #888;">Revenue</td><td style="text-align: right;">{target_data['매출액 (Revenue)']}</td></tr>
                <tr style="border-bottom: 1px solid #333;"><td style="padding: 10px; color: #888;">Op Income</td><td style="text-align: right;">{target_data['영업이익 (Op Income)']}</td></tr>
                <tr style="border-bottom: 1px solid #333;"><td style="padding: 10px; color: #888;">Margin</td><td style="text-align: right; color: #00ff00;">{target_data['마진 (Margin)']}</td></tr>
                <tr style="border-bottom: 1px solid #333;"><td style="padding: 10px; color: #888;">Rev Growth</td><td style="text-align: right; color: #00ff00;">{target_data['매출액 성장률']}</td></tr>
                <tr><td style="padding: 10px; color: #888;">EPS Growth</td><td style="text-align: right; color: #00ff00;">{target_data['영업이익 성장률']}</td></tr>
            </table>
        </div>
        """
        st.markdown(html_table, unsafe_allow_html=True)

    st.caption("Data source: Yahoo Finance & Finviz.com")
