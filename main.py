# main.py
import streamlit as st
from ui_components import setup_sidebar
from tab_pages import home_tab, screenshot_upload_tab, manual_input_tab

# ページ設定
st.set_page_config(
    page_title="麻雀点数管理システム",
    layout="wide"
)

def main():
    st.title("麻雀点数管理システム")
    st.markdown("雀魂のスクリーンショットからニックネームと点数を抽出し、データを管理・分析")
    
    # サイドバー設定
    setup_sidebar()
    
    # セッション状態の初期化
    if 'active_tab' not in st.session_state:
        st.session_state['active_tab'] = 'ホーム'
    
    # メインコンテンツ - 3つのタブ
    tab1, tab2, tab3 = st.tabs(["ホーム", "スクショアップロード", "手動入力"])
    
    # アクティブタブの設定
    if st.session_state.get('active_tab') == 'スクショアップロード':
        tab2.empty()
        with tab2:
            screenshot_upload_tab()
    elif st.session_state.get('active_tab') == '手動入力':
        tab3.empty()
        with tab3:
            manual_input_tab()
    else:
        with tab1:
            home_tab()
        
        with tab2:
            screenshot_upload_tab()
        
        with tab3:
            manual_input_tab()

if __name__ == "__main__":
    main()