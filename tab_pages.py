# tab_pages.py (完全版・絵文字なし)
import streamlit as st
import pandas as pd
from PIL import Image
from datetime import datetime, date
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
        from player_manager import PlayerManager
        player_manager = PlayerManager(st.session_state['game_records'])
        all_players = player_manager.get_all_player_names()
        
        # 基本統計情報
        st.subheader("基本統計")
        
        total_games = len(st.session_state['game_records'])
        total_players = len(all_players)
        
        # 最新の対局情報
        latest_game = st.session_state['game_records'][-1]
        latest_date = latest_game.get('date', '')
        
        # 最もアクティブなプレイヤー
        most_active_player = ""
        max_games = 0
        if all_players:
            for player in all_players:
                player_games = player_manager.get_player_statistics(player)['total_games']
                if player_games > max_games:
                    max_games = player_games
                    most_active_player = player
        
        # メトリクス表示
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("総対局数", f"{total_games}回")
        
        with col2:
            st.metric("参加プレイヤー数", f"{total_players}人")
        
        with col3:
            st.metric("最新対局日", latest_date)
        
        with col4:
            st.metric("最多対局者", most_active_player, f"{max_games}回")
        
        # データ操作メニュー
        st.divider()
        st.subheader("データ管理")
        
        btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
        
        with btn_col1:
            if st.button("データ表示", use_container_width=True):
                st.session_state['show_data'] = True
                st.rerun()
        
        with btn_col2:
            if st.button("基本統計", use_container_width=True):
                st.session_state['show_stats'] = True
                st.rerun()
        
        with btn_col3:
            if st.button("詳細統計", use_container_width=True):
                st.session_state['show_player_stats'] = True
                st.rerun()
        
        with btn_col4:
            # CSV出力ボタン
            df = pd.DataFrame(st.session_state['game_records'])
            csv_data = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="CSV出力",
                data=csv_data,
                file_name=f"mahjong_records_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # 最近の対局記録
        st.divider()
        st.subheader("最近の対局記録")
        
        col_count, col_filter = st.columns([1, 3])
        with col_count:
            display_count = st.selectbox(
                "表示件数",
                options=[5, 10, 20, 50],
                index=0
            )
        
        recent_records = st.session_state['game_records'][-display_count:]
        display_recent_records_enhanced(recent_records)
        
        # トッププレイヤー
        if total_players > 0:
            st.divider()
            st.subheader("トッププレイヤー")
            
            player_stats = []
            for player in all_players:
                stats = player_manager.get_player_statistics(player)
                if stats['total_games'] >= 3:
                    player_stats.append({
                        'プレイヤー': player,
                        '平均点数': stats['avg_score'],
                        '対局数': stats['total_games'],
                        '1位率': stats['win_rate']
                    })
            
            if player_stats:
                player_stats.sort(key=lambda x: x['平均点数'], reverse=True)
                top_players = player_stats[:5]
                
                top_cols = st.columns(min(len(top_players), 5))
                for i, (col, player_data) in enumerate(zip(top_cols, top_players)):
                    with col:
                        rank = i + 1
                        st.metric(
                            label=f"{rank}位: {player_data['プレイヤー']}",
                            value=f"{player_data['平均点数']:,.0f}点",
                            delta=f"1位率: {player_data['1位率']:.1f}%"
                        )
            else:
                st.info("3回以上対局したプレイヤーがいません")
    
    else:
        st.info("記録がありません。対局データを追加してください。")
        
        # クイックスタートガイド
        st.subheader("クイックスタート")
        
        quick_col1, quick_col2 = st.columns(2)
        
        with quick_col1:
            st.markdown("""
            **スクリーンショット解析**
            1. 「スクショ解析」タブを選択
            2. 画像をアップロード
            3. 解析結果を確認
            4. 記録を保存
            """)
        
        with quick_col2:
            st.markdown("""
            **手動入力**
            1. 「手動入力」タブを選択
            2. プレイヤー名と点数を入力
            3. 対局情報を設定
            4. 記録を保存
            """)
    
    # モーダル表示処理
    if st.session_state.get('show_data', False):
        show_data_modal()
    
    if st.session_state.get('show_stats', False):
        show_statistics_modal()
    
    if st.session_state.get('show_player_stats', False):
        show_player_statistics_modal()
        if st.button("統計を閉じる", use_container_width=True):
            st.session_state['show_player_stats'] = False
            st.rerun()

def display_recent_records_enhanced(records):
    """最近の記録表示"""
    if not records:
        st.info("表示する記録がありません")
        return
    
    display_data = []
    for i, record in enumerate(reversed(records)):
        players_info = []
        player_scores = []
        
        for j in range(1, 5):
            name_key = f'player{j}_name'
            score_key = f'player{j}_score'
            
            if name_key in record and score_key in record:
                name = record[name_key]
                score = record[score_key]
                
                if name and str(name).strip():
                    players_info.append({'name': name, 'score': score})
                    player_scores.append(score)
        
        # 順位付け
        if player_scores:
            sorted_scores = sorted(player_scores, reverse=True)
            player_ranks = []
            
            for player in players_info:
                rank = sorted_scores.index(player['score']) + 1
                player_ranks.append(f"{rank}位 {player['name']}: {player['score']:,}点")
            
            participants = " | ".join(player_ranks)
        else:
            participants = "参加者なし"
        
        display_data.append({
            '対局': f"#{len(records) - i}",
            '日付': record.get('date', ''),
            '時刻': record.get('time', ''),
            'タイプ': record.get('game_type', ''),
            '結果': participants
        })
    
    df = pd.DataFrame(display_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def screenshot_upload_tab():
    st.header("スクリーンショット解析")
    
    # ファイルアップローダーキーの管理
    if 'screenshot_uploader_key' not in st.session_state:
        st.session_state['screenshot_uploader_key'] = 0
    
    uploaded_file = st.file_uploader(
        "画像ファイルを選択",
        type=['png', 'jpg', 'jpeg'],
        key=f"screenshot_uploader_{st.session_state['screenshot_uploader_key']}"
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
    
    # 解析結果がある場合のみフォームを表示
    if 'analysis_result' in st.session_state and st.session_state['analysis_result'] is not None:
        result = st.session_state['analysis_result']
        if result.get('success', False):
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
    
    # 一意のフォームキーを使用
    form_key = f"extraction_form_{st.session_state.get('screenshot_uploader_key', 0)}"
    
    with st.form(form_key, clear_on_submit=False):
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
        
        col1, col2 = st.columns([3, 1])
        with col1:
            submitted = st.form_submit_button("記録を保存", type="primary", use_container_width=True)
        with col2:
            if st.form_submit_button("クリア", use_container_width=True):
                # フォームをクリア
                st.session_state['analysis_result'] = None
                st.session_state['screenshot_uploader_key'] += 1
                st.rerun()
        
        if submitted and is_valid:
            if save_game_record(player_names, scores, game_date, game_time, game_type, notes):
                st.success("記録を保存しました")
                # 成功後にフォームをクリア
                st.session_state['analysis_result'] = None
                st.session_state['screenshot_uploader_key'] += 1
                # rerunしない（ページ遷移を防ぐ）

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