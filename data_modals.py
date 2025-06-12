# data_modals.py
import streamlit as st
import pandas as pd
from data_analyzer import MahjongDataAnalyzer

def show_data_modal():
    """データ表示モーダル - シンプルデザイン"""
    st.subheader("保存済み対局記録")
    
    if 'game_records' in st.session_state and st.session_state['game_records']:
        df = pd.DataFrame(st.session_state['game_records'])
        
        # 表示用にデータを整理
        display_df = df.copy()
        
        # 列名を日本語に変更
        column_mapping = {
            'date': '対局日',
            'time': '時刻',
            'game_type': 'タイプ',
            'player1_name': 'P1名前',
            'player1_score': 'P1点数',
            'player2_name': 'P2名前',
            'player2_score': 'P2点数',
            'player3_name': 'P3名前',
            'player3_score': 'P3点数',
            'player4_name': 'P4名前',
            'player4_score': 'P4点数',
            'notes': 'メモ'
        }
        
        display_df = display_df.rename(columns=column_mapping)
        
        # 不要な列を除外
        if 'timestamp' in display_df.columns:
            display_df = display_df.drop('timestamp', axis=1)
        
        # データ表示
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # ボタン
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("閉じる", use_container_width=True, key="close_data_modal_btn"):
                st.session_state['show_data'] = False
                st.rerun()
        
        with col2:
            if st.button("全削除", type="secondary", use_container_width=True, key="delete_all_data_btn"):
                if 'delete_confirm' not in st.session_state:
                    st.session_state['delete_confirm'] = False
                
                if not st.session_state['delete_confirm']:
                    st.session_state['delete_confirm'] = True
                    st.rerun()
                else:
                    del st.session_state['game_records']
                    st.session_state['show_data'] = False
                    st.session_state['delete_confirm'] = False
                    st.success("全記録を削除しました")
                    st.rerun()
        
        with col3:
            if st.session_state.get('delete_confirm', False):
                st.warning("もう一度「全削除」ボタンを押してください")
        
    else:
        st.info("表示する記録がありません")
        if st.button("閉じる", key="close_empty_data_modal_btn"):
            st.session_state['show_data'] = False
            st.rerun()

def show_statistics_modal():
    """統計表示モーダル - シンプルデザイン"""
    st.subheader("統計分析")
    
    if 'game_records' in st.session_state and st.session_state['game_records']:
        analyzer = MahjongDataAnalyzer(st.session_state['game_records'])
        
        # 基本統計
        stats = analyzer.calculate_basic_stats()
        
        # メトリクス表示
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("総対局数", f"{stats.get('total_games', 0)}回")
        
        # 各プレイヤーの平均点数
        if 'avg_scores' in stats:
            avg_scores = stats['avg_scores']
            player_metrics = [
                ('P1平均', avg_scores.get('player1', 0)),
                ('P2平均', avg_scores.get('player2', 0)),
                ('P3平均', avg_scores.get('player3', 0))
            ]
            
            for i, (label, value) in enumerate(player_metrics):
                with [col2, col3, col4][i]:
                    st.metric(label, f"{value:,.0f}点")
        
        # グラフ表示
        tab1, tab2, tab3 = st.tabs(["点数推移", "平均点数比較", "順位分布"])
        
        with tab1:
            trend_chart = analyzer.create_score_trend_chart()
            if trend_chart.data:
                st.plotly_chart(trend_chart, use_container_width=True)
            else:
                st.info("グラフを表示するデータがありません")
        
        with tab2:
            avg_chart = analyzer.create_average_score_chart()
            if avg_chart.data:
                st.plotly_chart(avg_chart, use_container_width=True)
            else:
                st.info("グラフを表示するデータがありません")
        
        with tab3:
            rank_chart = analyzer.create_rank_distribution_chart()
            if rank_chart.data:
                st.plotly_chart(rank_chart, use_container_width=True)
            else:
                st.info("グラフを表示するデータがありません")
        
        # プレイヤー別詳細統計
        st.subheader("プレイヤー別詳細統計")
        
        df = pd.DataFrame(st.session_state['game_records'])
        player_stats = []
        
        for i in range(1, 5):
            name_col = f'player{i}_name'
            score_col = f'player{i}_score'
            
            if name_col in df.columns and score_col in df.columns:
                names = df[name_col].dropna()
                scores = pd.to_numeric(df[score_col], errors='coerce')
                
                # 最も多く使われている名前を取得
                if not names.empty:
                    most_common_name = names.mode().iloc[0] if len(names.mode()) > 0 else f"プレイヤー{i}"
                else:
                    most_common_name = f"プレイヤー{i}"
                
                if not scores.empty:
                    player_stats.append({
                        'プレイヤー': most_common_name,
                        '平均点数': f"{scores.mean():,.0f}点",
                        '最高点数': f"{scores.max():,.0f}点",
                        '最低点数': f"{scores.min():,.0f}点",
                        '対局数': f"{len(scores.dropna())}回"
                    })
        
        if player_stats:
            stats_df = pd.DataFrame(player_stats)
            st.dataframe(stats_df, use_container_width=True, hide_index=True)
        else:
            st.info("統計データがありません")
        
        # 閉じるボタン
        if st.button("統計表示を閉じる", use_container_width=True, key="close_stats_modal_btn"):
            st.session_state['show_stats'] = False
            st.rerun()
    
    else:
        st.info("統計を表示するデータがありません")
        if st.button("統計表示を閉じる", key="close_empty_stats_modal_btn"):
            st.session_state['show_stats'] = False
            st.rerun()