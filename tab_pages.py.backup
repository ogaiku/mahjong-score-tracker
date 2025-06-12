# tab_pages.py
import streamlit as st
import pandas as pd
from PIL import Image
from datetime import date
from ui_components import (
    extract_data_from_image,
    display_extraction_results,
    create_extraction_form,
    create_manual_input_form,
    display_simple_table,
    create_clean_metrics
)
from data_modals import show_data_modal, show_statistics_modal

def home_tab():
    """ホームタブ - 情報表示用"""
    st.header("ダッシュボード")
    
    # 統計サマリー
    if 'game_records' in st.session_state and st.session_state['game_records']:
        st.subheader("統計サマリー")
        
        df = pd.DataFrame(st.session_state['game_records'])
        
        # 基本統計の計算
        stats = {
            'total_games': len(df),
            'avg_scores': {}
        }
        
        for i in range(1, 5):
            score_col = f'player{i}_score'
            if score_col in df.columns:
                scores = pd.to_numeric(df[score_col], errors='coerce')
                stats['avg_scores'][f'player{i}'] = scores.mean()
        
        create_clean_metrics(stats)
        
        # 最近の記録
        st.subheader("最近の対局記録")
        recent_records = st.session_state['game_records'][-5:]  # 最新5件
        display_simple_table(recent_records, "")
        
    else:
        st.info("まだ記録がありません。上記のボタンから対局データを追加してください。")
    
    # モーダル表示
    if st.session_state.get('show_data', False):
        show_data_modal()
    
    if st.session_state.get('show_stats', False):
        show_statistics_modal()

def screenshot_upload_tab():
    """スクリーンショットアップロードタブ - シンプルデザイン"""
    st.header("スクリーンショット解析")
    
    # 画像アップロード
    uploaded_file = st.file_uploader(
        "画像ファイルを選択",
        type=['png', 'jpg', 'jpeg']
    )
    
    if uploaded_file is not None:
        # 画像表示
        image = Image.open(uploaded_file)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("アップロード画像")
            st.image(image, use_column_width=True)
            
            # 解析ボタン
            if st.button("解析開始", type="primary", use_container_width=True, key="screenshot_analyze_btn"):
                extract_data_from_image(image)
                st.rerun()
        
        with col2:
            st.subheader("解析結果")
            
            if 'analysis_result' in st.session_state:
                display_extraction_results()
            else:
                st.info("「解析開始」ボタンを押してください")
    
    # データ確認・修正フォーム
    if 'analysis_result' in st.session_state:
        st.divider()
        create_extraction_form()

def manual_input_tab():
    """手動入力タブ - シンプルデザイン"""
    st.header("手動データ入力")
    
    create_manual_input_form()