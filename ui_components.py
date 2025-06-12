# ui_components.py - 設定ファイル対応版
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
    """設定状況を表示"""
    st.sidebar.subheader("API設定状況")
    
    status = config_manager.get_config_status()
    
    # OpenAI API
    if status['openai_api_key']:
        st.sidebar.success("OpenAI API設定済み")
    else:
        st.sidebar.error("OpenAI API未設定")
    
    # Vision API
    if status['vision_credentials']:
        auth_type = status['vision_auth_type']
        if auth_type == "api_key":
            st.sidebar.success("Vision API設定済み（APIキー）")
        elif auth_type == "json_file":
            st.sidebar.success("Vision API設定済み（JSONファイル）")
        else:
            st.sidebar.error("Vision API未設定")
    else:
        st.sidebar.error("Vision API未設定")
    
    # Google Sheets & シーズン管理
    st.sidebar.subheader("Google Sheets & シーズン")
    
    # 認証情報とシーズン設定の確認
    has_sheets_auth = status['sheets_credentials']
    has_seasons = status['season_count'] > 0
    has_current_season_id = status['spreadsheet_id']
    
    if has_sheets_auth and has_seasons and has_current_season_id:
        current_season = status['current_season']
        season_count = status['season_count']
        st.sidebar.success(f"現在: {current_season} ({season_count}シーズン)")
        
        # シーズン選択
        seasons = status['seasons']
        if len(seasons) > 1:
            season_options = {key: info.get('name', key) for key, info in seasons.items()}
            selected_season = st.sidebar.selectbox(
                "シーズン選択",
                options=list(season_options.keys()),
                format_func=lambda x: season_options[x],
                index=list(season_options.keys()).index(current_season) if current_season in season_options else 0
            )
            
            if selected_season != current_season:
                if st.sidebar.button("シーズン変更"):
                    if config_manager.set_current_season(selected_season):
                        st.sidebar.success(f"{selected_season}に変更しました")
                        st.rerun()
        
        # 現在のシーズン情報表示
        current_season_info = config_manager.get_season_info(current_season)
        if current_season_info:
            st.sidebar.caption(f"名前: {current_season_info.get('name', '')}")
            st.sidebar.caption(f"ID: {current_season_info.get('spreadsheet_id', '')}")
    
    elif has_sheets_auth and has_seasons:
        st.sidebar.warning("Sheets認証OK、現在のシーズンにスプレッドシートIDなし")
    elif has_sheets_auth:
        st.sidebar.warning("Sheets認証OK、シーズン未設定")
    elif has_seasons:
        st.sidebar.warning("シーズン設定あり、Sheets認証なし")
    else:
        st.sidebar.error("Google Sheets未設定")
    
    # シーズン管理（認証の有無に関わらず表示）
    with st.sidebar.expander("シーズン管理"):
        if not has_sheets_auth:
            st.warning("Google Sheets認証ファイルが必要です")
            st.info("config.jsonでcredentials_fileを設定するか、Vision APIのJSONファイルを共用してください")
        
        # 新しいシーズン追加
        st.subheader("新シーズン追加")
        
        with st.form("add_season_form"):
            new_season_key = st.text_input("シーズンキー", placeholder="season2")
            new_season_name = st.text_input("シーズン名", placeholder="mahjong-score-tracker season2")
            
            # 作成方法選択
            creation_method = st.radio(
                "作成方法",
                ["自動作成", "既存URLを指定"],
                help="自動作成では新しいスプレッドシートを作成します"
            )
            
            new_season_url = ""
            if creation_method == "既存URLを指定":
                new_season_url = st.text_input("スプレッドシートURL", placeholder="https://docs.google.com/spreadsheets/d/...")
            
            if st.form_submit_button("シーズン追加"):
                if new_season_key and new_season_name:
                    if creation_method == "自動作成":
                        if config_manager.add_season(new_season_key, new_season_name, auto_create=True):
                            st.success(f"シーズン '{new_season_key}' を自動作成しました")
                            st.rerun()
                    else:
                        if new_season_url:
                            if config_manager.add_season(new_season_key, new_season_name, new_season_url):
                                st.success(f"シーズン '{new_season_key}' を追加しました")
                                st.rerun()
                        else:
                            st.error("スプレッドシートURLを入力してください")
                else:
                    st.error("シーズンキーと名前を入力してください")
        
        # 既存シーズン一覧
        if has_seasons:
            st.subheader("登録済みシーズン")
            seasons = status['seasons']
            for key, info in seasons.items():
                is_current = (key == status['current_season'])
                marker = " (現在)" if is_current else ""
                with st.container():
                    st.caption(f"• {info.get('name', key)}{marker}")
                    if st.button(f"🔗", key=f"open_{key}", help="スプレッドシートを開く"):
                        st.write(f"URL: {info.get('url', '')}")
        else:
            st.info("まだシーズンが登録されていません")
    
    # 設定ファイル管理
    with st.sidebar.expander("設定ファイル管理"):
        if st.button("設定テンプレート作成", use_container_width=True):
            from config_manager import create_config_template
            template_file = create_config_template()
            if template_file:
                st.success(f"{template_file}を作成しました")
        
        st.info("config.jsonファイルを編集してAPIキーを設定してください")
        st.caption("Vision APIはAPIキーまたはJSONファイルで認証できます")

def extract_data_from_image(image):
    """画像からデータを抽出"""
    # 設定マネージャーから認証情報を取得
    config_manager = ConfigManager()
    
    # API認証情報の確認
    openai_key = config_manager.get_openai_api_key()
    vision_creds = config_manager.load_vision_credentials()
    
    if not openai_key:
        st.error("OpenAI API Keyが設定されていません。config.jsonファイルを確認してください。")
        return
    
    if not vision_creds:
        st.error("Google Vision APIの認証情報が設定されていません。認証ファイルを確認してください。")
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
            st.error(f"解析エラー: {e}")
            st.session_state['analysis_result'] = {
                'success': False,
                'message': f'エラー: {str(e)}',
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
                        st.info("Google Sheetsにも保存しました")
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