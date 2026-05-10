import streamlit as st
import yfinance as yf
import pandas as pd
import time

# 페이지 설정
st.set_page_config(page_title="Advanced Stock Dashboard", layout="wide")

st.title("📈 주식 벤치마크 및 상세 분석 대시보드")

# 벤치마크 대상 목록 (요청하신 티커 추가)
DEFAULT_TICKERS = [
    'AAPL', 'MSFT', 'GOOG', 'AMZN', 'TSLA', 'NVDA', 'MU', 'PLTR', 'IREN', 'IONQ',
    'ANET', 'MRVL', 'VRT', 'VST'
]

def format_large_number(num):
    if pd.isna(num) or num is None: return 0
    return num

def format_display_number(num):
    if num == 0 or pd.isna(num): return "N/A"
    return f"${num / 1_000_000_000:,.2f}B"

def format_percent(num):
    if pd.isna(num) or num is None: return "N/A"
    return f"{num * 100:.2f}%"

@st.cache_data(ttl=3600)
def get_stock_data(tickers):
    results = []
    for t in tickers:
        try:
            s = yf.Ticker(t)
            time.sleep(0.1) # 속도 향상을 위해 딜레이 축소
            info = s.info
            
            # 정렬을 위해 원본 숫자 데이터를 보관
            raw_market_cap = format_large_number(info.get('marketCap'))
            
            results.append({
                "Ticker": t,
                "Market Cap (Raw)": raw_market_cap, # 숨김 처리용
                "시총 (Market Cap)": format_display_number(raw_market_cap),
                "P/E": round(info.get('trailingPE', 0), 2) if info.get('trailingPE') else "N/A",
                "PEG": info.get('pegRatio', 'N/A'),
                "매출액 (Revenue)": format_display_number(info.get('totalRevenue')),
                "영업이익 (Op Income)": format_display_number(info.get('operatingIncome', info.get('ebitda'))),
                "마진 (Margin)": format_percent(info.get('operatingMargins')),
                "매출액 성장률": format_percent(info.get('revenueGrowth')),
                "영업이익 성장률": format_percent(info.get('earningsGrowth'))
            })
        except:
            results.append({"Ticker": t, "Market Cap (Raw)": 0, "시총 (Market Cap)": "Error"})
    
    df = pd.DataFrame(results)
    # 1. 시총 순서대로 정렬 (내림차순)
    if not df.empty:
        df = df.sort_values(by="Market Cap (Raw)", ascending=False).drop(columns=["Market Cap (Raw)"])
    return df

# --- 데이터 준비 ---
st.header("📊 종목 비교 분석 (시총 순 정렬)")

search_ticker = st.text_input("분석할 티커를 입력하세요:", value="ORCL").upper()

with st.spinner('데이터를 불러오는 중입니다...'):
    # 벤치마크 데이터 가져오기
    df_main = get_stock_data(DEFAULT_TICKERS)
    
    if search_ticker and search_ticker not in DEFAULT_TICKERS:
        # 검색한 종목이 벤치마크에 없으면 추가 데이터 호출
        df_search = get_stock_data([search_ticker])
        # 3. 검색 종목을 맨 아래에 합치기
        df_final = pd.concat([df_main, df_search], ignore_index=True)
    else:
        df_final = df_main

# --- 표 렌더링 ---
# 스타일링: 마지막 행(검색 종목)에 음영 및 굵게 표시
def highlight_last_row(s):
    if search_ticker and s.Ticker == search_ticker:
        return ['background-color: #262730; font-weight: bold; color: #ff4b4b'] * len(s)
    return [''] * len(s)

st.dataframe(
    df_final.style.apply(highlight_last_row, axis=1),
    use_container_width=True,
    hide_index=True
)

st.divider()

# --- 4. Finviz 차트 및 재무정보 섹션 ---
if search_ticker:
    st.header(f"📈 {search_ticker} Finviz 상세 분석")
    
    # Finviz 기술적 분석 차트 (Monthly)
    chart_url = f"https://charts2.finviz.com/chart.ashx?t={search_ticker}&ty=c&ta=1&p=m"
    
    # Finviz 재무 정보 표 (자동 생성되는 스냅샷 이미지)
    # s=l 파라미터는 상세 재무 수치 표 이미지를 불러옵니다.
    stat_url = f"https://charts2.finviz.com/chart.ashx?t={search_ticker}&ty=c&ta=1&p=m&s=l"

    col_chart, col_stat = st.columns([2, 1])
    
    with col_chart:
        st.subheader("Monthly 기술적 분석 차트")
        st.markdown(f'<img src="{chart_url}" style="width:100%;">', unsafe_allow_html=True)
        
    with col_stat:
        st.subheader("상세 재무 지표 (Snapshot)")
        # Finviz 특유의 하단 재무 표 레이아웃 이미지
        st.markdown(f'<img src="{stat_url}" style="width:100%; border: 1px solid #444;">', unsafe_allow_html=True)

    st.caption(f"제공: Finviz.com - {search_ticker} 분석 자료")
