# tab_pages.py
import streamlit as st
import pandas as pd
from PIL import Image
from datetime import date
from ui_components import (
    extract_data_from_image,
    display_extraction_results,
    create_extraction_form,
    create_manual_input_form
)
from data_modals import show_data_modal, show_statistics_modal

def home_tab():
    """ホームタブ - ダッシュボード"""
    st.header("麻雀点数管理システム ダッシュボード")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("システム概要")
        st.markdown("""
        このシステムでは以下の機能を提供しています：
        
        **主要機能:**
        - 雀魂スクリーンショットからの自動データ抽出
        - ニックネームと点数の同時認識
        - 手動データ入力機能
        - Google Sheets連携
        - 統計分析とグラフ表示
        
        **使用方法:**
        1. **スクショアップロード**: 雀魂の結果画面をアップロードして自動抽出
        2. **手動入力**: 直接データを入力
        3. **データ管理**: サイドバーから記録の確認・出力
        """)
        
        # 最近の対局記録表示
        if 'game_records' in st.session_state and st.session_state['game_records']:
            st.subheader("最近の対局記録")
            recent_records = st.session_state['game_records'][-5:]  # 最新5件
            df_recent = pd.DataFrame(recent_records)
            
            # 表示用に列を整理
            display_columns = ['date', 'time', 'game_type']
            name_columns = [col for col in df_recent.columns if 'name' in col]
            score_columns = [col for col in df_recent.columns if 'score' in col and 'name' not in col]
            
            if name_columns and score_columns:
                display_df = df_recent[display_columns + name_columns + score_columns]
                st.dataframe(display_df, use_container_width=True)
    
    with col2:
        st.subheader("クイックアクション")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("スクショ解析", type="primary", use_container_width=True):
                st.session_state['active_tab'] = 'スクショアップロード'
                st.rerun()
        
        with col_btn2:
            if st.button("手動入力", use_container_width=True):
                st.session_state['active_tab'] = '手動入力'
                st.rerun()
        
        # 統計サマリー
        if 'game_records' in st.session_state and st.session_state['game_records']:
            st.subheader("統計サマリー")
            
            df = pd.DataFrame(st.session_state['game_records'])
            st.metric("総対局数", len(df))
            
            # 最高点数
            max_score = 0
            max_player = ""
            for i in range(1, 5):
                score_col = f'player{i}_score'
                if score_col in df.columns:
                    scores = pd.to_numeric(df[score_col], errors='coerce')
                    max_val = scores.max()
                    if max_val > max_score:
                        max_score = max_val
                        name_col = f'player{i}_name'
                        if name_col in df.columns:
                            max_player = df.loc[scores.idxmax(), name_col]
            
            if max_score > 0:
                st.metric("最高得点", f"{max_score:,}点")
                if max_player:
                    st.write(f"記録者: {max_player}")
    
    # データ表示モーダル
    if st.session_state.get('show_data', False):
        show_data_modal()
    
    # 統計表示モーダル
    if st.session_state.get('show_stats', False):
        show_statistics_modal()

def screenshot_upload_tab():
    """スクリーンショットアップロードタブ"""
    st.header("スクリーンショットから自動抽出")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("画像アップロード")
        uploaded_file = st.file_uploader(
            "雀魂の対局結果画面をアップロード",
            type=['png', 'jpg', 'jpeg'],
            help="対局結果が表示された画面のスクリーンショットを選択してください"
        )
        
        if uploaded_file is not None:
            # 画像表示
            image = Image.open(uploaded_file)
            st.image(image, caption="アップロード画像", use_column_width=True)
            
            # OCR処理
            if st.button("ニックネームと点数を抽出", type="primary"):
                extract_data_from_image(image)
    
    with col2:
        st.subheader("抽出結果")
        
        if 'analysis_result' in st.session_state:
            display_extraction_results()
            
            # 抽出データの確認・修正フォーム
            st.subheader("データ確認・修正")
            create_extraction_form()

def manual_input_tab():
    """手動入力タブ"""
    st.header("手動データ入力")
    
    st.markdown("対局データを直接入力できます")
    
    create_manual_input_form()