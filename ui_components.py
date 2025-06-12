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
    """サイドバーの設定"""
    st.sidebar.header("設定")
    
    # データ管理セクション
    with st.sidebar.expander("データ管理"):
        if st.button("データを表示"):
            st.session_state['show_data'] = True
        
        if st.button("統計を表示"):
            st.session_state['show_stats'] = True
        
        if 'game_records' in st.session_state and st.session_state['game_records']:
            st.metric("保存済み記録数", len(st.session_state['game_records']))
            
            # CSV出力
            df = pd.DataFrame(st.session_state['game_records'])
            csv_data = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="CSVダウンロード",
                data=csv_data,
                file_name=f"mahjong_records_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("まだ記録がありません")
    
    # Google Sheets設定
    with st.sidebar.expander("Google Sheets連携"):
        st.info("Google Sheets APIの認証情報（JSON）が必要です")
        
        credentials_file = st.file_uploader(
            "認証情報ファイル", 
            type=['json'],
            help="Google Cloud Consoleで作成したサービスアカウントのJSONファイル"
        )
        
        spreadsheet_id = st.text_input(
            "スプレッドシートID",
            help="GoogleスプレッドシートのURLに含まれているID"
        )
        
        # セッションステートに保存
        if credentials_file and spreadsheet_id:
            try:
                credentials_dict = json.load(credentials_file)
                st.session_state['credentials'] = credentials_dict
                st.session_state['spreadsheet_id'] = spreadsheet_id
                st.success("Google Sheets設定完了")
            except Exception as e:
                st.error(f"認証情報読み込みエラー: {e}")

def extract_data_from_image(image):
    """画像からニックネームと点数を抽出"""
    with st.spinner("画像を解析中..."):
        extractor = MahjongScoreExtractor()
        
        # PIL ImageをOpenCV形式に変換
        image_array = np.array(image)
        
        # 画像解析実行
        result = extractor.analyze_image(image_array)
        
        # セッションステートに保存
        st.session_state['analysis_result'] = result

def display_extraction_results():
    """抽出結果を表示"""
    result = st.session_state['analysis_result']
    
    st.success("データ抽出完了")
    
    # 抽出されたテキスト表示
    with st.expander("抽出されたテキスト"):
        st.text(result['extracted_text'])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**抽出されたニックネーム:**")
        nicknames = result['nicknames']
        if nicknames:
            for i, nickname in enumerate(nicknames):
                st.write(f"{i+1}. {nickname}")
        else:
            st.warning("ニックネームが抽出できませんでした")
    
    with col2:
        st.write("**抽出された点数:**")
        scores = result['scores']
        if scores:
            for i, score in enumerate(scores):
                st.write(f"{i+1}. {score:,}点")
        else:
            st.warning("点数が抽出できませんでした")

def create_extraction_form():
    """抽出データの確認・修正フォーム"""
    result = st.session_state['analysis_result']
    nicknames = result.get('nicknames', [])
    scores = result.get('scores', [])
    
    with st.form("extraction_form"):
        st.write("**抽出データを確認・修正してください:**")
        
        col1, col2, col3, col4 = st.columns(4)
        
        players_data = []
        
        with col1:
            st.write("**プレイヤー1**")
            name1 = st.text_input("ニックネーム", value=nicknames[0] if len(nicknames) > 0 else "", key="name1")
            score1 = st.number_input("点数", value=scores[0] if len(scores) > 0 else 25000, key="score1")
            players_data.append({"name": name1, "score": score1})
        
        with col2:
            st.write("**プレイヤー2**")
            name2 = st.text_input("ニックネーム", value=nicknames[1] if len(nicknames) > 1 else "", key="name2")
            score2 = st.number_input("点数", value=scores[1] if len(scores) > 1 else 25000, key="score2")
            players_data.append({"name": name2, "score": score2})
        
        with col3:
            st.write("**プレイヤー3**")
            name3 = st.text_input("ニックネーム", value=nicknames[2] if len(nicknames) > 2 else "", key="name3")
            score3 = st.number_input("点数", value=scores[2] if len(scores) > 2 else 25000, key="score3")
            players_data.append({"name": name3, "score": score3})
        
        with col4:
            st.write("**プレイヤー4**")
            name4 = st.text_input("ニックネーム", value=nicknames[3] if len(nicknames) > 3 else "", key="name4")
            score4 = st.number_input("点数", value=scores[3] if len(scores) > 3 else 25000, key="score4")
            players_data.append({"name": name4, "score": score4})
        
        game_date = st.date_input("対局日", value=date.today())
        game_time = st.time_input("対局時刻")
        game_type = st.selectbox("対局タイプ", ["四麻東風", "四麻半荘", "三麻東風", "三麻半荘"])
        notes = st.text_area("メモ", placeholder="特記事項があれば記入")
        
        submitted = st.form_submit_button("記録を保存", type="primary")
        
        if submitted:
            save_game_record_with_names(players_data, game_date, game_time, game_type, notes)

def create_manual_input_form():
    """手動入力フォーム"""
    with st.form("manual_input_form"):
        st.subheader("対局情報入力")
        
        col1, col2, col3, col4 = st.columns(4)
        
        players_data = []
        
        with col1:
            st.write("**プレイヤー1**")
            name1 = st.text_input("ニックネーム", key="manual_name1")
            score1 = st.number_input("点数", min_value=-100000, max_value=200000, value=25000, key="manual_score1")
            players_data.append({"name": name1, "score": score1})
        
        with col2:
            st.write("**プレイヤー2**")
            name2 = st.text_input("ニックネーム", key="manual_name2")
            score2 = st.number_input("点数", min_value=-100000, max_value=200000, value=25000, key="manual_score2")
            players_data.append({"name": name2, "score": score2})
        
        with col3:
            st.write("**プレイヤー3**")
            name3 = st.text_input("ニックネーム", key="manual_name3")
            score3 = st.number_input("点数", min_value=-100000, max_value=200000, value=25000, key="manual_score3")
            players_data.append({"name": name3, "score": score3})
        
        with col4:
            st.write("**プレイヤー4**")
            name4 = st.text_input("ニックネーム", key="manual_name4")
            score4 = st.number_input("点数", min_value=-100000, max_value=200000, value=25000, key="manual_score4")
            players_data.append({"name": name4, "score": score4})
        
        col_date, col_time, col_type = st.columns(3)
        
        with col_date:
            game_date = st.date_input("対局日", value=date.today())
        
        with col_time:
            game_time = st.time_input("対局時刻")
        
        with col_type:
            game_type = st.selectbox("対局タイプ", ["四麻東風", "四麻半荘", "三麻東風", "三麻半荘"])
        
        notes = st.text_area("メモ", placeholder="特記事項があれば記入")
        
        submitted = st.form_submit_button("記録を保存", type="primary")
        
        if submitted:
            save_game_record_with_names(players_data, game_date, game_time, game_type, notes)

def save_game_record_with_names(players_data, game_date, game_time, game_type, notes):
    """ニックネーム付きで対局記録を保存"""
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
                    st.success("Google Sheetsに記録しました")
        except Exception as e:
            st.error(f"Google Sheets保存エラー: {e}")