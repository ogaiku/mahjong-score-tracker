# main.py - player_master管理完全対応版
import streamlit as st
from ui_components import setup_sidebar
from tab_pages import home_tab, screenshot_upload_tab, manual_input_tab, player_management_tab

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
    
    .sidebar .block-container {
        padding-top: 1rem;
    }
    
    .stSelectbox > div > div {
        border-radius: 0.375rem;
    }
    
    .stTextInput > div > div {
        border-radius: 0.375rem;
    }
    
    .stNumberInput > div > div {
        border-radius: 0.375rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("麻雀点数管理システム")
    
    # 設定とplayer_masterの同期初期化
    initialize_config_and_players()
    
    # サイドバー設定
    setup_sidebar()
    
    # セッション状態の初期化とデータ読み込み
    initialize_session_and_load_data()
    
    # メインコンテンツ - 4つのタブ
    tab1, tab2, tab3, tab4 = st.tabs(["ホーム", "スクショ解析", "手動入力", "プレイヤー管理"])
    
    with tab1:
        home_tab()
    
    with tab2:
        screenshot_upload_tab()
    
    with tab3:
        manual_input_tab()
    
    with tab4:
        player_management_tab()

def initialize_config_and_players():
    """設定とplayer_masterを初期化"""
    if 'config_initialized' not in st.session_state:
        from config_manager import ConfigManager
        
        try:
            # 設定スプレッドシートからの同期を強制実行
            config_manager = ConfigManager()
            
            # player_masterを先に読み込み
            load_master_players(config_manager)
            
            # 設定同期後、現在のシーズンのデータも読み込み
            current_season = config_manager.get_current_season()
            if current_season:
                from ui_components import load_season_data
                load_season_data(config_manager, current_season)
                
                # 同期時刻を設定
                import time
                st.session_state['last_sync_time'] = time.time()
                st.session_state['data_loaded'] = True
            
            status = config_manager.get_config_status()
            st.session_state['config_initialized'] = True
            
        except Exception as e:
            # エラーが発生してもアプリケーションを継続
            st.session_state['config_initialized'] = True
            # デフォルト値を設定
            if 'master_players' not in st.session_state:
                st.session_state['master_players'] = []
            if 'game_records' not in st.session_state:
                st.session_state['game_records'] = []

def load_master_players(config_manager=None):
    """player_masterを設定スプレッドシートから読み込み"""
    try:
        # 既にセッション状態にある場合は、強制リロードフラグをチェック
        if ('master_players' in st.session_state and 
            not st.session_state.get('force_reload_players', False)):
            return
        
        if config_manager is None:
            from config_manager import ConfigManager
            config_manager = ConfigManager()
        
        from config_spreadsheet_manager import ConfigSpreadsheetManager
        
        sheets_creds = config_manager.load_sheets_credentials()
        
        if not sheets_creds:
            st.session_state['master_players'] = []
            return
        
        config_sheet_manager = ConfigSpreadsheetManager(sheets_creds)
        if config_sheet_manager.connect():
            players = config_sheet_manager.get_all_players()
            st.session_state['master_players'] = players
            
            # リロードフラグをクリア
            if 'force_reload_players' in st.session_state:
                del st.session_state['force_reload_players']
        else:
            st.session_state['master_players'] = []
            
    except Exception as e:
        st.session_state['master_players'] = []

def force_reload_players():
    """player_masterの強制リロード"""
    st.session_state['force_reload_players'] = True
    load_master_players()

def initialize_session_and_load_data():
    """セッション状態の初期化とGoogle Sheetsからのデータ読み込み"""
    default_states = {
        'active_tab': 'ホーム',
        'show_data': False,
        'show_stats': False,
        'show_player_stats': False,
        'data_loaded': False,
        'last_sync_time': None,
        'auto_sync_enabled': True,
        'delete_mode_enabled': False,
        'season_management_state': {
            'new_season_name': '',
            'operation_in_progress': False,
            'last_operation': None
        }
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
            
            # 初回読み込み時は制限なし、2回目以降は5秒制限
            if last_sync == 0 or current_time - last_sync > 5:
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

def refresh_all_data():
    """全データの手動リフレッシュ"""
    try:
        # player_masterを強制リロード
        force_reload_players()
        
        # 対戦データを再読み込み
        from config_manager import ConfigManager
        from ui_components import load_season_data
        
        config_manager = ConfigManager()
        current_season = config_manager.get_current_season()
        
        if current_season:
            load_season_data(config_manager, current_season)
            
            # 同期時刻を更新
            import time
            st.session_state['last_sync_time'] = time.time()
            st.session_state['data_loaded'] = True
        
        st.success("全データを更新しました")
        
    except Exception as e:
        st.error(f"データ更新エラー: {e}")

def get_app_status():
    """アプリケーションの状態を取得"""
    from config_manager import ConfigManager
    
    try:
        config_manager = ConfigManager()
        config_status = config_manager.get_config_status()
        
        # player_masterの状態
        master_players_count = len(st.session_state.get('master_players', []))
        
        # 対戦記録の状態
        game_records_count = len(st.session_state.get('game_records', []))
        
        return {
            'config_initialized': st.session_state.get('config_initialized', False),
            'data_loaded': st.session_state.get('data_loaded', False),
            'current_season': config_status.get('current_season', ''),
            'seasons_count': config_status.get('season_count', 0),
            'master_players_count': master_players_count,
            'game_records_count': game_records_count,
            'sheets_connected': config_status.get('sheets_credentials', False),
            'spreadsheet_configured': config_status.get('spreadsheet_id', False),
            'last_sync_time': st.session_state.get('last_sync_time'),
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'config_initialized': False,
            'data_loaded': False
        }

def cleanup_session():
    """セッション状態のクリーンアップ"""
    # 一時的なフラグをクリア
    temporary_keys = [
        'delete_mode_enabled',
        'force_reload_players',
        'analysis_result',
        'screenshot_uploader_key'
    ]
    
    for key in temporary_keys:
        if key in st.session_state:
            del st.session_state[key]

def handle_app_error(error_message, error_type="general"):
    """アプリケーションエラーの統一処理"""
    error_messages = {
        "config": "設定の読み込みに失敗しました",
        "sheets": "Google Sheetsとの接続に失敗しました", 
        "players": "プレイヤーデータの読み込みに失敗しました",
        "data": "対戦データの読み込みに失敗しました",
        "general": "予期しないエラーが発生しました"
    }
    
    base_message = error_messages.get(error_type, error_messages["general"])
    
    st.error(f"{base_message}: {error_message}")
    
    # エラー詳細を展開可能な形で表示
    with st.expander("エラー詳細"):
        st.code(error_message)
        
        # アプリケーション状態の表示
        status = get_app_status()
        st.json(status)

# グローバルエラーハンドラー（デバッグ用）
def setup_error_handling():
    """エラーハンドリングの設定"""
    import sys
    import traceback
    
    def exception_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        # Streamlitアプリが実行中の場合のみエラー表示
        try:
            handle_app_error(error_msg, "general")
        except:
            # Streamlitコンテキスト外の場合は標準エラー出力
            print(f"Critical Error: {error_msg}")
    
    sys.excepthook = exception_handler

if __name__ == "__main__":
    # エラーハンドリングを設定（開発時のみ）
    # setup_error_handling()
    
    try:
        main()
    except Exception as e:
        handle_app_error(str(e), "general")
        
        # アプリケーションの継続を試行
        st.warning("エラーが発生しましたが、アプリケーションを継続します")
        
        # 基本的な状態を初期化
        if 'master_players' not in st.session_state:
            st.session_state['master_players'] = []
        if 'game_records' not in st.session_state:
            st.session_state['game_records'] = []