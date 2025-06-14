# tab_pages.py - 完全版（不要な警告メッセージのみ削除）
import streamlit as st
import pandas as pd
from PIL import Image
from datetime import datetime, date
from input_forms import (
    create_player_input_fields_simple,
    create_player_input_fields_with_registration,
    create_score_input_fields,
    create_game_info_fields,
    show_input_confirmation,
    save_game_record,
    show_player_management
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
                        '合計スコア': stats['total_score'],
                        '対局数': stats['total_games'],
                        '1位率': stats['win_rate']
                    })
            
            if player_stats:
                player_stats.sort(key=lambda x: x['合計スコア'], reverse=True)
                top_players = player_stats[:5]
                
                top_cols = st.columns(min(len(top_players), 5))
                for i, (col, player_data) in enumerate(zip(top_cols, top_players)):
                    with col:
                        rank = i + 1
                        st.metric(
                            label=f"{rank}位: {player_data['プレイヤー']}",
                            value=f"{player_data['合計スコア']:+.1f}pt",
                            delta=f"1位率: {player_data['1位率']:.1f}%"
                        )
            else:
                st.info("3回以上対局したプレイヤーがいません")
            
            # スコア計算の説明を追加
            with st.expander("スコア計算について"):
                from scoring_config import SCORING_EXPLANATION
                st.markdown(f"""
                **計算式**: {SCORING_EXPLANATION['formula']}
                
                **詳細**:
                - {SCORING_EXPLANATION['uma_4_player']}
                - {SCORING_EXPLANATION['uma_3_player']}
                - {SCORING_EXPLANATION['participation']}
                - {SCORING_EXPLANATION['starting_points']}
                """)
        
        # データ操作メニュー
        st.divider()
        st.subheader("データ管理")
        
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        
        with btn_col1:
            if st.button("データ表示", use_container_width=True):
                st.session_state['show_data'] = True
                st.rerun()
        
        with btn_col2:
            if st.button("詳細統計", use_container_width=True):
                st.session_state['show_player_stats'] = True
                st.rerun()
        
        with btn_col3:
            # CSV出力ボタン
            df = pd.DataFrame(st.session_state['game_records'])
            csv_data = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="CSV出力",
                data=csv_data,
                file_name=f"mahjong_records_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="home_csv_download"
            )
    
    else:
        st.info("記録がありません。スクリーンショット解析または手動入力で対局データを追加してください。")
        
        # クイックスタートガイド
        st.subheader("始め方")
        
        st.markdown("""
        1. **スクリーンショット解析**または**手動入力**で対局記録を追加
        2. プレイヤー名は初回入力時に自動登録されます
        3. 統計データの確認
        """)
    
    # モーダル表示処理
    if st.session_state.get('show_data', False):
        show_data_modal()
    
    if st.session_state.get('show_player_stats', False):
        show_player_statistics_modal()
        if st.button("統計を閉じる", use_container_width=True):
            st.session_state['show_player_stats'] = False
            st.rerun()

def screenshot_upload_tab():
    st.header("スクリーンショット解析")
    
    # ファイルアップローダーキーの管理
    if 'screenshot_uploader_key' not in st.session_state:
        st.session_state['screenshot_uploader_key'] = 0
    
    uploaded_file = st.file_uploader(
        "雀魂のスクリーンショットを選択",
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
            pass
    
    # 解析結果がある場合のみフォームを表示
    if 'analysis_result' in st.session_state and st.session_state['analysis_result'] is not None:
        result = st.session_state['analysis_result']
        if result.get('success', False):
            st.divider()
            create_extraction_form()

def create_extraction_form():
    if ('analysis_result' not in st.session_state or 
        st.session_state['analysis_result'] is None):
        return
    
    result = st.session_state['analysis_result']
    
    if result is None or not result.get('success', False):
        return
    
    players = result.get('players', [])
    while len(players) < 4:
        players.append({'nickname': '', 'score': 25000})
    
    st.subheader("解析結果の確認・修正")
    
    # 一意のフォームキーを使用
    form_key = f"extraction_form_{st.session_state.get('screenshot_uploader_key', 0)}"
    
    with st.form(form_key, clear_on_submit=False):
        st.subheader("プレイヤー選択")
        # 解析結果をデフォルト値として設定
        extracted_names = [player.get('nickname', '') for player in players]
        player_names = create_player_input_fields_with_registration("extraction", extracted_names)
        
        st.subheader("点数確認")
        default_scores = [int(player.get('score', 25000)) for player in players]
        scores = create_score_input_fields(player_names, default_scores, "extraction")
        
        st.subheader("対局情報")
        game_date, game_time, game_type = create_game_info_fields("extraction")
        notes = st.text_area("メモ", placeholder="特記事項があれば入力")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            submitted = st.form_submit_button("記録を保存", type="primary", use_container_width=True)
        with col2:
            clear_clicked = st.form_submit_button("クリア", use_container_width=True)
        
        if clear_clicked:
            st.session_state['analysis_result'] = None
            st.session_state['screenshot_uploader_key'] += 1
            st.rerun()
        
        if submitted:
            # 新規プレイヤーがある場合は自動登録
            if 'pending_new_players' in st.session_state:
                for new_player in st.session_state['pending_new_players']:
                    if new_player.strip():
                        from input_forms import register_new_player
                        register_new_player(new_player.strip())
                # 登録後にpending_new_playersをクリア
                del st.session_state['pending_new_players']
            
            valid_players = [name for name in player_names if name.strip()]
            if len(valid_players) >= 1:
                if save_game_record(player_names, scores, game_date, game_time, game_type, notes):
                    st.session_state['analysis_result'] = None
                    st.session_state['screenshot_uploader_key'] += 1
                    st.rerun()
            else:
                st.error("少なくとも1名のプレイヤーを選択してください")

def manual_input_tab():
    st.header("手動データ入力")
    
    # プレイヤー登録状況をチェック
    from input_forms import get_registered_players
    existing_players = get_registered_players()
    
    with st.form("manual_input_form", clear_on_submit=True):
        st.subheader("プレイヤー選択")
        # 既存プレイヤーがいる場合は選択フィールド、いない場合は登録機能付きフィールド
        if existing_players:
            player_names = create_player_input_fields_simple("manual")
        else:
            # プレイヤーが未登録の場合は手動入力フィールドを表示
            player_names = create_manual_player_input_fields("manual")
        
        st.subheader("点数入力")
        scores = create_score_input_fields(player_names, prefix="manual")
        
        st.subheader("対局情報")
        game_date, game_time, game_type = create_game_info_fields("manual")
        notes = st.text_area("メモ", placeholder="特記事項があれば入力")
        
        submitted = st.form_submit_button("記録を保存", type="primary", use_container_width=True)
        
        if submitted:
            # 新規プレイヤーがある場合は自動登録
            if 'pending_new_players' in st.session_state:
                for new_player in st.session_state['pending_new_players']:
                    if new_player.strip():
                        from input_forms import register_new_player
                        register_new_player(new_player.strip())
                # 登録後にpending_new_playersをクリア
                del st.session_state['pending_new_players']
            
            # プレイヤー名の入力チェック
            valid_players = [name for name in player_names if name.strip()]
            if len(valid_players) >= 1:
                # 新しいプレイヤー名があれば自動登録
                register_new_players_if_needed(player_names)
                
                if save_game_record(player_names, scores, game_date, game_time, game_type, notes):
                    st.rerun()
            else:
                st.error("少なくとも1名のプレイヤーを入力してください")

def create_manual_player_input_fields(prefix="default"):
    """手動プレイヤー入力フィールド（プレイヤー未登録時用）"""
    cols = st.columns(4)
    player_names = []
    
    for i, col in enumerate(cols):
        with col:
            player_name = st.text_input(
                f"プレイヤー{i+1}",
                placeholder="プレイヤー名を入力",
                key=f"{prefix}_manual_player_{i}",
                label_visibility="collapsed"
            )
            player_names.append(player_name)
    
    return player_names

def register_new_players_if_needed(player_names):
    """新しいプレイヤー名があれば自動登録"""
    from input_forms import get_registered_players, register_new_player
    
    existing_players = get_registered_players()
    
    for name in player_names:
        if name.strip() and name.strip() not in existing_players:
            try:
                # プレイヤーを自動登録（エラーメッセージは表示しない）
                register_new_player(name.strip())
            except:
                # 登録に失敗してもプロセスを継続
                pass

def player_management_tab():
    """プレイヤー管理タブ"""
    st.header("プレイヤー管理")
    show_player_management()