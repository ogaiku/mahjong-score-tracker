# main.py
import streamlit as st
from ui_components import setup_sidebar
from tab_pages import home_tab, screenshot_upload_tab, manual_input_tab

# ページ設定
st.set_page_config(
    page_title="麻雀点数管理システム",
    page_icon="🀄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# シンプルなCSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    h1, h2, h3 {
        color: #1f2937;
        font-weight: 600;
    }
    
    [data-testid="metric-container"] {
        background-color: #f8fafc;
        border: 1px solid #e5e7eb;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button {
        border-radius: 0.375rem;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stDataFrame {
        border-radius: 0.5rem;
        overflow: hidden;
    }
    
    .stForm {
        background-color: #f9fafb;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e5e7eb;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        padding: 0 1.5rem;
        background-color: transparent;
        border-radius: 0.375rem;
        font-weight: 500;
    }
    
    .stAlert {
        border-radius: 0.5rem;
        border-left: 4px solid;
    }
    
    .stSuccess {
        border-left-color: #10b981;
        background-color: #f0fdf4;
    }
    
    .stWarning {
        border-left-color: #f59e0b;
        background-color: #fffbeb;
    }
    
    .stInfo {
        border-left-color: #3b82f6;
        background-color: #eff6ff;
    }
    
    .stError {
        border-left-color: #ef4444;
        background-color: #fef2f2;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("麻雀点数管理システム")
    
    # サイドバー設定
    setup_sidebar()
    
    # セッション状態の初期化
    if 'active_tab' not in st.session_state:
        st.session_state['active_tab'] = 'ホーム'
    
    if 'show_data' not in st.session_state:
        st.session_state['show_data'] = False
    
    if 'show_stats' not in st.session_state:
        st.session_state['show_stats'] = False
    
    if 'show_player_stats' not in st.session_state:
        st.session_state['show_player_stats'] = False
    
    # メインコンテンツ - 3つのタブ
    tab1, tab2, tab3 = st.tabs(["ホーム", "スクショ解析", "手動入力"])
    
    with tab1:
        home_tab()
    
    with tab2:
        screenshot_upload_tab()
    
    with tab3:
        manual_input_tab()

if __name__ == "__main__":
    main()