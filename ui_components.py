# ui_components.py - 自動シーズン切り替え対応版
import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import json
from datetime import datetime, date
from score_extractor import MahjongScoreExtractor
from spreadsheet_manager import SpreadsheetManager
from config_manager import ConfigManager

def setup_sidebar():
    """サイドバーの設定"""
    st.sidebar.title("設定")
    
    # 設定マネージャーの初期化
    config_manager = ConfigManager()
    
    # 設定状況の表示
    display_config_status(config_manager)
    
    st.sidebar.divider()
    
    # データ管理セクション
    st.sidebar.subheader("データ管理")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("データ表示", use_container_width=True, key="sidebar_data_btn"):
            st.session_state['show_data'] = True
    
    with col2:
        if st.button("統計表示", use_container_width=True, key="sidebar_stats_btn"):
            st.session_state['show_stats'] = True
    
    # 記録数とダウンロード
    if 'game_records' in st.session_state and st.session_state['game_records']:
        st.sidebar.metric("保存済み記録", f"{len(st.session_state['game_records'])}件")
        
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
        st.sidebar.info("記録なし")

def display_config_status(config_manager: ConfigManager):
    """設定状況を表示（簡略版）"""
    st.sidebar.subheader("Google Sheets & シーズン")
    
    status = config_manager.get_config_status()
    
    # 認証情報とシーズン設定の確認
    has_sheets_auth = status['sheets_credentials']
    has_seasons = status['season_count'] > 0
    has_current_season_id = status['spreadsheet_id']
    
    if has_sheets_auth and has_seasons and has_current_season_id:
        current_season = status['current_season']
        season_count = status['season_count']
        # より分かりやすい表示に変更
        st.sidebar.success(f"アクティブシーズン: {current_season}")
        st.sidebar.caption(f"登録済みシーズン数: {season_count}個")
        
        # シーズン選択 - 自動切り替え機能付き
        seasons = status['seasons']
        if len(seasons) > 1:
            season_options = {key: info.get('name', key) for key, info in seasons.items()}
            
            # セッション状態でシーズン変更を追跡
            if 'current_season_key' not in st.session_state:
                st.session_state['current_season_key'] = current_season
            
            selected_season = st.sidebar.selectbox(
                "シーズン切り替え",
                options=list(season_options.keys()),
                format_func=lambda x: season_options[x],
                index=list(season_options.keys()).index(st.session_state['current_season_key']) if st.session_state['current_season_key'] in season_options else 0,
                key="season_selector"
            )
            
            # シーズンが変更された場合の自動処理
            if selected_season != st.session_state['current_season_key']:
                with st.sidebar:
                    with st.spinner("シーズンを切り替え中..."):
                        if switch_season_automatically(config_manager, selected_season):
                            st.session_state['current_season_key'] = selected_season
                            # データをクリアして新しいシーズンのデータを読み込み
                            load_season_data(config_manager, selected_season)
                            st.success(f"シーズン '{selected_season}' に切り替えました")
                            st.rerun()
                        else:
                            st.error("シーズンの切り替えに失敗しました")
        
        # 現在のシーズン情報表示
        current_season_info = config_manager.get_season_info(current_season)
        if current_season_info:
            st.sidebar.caption(f"スプレッドシート: {current_season_info.get('name', '')}")
    
    elif has_sheets_auth and has_seasons:
        st.sidebar.warning("現在のシーズンにスプレッドシートIDなし")
    elif has_sheets_auth:
        st.sidebar.warning("シーズン未設定")
    elif has_seasons:
        st.sidebar.warning("シーズン設定あり、Sheets認証なし")
    else:
        st.sidebar.error("Google Sheets未設定")
    
    # シーズン管理（認証の有無に関わらず表示）
    with st.sidebar.expander("シーズン管理"):
        if not has_sheets_auth:
            st.warning("Google Sheets認証ファイルが必要です")
            st.info("config.jsonでcredentials_fileを設定するか、Vision APIのJSONファイルを共用してください")
        
        # 新しいシーズン追加 - 最簡化版
        st.subheader("新シーズン追加")
        
        with st.form("add_season_form"):
            season_name = st.text_input(
                "シーズン名", 
                placeholder="例: season1, season2, 2024spring",
                help="入力したシーズン名でスプレッドシートが自動作成されます"
            )
            
            # 生成されるスプレッドシート名をプレビュー表示
            if season_name:
                spreadsheet_name = f"mahjong-score-tracker-{season_name}"
                st.caption(f"作成されるスプレッドシート名: **{spreadsheet_name}**")
            
            if st.form_submit_button("シーズン追加", use_container_width=True):
                if season_name:
                    success, created_info = create_and_switch_season_simple(
                        config_manager, season_name
                    )
                    if success:
                        st.success(f"シーズン '{season_name}' を作成しました")
                        st.session_state['current_season_key'] = season_name
                        st.info(f"シーズン '{season_name}' に切り替えました")
                        st.rerun()
                else:
                    st.error("シーズン名を入力してください")
        
        # 既存シーズン一覧 - 削除機能付き
        if has_seasons:
            st.subheader("登録済みシーズン")
            seasons = status['seasons']
            for key, info in seasons.items():
                is_current = (key == status['current_season'])
                marker = " (現在)" if is_current else ""
                with st.container():
                    col1, col2, col3, col4 = st.columns([2.5, 0.8, 0.8, 0.8])
                    with col1:
                        st.caption(f"• {key}{marker}")
                    with col2:
                        spreadsheet_url = info.get('url', '')
                        if spreadsheet_url and st.button("リンク", key=f"open_{key}", help="クリックでリンクを表示"):
                            # セッション状態でリンク表示を管理
                            show_link_key = f"show_link_{key}"
                            if show_link_key not in st.session_state:
                                st.session_state[show_link_key] = False
                            st.session_state[show_link_key] = not st.session_state[show_link_key]
                            
                    # リンク表示（expanderの外で）
                    show_link_key = f"show_link_{key}"
                    if show_link_key in st.session_state and st.session_state[show_link_key]:
                        st.text("スプレッドシートリンク:")
                        st.code(spreadsheet_url, language=None)
                        st.caption("上のリンクを選択してコピーしてください")
                    with col3:
                        if not is_current and st.button("選択", key=f"select_{key}", help="このシーズンに切り替え"):
                            if switch_season_automatically(config_manager, key):
                                st.session_state['current_season_key'] = key
                                load_season_data(config_manager, key)
                                st.success(f"シーズン '{key}' に切り替えました")
                                st.rerun()
                    with col4:
                        if not is_current and st.button("削除", key=f"delete_{key}", help="このシーズンを削除"):
                            # 削除確認の状態管理
                            confirm_key = f"confirm_delete_{key}"
                            if confirm_key not in st.session_state:
                                st.session_state[confirm_key] = False
                            
                            if not st.session_state[confirm_key]:
                                st.session_state[confirm_key] = True
                                st.warning(f"シーズン '{key}' を削除しますか？もう一度削除ボタンを押してください")
                                st.rerun()
                            else:
                                if config_manager.delete_season(key):
                                    st.success(f"シーズン '{key}' を削除しました")
                                    # 確認状態をリセット
                                    del st.session_state[confirm_key]
                                    st.rerun()
                                else:
                                    st.error("削除に失敗しました")
                                    del st.session_state[confirm_key]
        else:
            st.info("まだシーズンが登録されていません")

def create_and_switch_season_simple(config_manager: ConfigManager, season_name: str) -> tuple[bool, dict]:
    """シーズン名のみで新しいシーズンを作成し、自動切り替え"""
    try:
        # スプレッドシート名を生成
        spreadsheet_name = f"mahjong-score-tracker-{season_name}"
        
        # シーズンを自動作成（シーズンキーとシーズン名は同じ）
        if config_manager.add_season(season_name, spreadsheet_name, auto_create=True):
            # 自動切り替え
            if config_manager.set_current_season(season_name):
                # 新しいシーズンのデータを初期化
                initialize_new_season_data()
                return True, {"switched": True}
            else:
                return True, {"switched": False, "error": "切り替えに失敗"}
        return False, {"error": "シーズン作成に失敗"}
    except Exception as e:
        st.error(f"シーズン作成エラー: {e}")
        return False, {"error": str(e)}

def switch_season_automatically(config_manager: ConfigManager, season_key: str) -> bool:
    """シーズンを自動切り替え"""
    try:
        return config_manager.set_current_season(season_key)
    except Exception as e:
        st.error(f"シーズン切り替えエラー: {e}")
        return False

def load_season_data(config_manager: ConfigManager, season_key: str):
    """指定したシーズンのデータを読み込み"""
    try:
        # 現在のローカルデータをクリア
        if 'game_records' in st.session_state:
            del st.session_state['game_records']
        
        # Google Sheetsからデータを読み込み（可能な場合）
        sheets_creds = config_manager.load_sheets_credentials()
        spreadsheet_id = config_manager.get_spreadsheet_id()
        
        if sheets_creds and spreadsheet_id:
            try:
                sheet_manager = SpreadsheetManager(sheets_creds)
                if sheet_manager.connect(spreadsheet_id):
                    records = sheet_manager.get_all_records()
                    if records:
                        # Google Sheetsの形式からアプリの形式に変換
                        converted_records = convert_sheets_records(records)
                        st.session_state['game_records'] = converted_records
                        st.info(f"シーズン '{season_key}' のデータを読み込みました ({len(converted_records)}件)")
                    else:
                        st.info(f"シーズン '{season_key}' にはまだデータがありません")
            except Exception as e:
                st.warning(f"シーズンデータの読み込みに失敗: {e}")
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")

def initialize_new_season_data():
    """新しいシーズンのデータを初期化"""
    if 'game_records' in st.session_state:
        del st.session_state['game_records']
    st.info("新しいシーズンを開始しました")

def convert_sheets_records(sheets_records: list) -> list:
    """Google Sheetsの記録をアプリの形式に変換"""
    converted = []
    for record in sheets_records:
        # Google Sheetsの列名からアプリの形式に変換
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

def delete_season_with_confirmation(config_manager: ConfigManager, season_key: str) -> bool:
    """シーズンを削除（確認付き）"""
    try:
        # 現在のシーズンは削除不可
        current_season = config_manager.get_current_season()
        if season_key == current_season:
            st.error("現在アクティブなシーズンは削除できません")
            return False
        
        # シーズンを削除
        if config_manager.delete_season(season_key):
            return True
        else:
            return False
    except Exception as e:
        st.error(f"シーズン削除エラー: {e}")
        return False

def extract_data_from_image(image):
    """画像からデータを抽出"""
    # 設定マネージャーから認証情報を取得
    config_manager = ConfigManager()
    
    # API認証情報の確認
    openai_key = config_manager.get_openai_api_key()
    vision_creds = config_manager.load_vision_credentials()
    
    # OpenAI APIキーの詳細チェック
    if not openai_key or openai_key == "your-openai-api-key-here" or openai_key.startswith("your-ope"):
        st.error("OpenAI API Keyが正しく設定されていません")
        st.markdown("""
        **設定方法:**
        1. [OpenAI API Keys](https://platform.openai.com/account/api-keys) にアクセス
        2. 新しいAPIキーを作成（sk-で始まる文字列）
        3. config.jsonファイルの`openai.api_key`を更新
        
        **config.json例:**
        ```json
        {
          "openai": {
            "api_key": "sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "model": "gpt-4o"
          }
        }
        ```
        """)
        return
    
    if not vision_creds:
        st.error("Google Vision APIの認証情報が設定されていません")
        st.info("config.jsonでcredentials_fileを確認してください")
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
            
            # OpenAI API関連のエラーを詳しく表示
            if "401" in error_message or "invalid_api_key" in error_message:
                st.error("OpenAI APIキーが無効です")
                st.markdown("""
                **解決方法:**
                1. APIキーが正しいか確認（sk-で始まる）
                2. APIキーに十分なクレジットがあるか確認
                3. [OpenAI Platform](https://platform.openai.com/account/api-keys) で新しいキーを作成
                """)
            elif "quota" in error_message.lower() or "limit" in error_message.lower():
                st.error("OpenAI APIの利用制限に達しています")
                st.info("APIクレジットを追加するか、しばらく時間をおいてから再試行してください")
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
    result = st.session_state['analysis_result']
    
    if not result.get('success', False):
        st.error(result.get('message', '解析に失敗しました'))
        return
    
    # 成功メッセージと信頼度
    confidence = result.get('confidence', 0.0)
    st.success("解析完了")
    st.write(f"信頼度: {confidence:.0%}")
    
    # 解析されたプレイヤー情報
    players = result.get('players', [])
    
    if any(player.get('nickname', '').strip() for player in players):
        st.subheader("抽出されたプレイヤー情報")
        
        # テーブル形式で表示
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
    
    # 注意事項があれば表示
    notes = result.get('notes', '')
    if notes:
        st.info(f"解析メモ: {notes}")
    
    # 詳細は折りたたみで表示
    with st.expander("抽出テキスト詳細"):
        extracted_text = result.get('extracted_text', '')
        if extracted_text:
            st.text(extracted_text)
        else:
            st.info("テキストが抽出されませんでした")

def create_extraction_form():
    """抽出データの確認・修正フォーム"""
    result = st.session_state['analysis_result']
    
    if not result.get('success', False):
        st.warning("解析結果がありません")
        return
    
    players = result.get('players', [])
    
    # プレイヤーデータが不足している場合は空のデータで埋める
    while len(players) < 4:
        players.append({'nickname': '', 'score': 25000})
    
    st.subheader("データ確認・修正")
    
    with st.form("extraction_form"):
        # プレイヤー情報を4列で表示
        col1, col2, col3, col4 = st.columns(4)
        
        players_data = []
        
        with col1:
            st.caption("プレイヤー1")
            name1 = st.text_input(
                "名前", 
                value=players[0].get('nickname', ''), 
                key="name1", 
                label_visibility="collapsed",
                placeholder="ニックネーム"
            )
            score1 = st.number_input(
                "点数", 
                value=int(players[0].get('score', 25000)), 
                min_value=-100000,
                max_value=200000,
                step=100,
                key="score1", 
                label_visibility="collapsed"
            )
            players_data.append({"name": name1, "score": score1})
        
        with col2:
            st.caption("プレイヤー2")
            name2 = st.text_input(
                "名前", 
                value=players[1].get('nickname', ''), 
                key="name2", 
                label_visibility="collapsed",
                placeholder="ニックネーム"
            )
            score2 = st.number_input(
                "点数", 
                value=int(players[1].get('score', 25000)), 
                min_value=-100000,
                max_value=200000,
                step=100,
                key="score2", 
                label_visibility="collapsed"
            )
            players_data.append({"name": name2, "score": score2})
        
        with col3:
            st.caption("プレイヤー3")
            name3 = st.text_input(
                "名前", 
                value=players[2].get('nickname', ''), 
                key="name3", 
                label_visibility="collapsed",
                placeholder="ニックネーム"
            )
            score3 = st.number_input(
                "点数", 
                value=int(players[2].get('score', 25000)), 
                min_value=-100000,
                max_value=200000,
                step=100,
                key="score3", 
                label_visibility="collapsed"
            )
            players_data.append({"name": name3, "score": score3})
        
        with col4:
            st.caption("プレイヤー4")
            name4 = st.text_input(
                "名前", 
                value=players[3].get('nickname', ''), 
                key="name4", 
                label_visibility="collapsed",
                placeholder="ニックネーム"
            )
            score4 = st.number_input(
                "点数", 
                value=int(players[3].get('score', 25000)), 
                min_value=-100000,
                max_value=200000,
                step=100,
                key="score4", 
                label_visibility="collapsed"
            )
            players_data.append({"name": name4, "score": score4})
        
        st.divider()
        
        # 対局情報
        col_info1, col_info2, col_info3 = st.columns(3)
        
        with col_info1:
            game_date = st.date_input("対局日", value=date.today())
        
        with col_info2:
            game_time = st.time_input("対局時刻")
        
        with col_info3:
            game_type = st.selectbox("対局タイプ", ["四麻東風", "四麻半荘", "三麻東風", "三麻半荘"])
        
        notes = st.text_area("メモ", placeholder="特記事項", height=80)
        
        # 信頼度による警告表示
        confidence = result.get('confidence', 0.0)
        if confidence < 0.8:
            st.warning(f"解析信頼度が{confidence:.0%}です。データを確認してください。")
        
        # 保存ボタン
        submitted = st.form_submit_button("記録を保存", type="primary", use_container_width=True)
        
        if submitted:
            save_game_record_with_names(players_data, game_date, game_time, game_type, notes)

def create_manual_input_form():
    """手動入力フォーム"""
    st.subheader("対局データ入力")
    
    # デフォルト値を設定ファイルから取得
    config_manager = ConfigManager()
    default_game_type = config_manager.get_default_game_type()
    
    with st.form("manual_input_form"):
        # プレイヤー情報
        col1, col2, col3, col4 = st.columns(4)
        
        players_data = []
        
        with col1:
            st.caption("プレイヤー1")
            name1 = st.text_input("名前", key="manual_name1", label_visibility="collapsed", placeholder="ニックネーム")
            score1 = st.number_input("点数", min_value=-100000, max_value=200000, value=25000, step=100, key="manual_score1", label_visibility="collapsed")
            players_data.append({"name": name1, "score": score1})
        
        with col2:
            st.caption("プレイヤー2")
            name2 = st.text_input("名前", key="manual_name2", label_visibility="collapsed", placeholder="ニックネーム")
            score2 = st.number_input("点数", min_value=-100000, max_value=200000, value=25000, step=100, key="manual_score2", label_visibility="collapsed")
            players_data.append({"name": name2, "score": score2})
        
        with col3:
            st.caption("プレイヤー3")
            name3 = st.text_input("名前", key="manual_name3", label_visibility="collapsed", placeholder="ニックネーム")
            score3 = st.number_input("点数", min_value=-100000, max_value=200000, value=25000, step=100, key="manual_score3", label_visibility="collapsed")
            players_data.append({"name": name3, "score": score3})
        
        with col4:
            st.caption("プレイヤー4")
            name4 = st.text_input("名前", key="manual_name4", label_visibility="collapsed", placeholder="ニックネーム")
            score4 = st.number_input("点数", min_value=-100000, max_value=200000, value=25000, step=100, key="manual_score4", label_visibility="collapsed")
            players_data.append({"name": name4, "score": score4})
        
        st.divider()
        
        # 対局情報
        col_info1, col_info2, col_info3 = st.columns(3)
        
        with col_info1:
            game_date = st.date_input("対局日", value=date.today())
        
        with col_info2:
            game_time = st.time_input("対局時刻")
        
        with col_info3:
            game_types = ["四麻東風", "四麻半荘", "三麻東風", "三麻半荘"]
            default_index = game_types.index(default_game_type) if default_game_type in game_types else 0
            game_type = st.selectbox("対局タイプ", game_types, index=default_index)
        
        notes = st.text_area("メモ", placeholder="特記事項", height=80)
        
        # 保存ボタン
        submitted = st.form_submit_button("記録を保存", type="primary", use_container_width=True)
        
        if submitted:
            save_game_record_with_names(players_data, game_date, game_time, game_type, notes)

def save_game_record_with_names(players_data, game_date, game_time, game_type, notes):
    """ニックネーム付きで対局記録を保存"""
    
    # 入力値検証
    valid_players = [p for p in players_data if p['name'].strip()]
    if len(valid_players) < 2:
        st.error("最低2名のプレイヤー名を入力してください")
        return
    
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
    
    # ローカル保存
    if 'game_records' not in st.session_state:
        st.session_state['game_records'] = []
    
    st.session_state['game_records'].append(game_data)
    st.success("記録を保存しました")
    
    # Google Sheets保存（設定ファイルから）
    config_manager = ConfigManager()
    if config_manager.get_auto_save_to_sheets():
        sheets_creds = config_manager.load_sheets_credentials()
        spreadsheet_id = config_manager.get_spreadsheet_id()
        
        if sheets_creds and spreadsheet_id:
            try:
                sheet_manager = SpreadsheetManager(sheets_creds)
                if sheet_manager.connect(spreadsheet_id):
                    if sheet_manager.add_record(game_data):
                        current_season = config_manager.get_current_season()
                        st.info(f"Google Sheets ({current_season}) にも保存しました")
            except Exception as e:
                st.warning(f"Google Sheets保存に失敗: {e}")
        else:
            st.info("Google Sheets設定が不完全です（自動保存スキップ）")

def display_simple_table(data, title="データ"):
    """シンプルなテーブル表示"""
    if title:
        st.subheader(title)
    
    if not data:
        st.info("表示するデータがありません")
        return
    
    df = pd.DataFrame(data)
    
    # 列名を日本語に変更
    column_mapping = {
        'date': '対局日',
        'time': '時刻',
        'game_type': 'タイプ',
        'player1_name': 'P1',
        'player1_score': 'P1点数',
        'player2_name': 'P2',
        'player2_score': 'P2点数',
        'player3_name': 'P3',
        'player3_score': 'P3点数',
        'player4_name': 'P4',
        'player4_score': 'P4点数',
        'notes': 'メモ'
    }
    
    display_df = df.rename(columns=column_mapping)
    
    # 不要な列を除外
    if 'timestamp' in display_df.columns:
        display_df = display_df.drop('timestamp', axis=1)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

def create_clean_metrics(stats_data):
    """クリーンなメトリクス表示"""
    if not stats_data:
        return
    
    cols = st.columns(4)
    
    # 総対局数
    with cols[0]:
        st.metric("総対局数", f"{stats_data.get('total_games', 0)}回")
    
    # 各プレイヤーの平均点数（上位3名）
    if 'avg_scores' in stats_data:
        avg_scores = stats_data['avg_scores']
        sorted_players = sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        
        for i, (player, avg_score) in enumerate(sorted_players):
            if i < 3:
                with cols[i+1]:
                    player_num = player.replace('player', 'P')
                    st.metric(f"{player_num}平均", f"{avg_score:,.0f}点")