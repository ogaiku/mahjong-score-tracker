# ui_components.py
import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import json
from datetime import datetime, date
from score_extractor import MahjongScoreExtractor
from spreadsheet_manager import SpreadsheetManager

def setup_sidebar():
    """サイドバーの設定 - シンプルなデザイン"""
    st.sidebar.title("設定")
    
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
    
    # Google Sheets連携
    st.sidebar.subheader("Google Sheets連携")
    
    with st.sidebar.expander("設定"):
        credentials_file = st.file_uploader(
            "認証情報ファイル", 
            type=['json']
        )
        
        spreadsheet_id = st.text_input(
            "スプレッドシートID",
            placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        )
        
        if credentials_file and spreadsheet_id:
            try:
                credentials_dict = json.load(credentials_file)
                st.session_state['credentials'] = credentials_dict
                st.session_state['spreadsheet_id'] = spreadsheet_id
                st.success("設定完了")
            except Exception as e:
                st.error(f"設定エラー: {e}")

def extract_data_from_image(image):
    """画像からニックネームと点数を抽出"""
    with st.spinner("解析中..."):
        extractor = MahjongScoreExtractor()
        image_array = np.array(image)
        result = extractor.analyze_image(image_array)
        st.session_state['analysis_result'] = result

def display_extraction_results():
    """抽出結果をシンプルに表示"""
    result = st.session_state['analysis_result']
    
    # 成功メッセージ
    st.success("データ抽出完了")
    
    # 結果を2列で表示
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("抽出されたニックネーム")
        nicknames = result['nicknames']
        if nicknames:
            for nickname in nicknames:
                st.text(nickname)
        else:
            st.warning("ニックネームが見つかりませんでした")
    
    with col2:
        st.subheader("抽出された点数")
        scores = result['scores']
        if scores:
            for score in scores:
                st.text(f"{score:,}点")
        else:
            st.warning("点数が見つかりませんでした")
    
    # 詳細は折りたたみで表示
    with st.expander("抽出テキスト詳細"):
        st.text(result['extracted_text'])

def create_extraction_form():
    """抽出データの確認・修正フォーム - シンプルデザイン"""
    result = st.session_state['analysis_result']
    nicknames = result.get('nicknames', [])
    scores = result.get('scores', [])
    
    st.subheader("データ確認・修正")
    
    with st.form("extraction_form"):
        # プレイヤー情報を4列で表示
        col1, col2, col3, col4 = st.columns(4)
        
        players_data = []
        
        with col1:
            st.caption("プレイヤー1")
            name1 = st.text_input("名前", value=nicknames[0] if len(nicknames) > 0 else "", key="name1", label_visibility="collapsed")
            score1 = st.number_input("点数", value=scores[0] if len(scores) > 0 else 25000, key="score1", label_visibility="collapsed")
            players_data.append({"name": name1, "score": score1})
        
        with col2:
            st.caption("プレイヤー2")
            name2 = st.text_input("名前", value=nicknames[1] if len(nicknames) > 1 else "", key="name2", label_visibility="collapsed")
            score2 = st.number_input("点数", value=scores[1] if len(scores) > 1 else 25000, key="score2", label_visibility="collapsed")
            players_data.append({"name": name2, "score": score2})
        
        with col3:
            st.caption("プレイヤー3")
            name3 = st.text_input("名前", value=nicknames[2] if len(nicknames) > 2 else "", key="name3", label_visibility="collapsed")
            score3 = st.number_input("点数", value=scores[2] if len(scores) > 2 else 25000, key="score3", label_visibility="collapsed")
            players_data.append({"name": name3, "score": score3})
        
        with col4:
            st.caption("プレイヤー4")
            name4 = st.text_input("名前", value=nicknames[3] if len(nicknames) > 3 else "", key="name4", label_visibility="collapsed")
            score4 = st.number_input("点数", value=scores[3] if len(scores) > 3 else 25000, key="score4", label_visibility="collapsed")
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
        
        # 保存ボタン
        submitted = st.form_submit_button("記録を保存", type="primary", use_container_width=True)
        
        if submitted:
            save_game_record_with_names(players_data, game_date, game_time, game_type, notes)

def create_manual_input_form():
    """手動入力フォーム - シンプルデザイン"""
    st.subheader("対局データ入力")
    
    with st.form("manual_input_form"):
        # プレイヤー情報
        col1, col2, col3, col4 = st.columns(4)
        
        players_data = []
        
        with col1:
            st.caption("プレイヤー1")
            name1 = st.text_input("名前", key="manual_name1", label_visibility="collapsed", placeholder="ニックネーム")
            score1 = st.number_input("点数", min_value=-100000, max_value=200000, value=25000, key="manual_score1", label_visibility="collapsed")
            players_data.append({"name": name1, "score": score1})
        
        with col2:
            st.caption("プレイヤー2")
            name2 = st.text_input("名前", key="manual_name2", label_visibility="collapsed", placeholder="ニックネーム")
            score2 = st.number_input("点数", min_value=-100000, max_value=200000, value=25000, key="manual_score2", label_visibility="collapsed")
            players_data.append({"name": name2, "score": score2})
        
        with col3:
            st.caption("プレイヤー3")
            name3 = st.text_input("名前", key="manual_name3", label_visibility="collapsed", placeholder="ニックネーム")
            score3 = st.number_input("点数", min_value=-100000, max_value=200000, value=25000, key="manual_score3", label_visibility="collapsed")
            players_data.append({"name": name3, "score": score3})
        
        with col4:
            st.caption("プレイヤー4")
            name4 = st.text_input("名前", key="manual_name4", label_visibility="collapsed", placeholder="ニックネーム")
            score4 = st.number_input("点数", min_value=-100000, max_value=200000, value=25000, key="manual_score4", label_visibility="collapsed")
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
    
    # Google Sheets保存
    if 'credentials' in st.session_state and 'spreadsheet_id' in st.session_state:
        try:
            sheet_manager = SpreadsheetManager(st.session_state['credentials'])
            if sheet_manager.connect(st.session_state['spreadsheet_id']):
                if sheet_manager.add_record(game_data):
                    st.info("Google Sheetsにも保存しました")
        except Exception as e:
            st.warning(f"Google Sheets保存に失敗: {e}")

def display_simple_table(data, title="データ"):
    """シンプルなテーブル表示"""
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