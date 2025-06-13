# tab_pages.py (simplified)
import streamlit as st
import pandas as pd
from PIL import Image
from datetime import date
from input_forms import (
    create_player_input_fields, 
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
    
    uploaded_file = st.file_uploader(
        "画像ファイルを選択",
        type=['png', 'jpg', 'jpeg']
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
            
            if 'analysis_result' in st.session_state:
                display_extraction_results()
            else:
                st.info("解析開始ボタンを押してください")
    
    if 'analysis_result' in st.session_state:
        st.divider()
        create_extraction_form()

def create_extraction_form():
    result = st.session_state['analysis_result']
    
    if not result.get('success', False):
        st.warning("解析結果がありません")
        return
    
    players = result.get('players', [])
    while len(players) < 4:
        players.append({'nickname': '', 'score': 25000})
    
    st.subheader("データ確認・修正")
    
    with st.form("extraction_form"):
        player_names = create_player_input_fields()
        
        # 解析結果をデフォルト値として使用
        default_scores = [int(player.get('score', 25000)) for player in players]
        scores = create_score_input_fields(player_names, default_scores)
        
        game_date, game_time, game_type = create_game_info_fields()
        notes = st.text_area("メモ", placeholder="特記事項")
        
        st.subheader("入力内容確認")
        is_valid = show_input_confirmation(player_names, scores)
        
        confidence = result.get('confidence', 0.0)
        if confidence < 0.8:
            st.warning(f"解析信頼度: {confidence:.0%} - データを確認してください")
        
        submitted = st.form_submit_button("記録を保存", type="primary", use_container_width=True)
        
        if submitted and is_valid:
            save_game_record(player_names, scores, game_date, game_time, game_type, notes)

def manual_input_tab():
    st.header("手動データ入力")
    
    with st.form("manual_input_form"):
        st.subheader("プレイヤー情報")
        player_names = create_player_input_fields()
        
        st.subheader("点数入力")
        scores = create_score_input_fields(player_names)
        
        st.subheader("対局情報")
        game_date, game_time, game_type = create_game_info_fields()
        notes = st.text_area("メモ", placeholder="特記事項")
        
        st.subheader("入力内容確認")
        is_valid = show_input_confirmation(player_names, scores)
        
        submitted = st.form_submit_button("記録を保存", type="primary", use_container_width=True)
        
        if submitted and is_valid:
            save_game_record(player_names, scores, game_date, game_time, game_type, notes)

def quick_entry_tab():
    st.header("クイック入力")
    
    if 'game_records' not in st.session_state or not st.session_state['game_records']:
        st.info("過去の記録がないため、まず手動入力で記録を作成してください")
        return
    
    from player_manager import PlayerManager
    player_manager = PlayerManager(st.session_state['game_records'])
    
    # よく一緒に対局するメンバー組み合わせを取得
    all_players = player_manager.get_all_player_names()
    
    if len(all_players) < 2:
        st.info("クイック入力を使用するには複数のプレイヤーが必要です")
        return
    
    with st.form("quick_entry_form"):
        st.subheader("メンバー選択")
        selected_players = st.multiselect(
            "参加プレイヤーを選択",
            all_players,
            max_selections=4
        )
        
        if selected_players:
            st.subheader("点数入力")
            cols = st.columns(len(selected_players))
            scores = []
            
            for i, (col, player) in enumerate(zip(cols, selected_players)):
                with col:
                    st.caption(player)
                    score = st.number_input(
                        "点数",
                        min_value=-100000,
                        max_value=200000,
                        value=25000,
                        step=100,
                        key=f"quick_score_{i}",
                        label_visibility="collapsed"
                    )
                    scores.append(score)
            
            # 対局情報
            col1, col2 = st.columns(2)
            with col1:
                game_date = st.date_input("対局日", value=date.today())
            with col2:
                game_type = st.selectbox("対局タイプ", ["四麻東風", "四麻半荘", "三麻東風", "三麻半荘"])
            
            notes = st.text_input("メモ")
            
            # 順位プレビュー
            if selected_players and scores:
                st.subheader("順位プレビュー")
                sorted_players = sorted(zip(selected_players, scores), key=lambda x: x[1], reverse=True)
                rank_data = []
                for rank, (name, score) in enumerate(sorted_players, 1):
                    rank_data.append({
                        "順位": f"{rank}位",
                        "プレイヤー": name,
                        "点数": f"{score:,}点"
                    })
                
                rank_df = pd.DataFrame(rank_data)
                st.dataframe(rank_df, hide_index=True, use_container_width=True)
        
        submitted = st.form_submit_button("高速保存", type="primary", use_container_width=True)
        
        if submitted and selected_players:
            from datetime import datetime
            current_time = datetime.now().time()
            
            # プレイヤーデータを4人分に調整
            player_names = selected_players + [''] * (4 - len(selected_players))
            all_scores = scores + [25000] * (4 - len(scores))
            
            save_game_record(player_names, all_scores, game_date, current_time, game_type, notes)