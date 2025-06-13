# ui_components.py - 基本UI部品とサイドバー管理
import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
from datetime import datetime, date
from score_extractor import MahjongScoreExtractor
from spreadsheet_manager import SpreadsheetManager
from config_manager import ConfigManager

def setup_sidebar():
    """サイドバーの設定"""
    st.sidebar.title("設定")
    
    config_manager = ConfigManager()
    display_config_status(config_manager)
    
    st.sidebar.divider()
    
    # データ管理セクション
    st.sidebar.subheader("データ管理")
    
    # データ同期ボタン
    if st.sidebar.button("データ同期", use_container_width=True, help="Google Sheetsからデータを読み込み"):
        sync_data_from_sheets(config_manager)
    
    # データ表示・統計ボタン
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("データ表示", use_container_width=True, key="sidebar_data_btn"):
            st.session_state['show_data'] = True
    
    with col2:
        if st.button("統計表示", use_container_width=True, key="sidebar_stats_btn"):
            st.session_state['show_stats'] = True
    
    # 記録数とダウンロード
    if 'game_records' in st.session_state and st.session_state['game_records']:
        record_count = len(st.session_state['game_records'])
        st.sidebar.metric("読み込み済み記録", f"{record_count}件")
        
        # Google Sheets連携状況
        sheets_status = check_sheets_sync_status(config_manager)
        if sheets_status['configured']:
            if sheets_status['can_connect']:
                st.sidebar.success("Google Sheets: 接続OK")
            else:
                st.sidebar.error("Google Sheets: 接続エラー")
        else:
            st.sidebar.warning("Google Sheets: 未設定")
        
        df = pd.DataFrame(st.session_state['game_records'])
        csv_data = df.to_csv(index=False, encoding='utf-8-sig')
        st.sidebar.download_button(
            label="CSV出力",
            data=csv_data,
            file_name=f"mahjong_records_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.sidebar.info("記録なし - データ同期を実行してください")

def display_config_status(config_manager: ConfigManager):
    """設定状況を表示"""
    st.sidebar.subheader("Google Sheets設定")
    
    status = config_manager.get_config_status()
    
    has_sheets_auth = status['sheets_credentials']
    has_seasons = status['season_count'] > 0
    has_current_season_id = status['spreadsheet_id']
    
    if has_sheets_auth and has_seasons and has_current_season_id:
        current_season = status['current_season']
        season_count = status['season_count']
        st.sidebar.success(f"現在のシーズン: {current_season}")
        st.sidebar.caption(f"登録済みシーズン: {season_count}個")
        
        # シーズン選択
        seasons = status['seasons']
        if len(seasons) > 1:
            season_options = {key: info.get('name', key) for key, info in seasons.items()}
            
            if 'current_season_key' not in st.session_state:
                st.session_state['current_season_key'] = current_season
            
            selected_season = st.sidebar.selectbox(
                "シーズン切り替え",
                options=list(season_options.keys()),
                format_func=lambda x: season_options[x],
                index=list(season_options.keys()).index(st.session_state['current_season_key']) if st.session_state['current_season_key'] in season_options else 0,
                key="season_selector"
            )
            
            if selected_season != st.session_state['current_season_key']:
                if switch_season(config_manager, selected_season):
                    st.session_state['current_season_key'] = selected_season
                    load_season_data(config_manager, selected_season)
                    st.sidebar.success(f"シーズン {selected_season} に切り替え")
                    st.rerun()
    else:
        st.sidebar.error("Google Sheets未設定")
    
    # シーズン管理
    with st.sidebar.expander("シーズン管理"):
        if not has_sheets_auth:
            st.warning("Google Sheets認証が必要")
        
        # 新シーズン追加
        with st.form("add_season_form"):
            season_name = st.text_input("シーズン名", placeholder="例: season2024")
            
            if season_name:
                spreadsheet_name = f"mahjong-score-tracker-{season_name}"
                st.caption(f"作成名: {spreadsheet_name}")
            
            if st.form_submit_button("シーズン追加", use_container_width=True):
                if season_name and has_sheets_auth:
                    if create_new_season(config_manager, season_name):
                        st.success(f"シーズン {season_name} を作成")
                        st.rerun()
                else:
                    st.error("シーズン名を入力してください")
        
        # 既存シーズン管理
        if has_seasons:
            seasons = status['seasons']
            for key, info in seasons.items():
                is_current = (key == status['current_season'])
                marker = " (現在)" if is_current else ""
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.caption(f"{key}{marker}")
                with col2:
                    if not is_current and st.button("選択", key=f"select_{key}"):
                        if switch_season(config_manager, key):
                            st.session_state['current_season_key'] = key
                            load_season_data(config_manager, key)
                            st.rerun()
                with col3:
                    if not is_current and st.button("削除", key=f"delete_{key}"):
                        if config_manager.delete_season(key):
                            st.success(f"シーズン {key} を削除")
                            st.rerun()

def create_new_season(config_manager: ConfigManager, season_name: str) -> bool:
    """新しいシーズンを作成"""
    try:
        spreadsheet_name = f"mahjong-score-tracker-{season_name}"
        
        if config_manager.add_season(season_name, spreadsheet_name, auto_create=True):
            if config_manager.set_current_season(season_name):
                initialize_new_season_data()
                return True
        return False
    except Exception as e:
        st.error(f"シーズン作成エラー: {e}")
        return False

def switch_season(config_manager: ConfigManager, season_key: str) -> bool:
    """シーズンを切り替え"""
    try:
        return config_manager.set_current_season(season_key)
    except Exception as e:
        st.error(f"シーズン切り替えエラー: {e}")
        return False

def load_season_data(config_manager: ConfigManager, season_key: str):
    """シーズンデータを読み込み"""
    try:
        if 'game_records' in st.session_state:
            del st.session_state['game_records']
        
        sheets_creds = config_manager.load_sheets_credentials()
        spreadsheet_id = config_manager.get_spreadsheet_id()
        
        if sheets_creds and spreadsheet_id:
            try:
                sheet_manager = SpreadsheetManager(sheets_creds)
                if sheet_manager.connect(spreadsheet_id):
                    records = sheet_manager.get_all_records()
                    if records:
                        converted_records = convert_sheets_records(records)
                        st.session_state['game_records'] = converted_records
            except Exception as e:
                st.warning(f"データ読み込み失敗: {e}")
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")

def initialize_new_season_data():
    """新シーズンのデータを初期化"""
    if 'game_records' in st.session_state:
        del st.session_state['game_records']

def sync_data_from_sheets(config_manager: ConfigManager):
    """Google Sheetsからデータを手動同期"""
    try:
        current_season = config_manager.get_current_season()
        
        with st.sidebar:
            with st.spinner("データを同期中..."):
                load_season_data(config_manager, current_season)
                
                if 'game_records' in st.session_state and st.session_state['game_records']:
                    record_count = len(st.session_state['game_records'])
                    st.success(f"{record_count}件の記録を同期しました")
                else:
                    st.info("同期するデータがありませんでした")
                
    except Exception as e:
        st.sidebar.error(f"同期エラー: {e}")

def check_sheets_sync_status(config_manager: ConfigManager) -> dict:
    """Google Sheets同期状況をチェック"""
    try:
        sheets_creds = config_manager.load_sheets_credentials()
        spreadsheet_id = config_manager.get_spreadsheet_id()
        
        if not sheets_creds or not spreadsheet_id:
            return {'configured': False, 'can_connect': False}
        
        # 接続テスト
        sheet_manager = SpreadsheetManager(sheets_creds)
        can_connect = sheet_manager.connect(spreadsheet_id)
        
        return {'configured': True, 'can_connect': can_connect}
        
    except Exception:
        return {'configured': True, 'can_connect': False}

def convert_sheets_records(sheets_records: list) -> list:
    """Google Sheetsの記録をアプリ形式に変換"""
    converted = []
    for record in sheets_records:
        converted_record = {
            'date': record.get('対局日', ''),
            'time': record.get('対局時刻', ''),
            'game_type': record.get('対局タイプ', ''),
            'player1_name': record.get('プレイヤー1名', ''),
            'player1_score': record.get('プレイヤー1点数', 0),
            'player2_name': record.get('プレイヤー2名', ''),
            'player2_score': record.get('プレイヤー2点数', 0),
            'player3_name': record.get('プレイヤー3名', ''),
            'player3_score': record.get('プレイヤー3点数', 0),
            'player4_name': record.get('プレイヤー4名', ''),
            'player4_score': record.get('プレイヤー4点数', 0),
            'notes': record.get('メモ', ''),
            'timestamp': record.get('登録日時', '')
        }
        converted.append(converted_record)
    return converted
    """Google Sheetsの記録をアプリ形式に変換"""
    converted = []
    for record in sheets_records:
        converted_record = {
            'date': record.get('対局日', ''),
            'time': record.get('対局時刻', ''),
            'game_type': record.get('対局タイプ', ''),
            'player1_name': record.get('プレイヤー1名', ''),
            'player1_score': record.get('プレイヤー1点数', 0),
            'player2_name': record.get('プレイヤー2名', ''),
            'player2_score': record.get('プレイヤー2点数', 0),
            'player3_name': record.get('プレイヤー3名', ''),
            'player3_score': record.get('プレイヤー3点数', 0),
            'player4_name': record.get('プレイヤー4名', ''),
            'player4_score': record.get('プレイヤー4点数', 0),
            'notes': record.get('メモ', ''),
            'timestamp': record.get('登録日時', '')
        }
        converted.append(converted_record)
    return converted

def extract_data_from_image(image):
    """画像からデータを抽出"""
    config_manager = ConfigManager()
    
    openai_key = config_manager.get_openai_api_key()
    vision_creds = config_manager.load_vision_credentials()
    
    if not openai_key or openai_key == "your-openai-api-key-here":
        st.error("OpenAI API Keyが正しく設定されていません")
        st.markdown("""
        **設定方法:**
        1. [OpenAI API Keys](https://platform.openai.com/account/api-keys)にアクセス
        2. 新しいAPIキーを作成
        3. config.jsonの`openai.api_key`を更新
        """)
        return
    
    if not vision_creds:
        st.error("Google Vision APIの認証情報が設定されていません")
        return
    
    with st.spinner("AI解析中..."):
        try:
            extractor = MahjongScoreExtractor(
                vision_credentials=vision_creds,
                openai_api_key=openai_key
            )
            
            image_array = np.array(image)
            result = extractor.analyze_image(image_array)
            
            st.session_state['analysis_result'] = result
            
        except Exception as e:
            error_message = str(e)
            
            if "401" in error_message or "invalid_api_key" in error_message:
                st.error("OpenAI APIキーが無効です")
            elif "quota" in error_message.lower():
                st.error("OpenAI APIの利用制限に達しています")
            else:
                st.error(f"解析エラー: {error_message}")
            
            st.session_state['analysis_result'] = {
                'success': False,
                'message': f'エラー: {error_message}',
                'players': [
                    {'nickname': '', 'score': 25000},
                    {'nickname': '', 'score': 25000},
                    {'nickname': '', 'score': 25000},
                    {'nickname': '', 'score': 25000}
                ],
                'extracted_text': '',
                'confidence': 0.0
            }

def display_extraction_results():
    """解析結果の表示"""
    # analysis_resultがNoneまたは存在しない場合は何も表示しない
    if 'analysis_result' not in st.session_state or st.session_state['analysis_result'] is None:
        return
    
    result = st.session_state['analysis_result']
    
    if not result.get('success', False):
        st.error(result.get('message', '解析に失敗しました'))
        return
    
    st.success("解析完了")
    
    players = result.get('players', [])
    
    if any(player.get('nickname', '').strip() for player in players):
        st.subheader("抽出されたプレイヤー情報")
        
        player_data = []
        for i, player in enumerate(players):
            nickname = player.get('nickname', '')
            score = player.get('score', 25000)
            
            if nickname.strip():
                player_data.append({
                    'プレイヤー': f"Player {i+1}",
                    'ニックネーム': nickname,
                    '点数': f"{score:,}点"
                })
        
        if player_data:
            player_df = pd.DataFrame(player_data)
            st.dataframe(player_df, use_container_width=True, hide_index=True)
        else:
            st.warning("有効なプレイヤー情報が抽出できませんでした")
    else:
        st.warning("プレイヤー情報が抽出できませんでした")

def save_game_record_with_names(players_data, game_date, game_time, game_type, notes):
    """対局記録をGoogle Sheetsに保存"""
    valid_players = [p for p in players_data if p['name'].strip()]
    if len(valid_players) < 1:
        st.error("少なくとも1名のプレイヤー名を入力してください")
        return False
    
    game_data = {
        'date': game_date.strftime('%Y-%m-%d'),
        'time': game_time.strftime('%H:%M'),
        'game_type': game_type,
        'player1_name': players_data[0]['name'],
        'player1_score': players_data[0]['score'],
        'player2_name': players_data[1]['name'],
        'player2_score': players_data[1]['score'],
        'player3_name': players_data[2]['name'],
        'player3_score': players_data[2]['score'],
        'player4_name': players_data[3]['name'],
        'player4_score': players_data[3]['score'],
        'notes': notes,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Google Sheetsに保存
    config_manager = ConfigManager()
    sheets_creds = config_manager.load_sheets_credentials()
    spreadsheet_id = config_manager.get_spreadsheet_id()
    
    if not sheets_creds:
        st.error("Google Sheets認証情報が設定されていません")
        st.info("サイドバーの「シーズン管理」で認証情報を設定してください")
        return False
    
    if not spreadsheet_id:
        st.error("スプレッドシートIDが設定されていません")
        st.info("サイドバーの「シーズン管理」でシーズンを設定してください")
        return False
    
    try:
        sheet_manager = SpreadsheetManager(sheets_creds)
        if not sheet_manager.connect(spreadsheet_id):
            st.error("スプレッドシートへの接続に失敗しました")
            return False
        
        if sheet_manager.add_record(game_data):
            current_season = config_manager.get_current_season()
            st.success(f"記録をGoogle Sheets ({current_season}) に保存しました")
            
            # ローカルキャッシュも更新
            if 'game_records' not in st.session_state:
                st.session_state['game_records'] = []
            st.session_state['game_records'].append(game_data)
            
            return True
        else:
            st.error("記録の追加に失敗しました")
            return False
            
    except Exception as e:
        error_message = str(e)
        st.error(f"Google Sheets保存エラー: {error_message}")
        
        # 権限エラーの詳細説明
        if "403" in error_message or "permission" in error_message.lower():
            service_email = sheets_creds.get('client_email', 'N/A')
            st.info(f"権限エラー: スプレッドシートを {service_email} と共有し、編集者権限を付与してください")
        
        return False