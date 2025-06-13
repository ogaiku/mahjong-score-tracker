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

def initialize_session_and_load_data():
    """セッション状態の初期化とGoogle Sheetsからのデータ読み込み"""
    # セッション状態の初期化
    default_states = {
        'active_tab': 'ホーム',
        'show_data': False,
        'show_stats': False,
        'show_player_stats': False,
        'data_loaded': False
    }
    
    for key, default_value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    # Google Sheetsからのデータ読み込み（初回のみ）
    if not st.session_state.get('data_loaded', False):
        load_data_from_sheets()
        st.session_state['data_loaded'] = True

def load_data_from_sheets():
    """Google Sheetsからデータを読み込み"""
    from config_manager import ConfigManager
    from ui_components import load_season_data
    
    try:
        config_manager = ConfigManager()
        current_season = config_manager.get_current_season()
        
        # 現在のシーズンのデータを読み込み
        load_season_data(config_manager, current_season)
        
        # 読み込み結果を表示
        if 'game_records' in st.session_state and st.session_state['game_records']:
            record_count = len(st.session_state['game_records'])
            st.info(f"Google Sheetsから {record_count} 件の記録を読み込みました")
        else:
            st.info("Google Sheetsにデータがありません。新しい記録を追加してください。")
        
    except Exception as e:
        st.warning(f"データ読み込み中にエラーが発生: {e}")
        st.info("Google Sheets設定を確認してください")
        # ローカルデータを初期化
        if 'game_records' not in st.session_state:
            st.session_state['game_records'] = []

if __name__ == "__main__":
    main()