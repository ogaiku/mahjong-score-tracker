# ui_components.py - シーズン管理修正版（選択ボタン削除・重複メッセージ修正）
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
    
    # 記録数表示と接続状況
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
    else:
        st.sidebar.info("記録なし")

def display_config_status(config_manager: ConfigManager):
    """設定状況を表示"""
    st.sidebar.subheader("Google Sheets設定")
    
    status = config_manager.get_config_status()
    
    has_sheets_auth = status['sheets_credentials']
    has_seasons = status['season_count'] > 0
    current_season = status['current_season']
    has_current_season_id = status['spreadsheet_id']
    
    if has_sheets_auth and has_seasons and current_season and has_current_season_id:
        season_count = status['season_count']
        st.sidebar.success(f"現在のシーズン: {current_season}")
        st.sidebar.caption(f"登録済みシーズン: {season_count}個")
        
        # スプレッドシートURLの表示
        current_season_info = config_manager.get_season_info(current_season)
        if current_season_info and current_season_info.get('url'):
            spreadsheet_url = current_season_info['url']
            with st.sidebar.expander("スプレッドシート"):
                st.markdown(f"**{current_season_info.get('name', current_season)}**")
                st.markdown(f'<a href="{spreadsheet_url}" target="_blank" style="text-decoration: none;"><button style="background-color: #f0f2f6; color: #262730; border: 1px solid #d4d4d8; padding: 8px 16px; border-radius: 4px; cursor: pointer; width: 100%; font-size: 14px;">新しいタブで開く</button></a>', unsafe_allow_html=True)
                short_url = spreadsheet_url[:50] + "..." if len(spreadsheet_url) > 50 else spreadsheet_url
                st.code(short_url, language=None)
        
        # シーズン選択
        seasons = status['seasons']
        if len(seasons) > 1:
            season_options = {key: info.get('name', key) for key, info in seasons.items()}
            
            # 現在のシーズンをセッション状態で管理
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
                if switch_season_sync(config_manager, selected_season):
                    st.session_state['current_season_key'] = selected_season
                    load_season_data(config_manager, selected_season)
                    st.rerun()
    elif has_sheets_auth and has_seasons:
        # シーズンはあるが現在のシーズンが設定されていない場合
        st.sidebar.warning("シーズン未選択")
        season_count = status['season_count']
        st.sidebar.caption(f"登録済み: {season_count}個")
    elif has_sheets_auth:
        # 認証はあるがシーズンがない場合
        st.sidebar.info("シーズン未登録")
    else:
        st.sidebar.error("未設定")
    
    # シーズン管理
    with st.sidebar.expander("シーズン管理", expanded=False):
        if not has_sheets_auth:
            st.warning("Google Sheets認証が必要")
            return
        
        # セッション状態初期化
        if 'season_management_state' not in st.session_state:
            st.session_state['season_management_state'] = {
                'new_season_name': '',
                'operation_in_progress': False,
                'last_operation': None
            }
        
        # 新シーズン追加
        st.subheader("新シーズン追加")
        
        # 操作中の場合は入力を無効化
        disabled = st.session_state['season_management_state']['operation_in_progress']
        
        new_season_name = st.text_input(
            "シーズン名", 
            value=st.session_state['season_management_state']['new_season_name'],
            placeholder="例: 2024年春シーズン",
            disabled=disabled,
            key="season_name_input"
        )
        
        if st.button("シーズン追加", disabled=disabled or not new_season_name.strip(), key="add_season_button"):
            # 操作開始
            st.session_state['season_management_state']['operation_in_progress'] = True
            st.session_state['season_management_state']['last_operation'] = 'add'
            
            season_key = new_season_name.strip().replace(' ', '_').lower()
            
            # 既存チェック
            existing_seasons = config_manager.get_all_seasons()
            if season_key in existing_seasons:
                st.error(f"シーズンキー '{season_key}' は既に存在します")
                st.session_state['season_management_state']['operation_in_progress'] = False
            else:
                # シーズン作成実行
                success = create_new_season_sync(config_manager, season_key, new_season_name.strip())
                
                if success:
                    st.success(f"'{new_season_name.strip()}' を作成")
                    # 入力フィールドをクリア
                    st.session_state['season_management_state']['new_season_name'] = ''
                    # セッション状態をクリアして最新の設定を反映
                    if 'current_season_key' in st.session_state:
                        del st.session_state['current_season_key']
                    # 操作完了
                    st.session_state['season_management_state']['operation_in_progress'] = False
                    st.rerun()
                else:
                    st.error("作成失敗")
                    st.session_state['season_management_state']['operation_in_progress'] = False
        
        # 既存シーズン管理
        if has_seasons:
            st.subheader("既存シーズン")
            seasons = status['seasons']
            current_season = status['current_season']
            
            if len(seasons) > 0:
                for season_key, season_info in seasons.items():
                    season_name = season_info.get('name', season_key)
                    
                    # 各シーズンのコンテナ
                    with st.container():
                        if season_key == current_season:
                            st.write(f"**{season_name}** (現在)")
                        else:
                            st.write(f"**{season_name}**")
                        
                        # 現在のシーズンではない場合のみ削除ボタンを表示
                        if season_key != current_season:
                            delete_key = f"delete_{season_key}"
                            confirm_key = f"confirm_delete_{season_key}"
                            
                            if st.session_state.get(confirm_key, False):
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("削除実行", key=f"exec_delete_{season_key}", type="primary", use_container_width=True, disabled=disabled):
                                        st.session_state['season_management_state']['operation_in_progress'] = True
                                        success = delete_season_sync(config_manager, season_key)
                                        if success:
                                            st.success(f"シーズン '{season_name}' を削除しました")
                                            if confirm_key in st.session_state:
                                                del st.session_state[confirm_key]
                                            st.session_state['season_management_state']['operation_in_progress'] = False
                                            st.rerun()
                                        else:
                                            st.error("削除に失敗しました")
                                            st.session_state['season_management_state']['operation_in_progress'] = False
                                with col2:
                                    if st.button("キャンセル", key=f"cancel_{season_key}", use_container_width=True):
                                        del st.session_state[confirm_key]
                                        st.rerun()
                            else:
                                if st.button("削除", key=delete_key, use_container_width=True, disabled=disabled):
                                    st.session_state[confirm_key] = True
                                    st.rerun()
                        
                        st.divider()
            else:
                st.info("シーズンなし")

def create_new_season_sync(config_manager: ConfigManager, season_key: str, season_name: str) -> bool:
    """新しいシーズンを同期的に作成"""
    try:
        # プログレスバー表示
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("作成中...")
        progress_bar.progress(25)
        
        # シーズンを追加（シーズン名でスプレッドシート作成）
        if config_manager.add_season(season_key, season_name, auto_create=True):
            progress_bar.progress(100)
            status_text.text("完了")
            
            # 新しいシーズンのデータを初期化
            initialize_new_season_data()
            
            # プログレスバーを削除
            progress_bar.empty()
            status_text.empty()
            
            return True
        else:
            progress_bar.empty()
            status_text.empty()
            return False
            
    except Exception as e:
        st.error(f"シーズン作成エラー: {e}")
        return False

def switch_season_sync(config_manager: ConfigManager, season_key: str) -> bool:
    """シーズンを同期的に切り替え"""
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text(f"'{season_key}' に切り替え中...")
        progress_bar.progress(50)
        
        success = config_manager.set_current_season(season_key)
        
        progress_bar.progress(100)
        
        if success:
            status_text.text("完了")
        else:
            status_text.text("失敗")
        
        # クリーンアップ
        progress_bar.empty()
        status_text.empty()
        
        return success
        
    except Exception as e:
        st.error(f"シーズン切り替えエラー: {e}")
        return False

def delete_season_sync(config_manager: ConfigManager, season_key: str) -> bool:
    """シーズンを同期的に削除"""
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text(f"'{season_key}' を削除中...")
        progress_bar.progress(50)
        
        success = config_manager.delete_season(season_key)
        
        progress_bar.progress(100)
        
        if success:
            status_text.text("完了")
        else:
            status_text.text("失敗")
        
        # クリーンアップ
        progress_bar.empty()
        status_text.empty()
        
        return success
        
    except Exception as e:
        st.error(f"シーズン削除エラー: {e}")
        return False

def load_season_data(config_manager: ConfigManager, season_key: str):
    """シーズンデータを読み込み"""
    try:
        # 既存のデータをクリア
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
                    else:
                        st.session_state['game_records'] = []
                else:
                    st.session_state['game_records'] = []
            except Exception as e:
                st.session_state['game_records'] = []
        else:
            st.session_state['game_records'] = []
            
    except Exception as e:
        st.session_state['game_records'] = []

def initialize_new_season_data():
    """新シーズンのデータを初期化"""
    st.session_state['game_records'] = []

def sync_data_from_sheets(config_manager: ConfigManager):
    """Google Sheetsからデータを手動同期"""
    try:
        current_season = config_manager.get_current_season()
        
        if not current_season:
            st.sidebar.warning("シーズンが未設定")
            return
        
        with st.sidebar:
            with st.spinner("同期中..."):
                load_season_data(config_manager, current_season)
                
                if 'game_records' in st.session_state and st.session_state['game_records']:
                    record_count = len(st.session_state['game_records'])
                    st.success(f"{record_count}件同期完了")
                else:
                    st.info("データなし")
                
    except Exception as e:
        st.sidebar.error(f"同期エラー: {e}")

def check_sheets_sync_status(config_manager: ConfigManager) -> dict:
    """Google Sheets同期状況をチェック"""
    try:
        sheets_creds = config_manager.load_sheets_credentials()
        spreadsheet_id = config_manager.get_spreadsheet_id()
        
        if not sheets_creds or not spreadsheet_id:
            return {'configured': False, 'can_connect': False}
        
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

def extract_data_from_image(image):
    """画像からデータを抽出"""
    config_manager = ConfigManager()
    
    openai_key = config_manager.get_openai_api_key()
    vision_creds = config_manager.load_vision_credentials()
    
    if not openai_key or openai_key == "your-openai-api-key-here":
        st.error("OpenAI API Keyが正しく設定されていません")
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
    if 'analysis_result' not in st.session_state or st.session_state['analysis_result'] is None:
        return
    
    result = st.session_state['analysis_result']
    
    if not result.get('success', False):
        st.error(result.get('message', '解析に失敗しました'))
        return
    
    st.success("解析完了")

def save_game_record_with_names(players_data, game_date, game_time, game_type, notes):
    """対局記録をGoogle Sheetsに保存（重複メッセージ修正版）"""
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
    
    config_manager = ConfigManager()
    sheets_creds = config_manager.load_sheets_credentials()
    spreadsheet_id = config_manager.get_spreadsheet_id()
    
    if not sheets_creds:
        st.error("Google Sheets認証情報が設定されていません")
        return False
    
    if not spreadsheet_id:
        st.error("シーズンを作成してください")
        return False
    
    try:
        sheet_manager = SpreadsheetManager(sheets_creds)
        if not sheet_manager.connect(spreadsheet_id):
            st.error("スプレッドシートへの接続に失敗しました")
            return False
        
        if sheet_manager.add_record(game_data):
            # 成功メッセージを1回だけ表示
            st.success("記録を保存しました")
            
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
        
        if "403" in error_message or "permission" in error_message.lower():
            service_email = sheets_creds.get('client_email', 'N/A')
            st.info(f"権限エラー: スプレッドシートを {service_email} と共有し、編集者権限を付与してください")
        
        return False