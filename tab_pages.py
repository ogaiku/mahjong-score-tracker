# tab_pages.py (simplified)
import streamlit as st
import pandas as pd
from PIL import Image
from datetime import date
from input_forms import (
    create_player_input_fields, 
    create_player_input_fields_with_defaults,
    create_score_input_fields,
    create_game_info_fields,
    show_input_confirmation,
    save_game_record
)
from ui_components import extract_data_from_image, display_extraction_results
from data_modals import show_data_modal, show_statistics_modal
from player_stats_ui import show_player_statistics_modal

def home_tab():
    st.header("ダッシュボード")
    
    if 'game_records' in st.session_state and st.session_state['game_records']:
        # 基本統計
        total_games = len(st.session_state['game_records'])
        
        from player_manager import PlayerManager
        player_manager = PlayerManager(st.session_state['game_records'])
        all_players = player_manager.get_all_player_names()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("総対局数", f"{total_games}回")
        with col2:
            st.metric("参加プレイヤー数", f"{len(all_players)}人")
        with col3:
            if st.button("詳細統計", use_container_width=True):
                st.session_state['show_player_stats'] = True
                st.rerun()
        
        # 最近の記録
        st.subheader("最近の対局記録")
        recent_records = st.session_state['game_records'][-5:]
        display_recent_records(recent_records)
    else:
        st.info("記録がありません。対局データを追加してください。")
    
    # モーダル表示
    if st.session_state.get('show_data', False):
        show_data_modal()
    
    if st.session_state.get('show_stats', False):
        show_statistics_modal()
    
    if st.session_state.get('show_player_stats', False):
        show_player_statistics_modal()
        if st.button("統計を閉じる", use_container_width=True):
            st.session_state['show_player_stats'] = False
            st.rerun()

def display_recent_records(records):
    if not records:
        st.info("表示する記録がありません")
        return
    
    display_data = []
    for record in reversed(records):
        players_info = []
        for i in range(1, 5):
            name_key = f'player{i}_name'
            score_key = f'player{i}_score'
            
            if name_key in record and score_key in record:
                name = record[name_key]
                score = record[score_key]
                
                if name and str(name).strip():
                    players_info.append(f"{name}: {score:,}点")
        
        display_data.append({
            '日付': record.get('date', ''),
            '時刻': record.get('time', ''),
            'タイプ': record.get('game_type', ''),
            '参加者': ' | '.join(players_info)
        })
    
    df = pd.DataFrame(display_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def screenshot_upload_tab():
    st.header("スクリーンショット解析")
    
    # フォーム送信後のクリア処理（最初にチェック）
    if st.session_state.get('clear_screenshot', False):
        st.session_state['clear_screenshot'] = False
        st.session_state['analysis_result'] = None
        # ファイルアップローダーをクリアするためにキーを変更
        if 'file_uploader_key' not in st.session_state:
            st.session_state['file_uploader_key'] = 0
        st.session_state['file_uploader_key'] += 1
        st.rerun()
    
    # ファイルアップローダーのキー
    uploader_key = st.session_state.get('file_uploader_key', 0)
    
    uploaded_file = st.file_uploader(
        "画像ファイルを選択",
        type=['png', 'jpg', 'jpeg'],
        key=f"file_uploader_{uploader_key}"
    )
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("アップロード画像")
            st.image(image, use_container_width=True)
            
            if st.button("解析開始", type="primary", use_container_width=True):
                extract_data_from_image(image)
                st.rerun()
        
        with col2:
            st.subheader("解析結果")
            
            if 'analysis_result' in st.session_state and st.session_state['analysis_result'] is not None:
                display_extraction_results()
            else:
                st.info("解析開始ボタンを押してください")
    
    if 'analysis_result' in st.session_state and st.session_state['analysis_result'] is not None:
        st.divider()
        create_extraction_form()

def create_extraction_form():
    # analysis_resultがNoneまたは存在しない場合は何も表示しない
    if ('analysis_result' not in st.session_state or 
        st.session_state['analysis_result'] is None):
        return
    
    result = st.session_state['analysis_result']
    
    # resultがNoneの場合も早期リターン
    if result is None or not result.get('success', False):
        return
    
    players = result.get('players', [])
    while len(players) < 4:
        players.append({'nickname': '', 'score': 25000})
    
    st.subheader("データ確認・修正")
    
    # フォーム送信後のクリア処理（削除）
    
    with st.form("extraction_form", clear_on_submit=True):
        # 解析結果のニックネームをデフォルト値として設定
        extracted_names = [player.get('nickname', '') for player in players]
        player_names = create_player_input_fields_with_defaults("extraction", extracted_names)
        
        # 解析結果をデフォルト値として使用
        default_scores = [int(player.get('score', 25000)) for player in players]
        scores = create_score_input_fields(player_names, default_scores, "extraction")
        
        game_date, game_time, game_type = create_game_info_fields("extraction")
        notes = st.text_area("メモ", placeholder="特記事項")
        
        st.subheader("入力内容確認")
        is_valid = show_input_confirmation(player_names, scores)
        
        submitted = st.form_submit_button("記録を保存", type="primary", use_container_width=True)
        
        if submitted and is_valid:
            if save_game_record(player_names, scores, game_date, game_time, game_type, notes):
                st.session_state['clear_screenshot'] = True
                st.rerun()

def manual_input_tab():
    st.header("手動データ入力")
    
    # フォーム送信後のクリア処理
    if st.session_state.get('manual_form_submitted', False):
        st.session_state['manual_form_submitted'] = False
        st.rerun()
    
    with st.form("manual_input_form", clear_on_submit=True):
        st.subheader("プレイヤー情報")
        player_names = create_player_input_fields("manual")
        
        st.subheader("点数入力")
        scores = create_score_input_fields(player_names, prefix="manual")
        
        st.subheader("対局情報")
        game_date, game_time, game_type = create_game_info_fields("manual")
        notes = st.text_area("メモ", placeholder="特記事項")
        
        st.subheader("入力内容確認")
        is_valid = show_input_confirmation(player_names, scores)
        
        submitted = st.form_submit_button("記録を保存", type="primary", use_container_width=True)
        
        if submitted and is_valid:
            if save_game_record(player_names, scores, game_date, game_time, game_type, notes):
                st.session_state['manual_form_submitted'] = True
                st.rerun()