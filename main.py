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
    
    # 設定スプレッドシートとの同期を最初に実行
    initialize_config_with_spreadsheet_sync()
    
    # サイドバー設定
    setup_sidebar()
    
    # セッション状態の初期化とデータ読み込み
    initialize_session_and_load_data()
    
    # メインコンテンツ - 3つのタブ
    tab1, tab2, tab3 = st.tabs(["ホーム", "スクショ解析", "手動入力"])
    
    with tab1:
        home_tab()
    
    with tab2:
        screenshot_upload_tab()
    
    with tab3:
        manual_input_tab()

def initialize_config_with_spreadsheet_sync():
    """設定スプレッドシートと同期して設定を初期化"""
    if 'config_initialized' not in st.session_state:
        from config_manager import ConfigManager
        
        try:
            config_manager = ConfigManager()
            status = config_manager.get_config_status()
            st.session_state['config_initialized'] = True
            
        except Exception as e:
            st.session_state['config_initialized'] = True

def initialize_session_and_load_data():
    """セッション状態の初期化とGoogle Sheetsからのデータ読み込み"""
    default_states = {
        'active_tab': 'ホーム',
        'show_data': False,
        'show_stats': False,
        'show_player_stats': False,
        'data_loaded': False,
        'last_sync_time': None,
        'auto_sync_enabled': True
    }
    
    for key, default_value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    load_data_from_sheets_with_config_sync()

def load_data_from_sheets_with_config_sync():
    """設定スプレッドシート同期後にGoogle Sheetsからデータを読み込み"""
    from config_manager import ConfigManager
    from ui_components import load_season_data
    import time
    
    try:
        config_manager = ConfigManager()
        current_season = config_manager.get_current_season()
        
        if current_season:
            current_time = time.time()
            last_sync = st.session_state.get('last_sync_time', 0)
            
            if current_time - last_sync > 5:
                try:
                    load_season_data(config_manager, current_season)
                    st.session_state['last_sync_time'] = current_time
                    st.session_state['data_loaded'] = True
                except Exception as e:
                    if 'game_records' not in st.session_state:
                        st.session_state['game_records'] = []
        else:
            if 'game_records' not in st.session_state:
                st.session_state['game_records'] = []
        
    except Exception as e:
        if 'game_records' not in st.session_state:
            st.session_state['game_records'] = []

if __name__ == "__main__":
    main()