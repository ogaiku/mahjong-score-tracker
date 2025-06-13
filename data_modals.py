# data_modals.py
import streamlit as st
import pandas as pd
from player_manager import PlayerManager

def show_data_modal():
    """データ表示モーダル"""
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
    """統計表示モーダル"""
    st.subheader("統計分析")
    
    if 'game_records' in st.session_state and st.session_state['game_records']:
        player_manager = PlayerManager(st.session_state['game_records'])
        
        # 基本統計
        total_games = len(st.session_state['game_records'])
        all_players = player_manager.get_all_player_names()
        
        # メトリクス表示
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("総対局数", f"{total_games}回")
        
        with col2:
            st.metric("参加プレイヤー数", f"{len(all_players)}人")
        
        with col3:
            if all_players:
                # 最も対局数の多いプレイヤー
                most_active = max(all_players, key=lambda p: player_manager.get_player_statistics(p)['total_games'])
                most_active_games = player_manager.get_player_statistics(most_active)['total_games']
                st.metric("最多対局者", f"{most_active}", f"{most_active_games}回")
        
        with col4:
            if all_players:
                # 最高平均点数のプレイヤー
                best_avg = max(all_players, key=lambda p: player_manager.get_player_statistics(p)['avg_score'])
                best_avg_score = player_manager.get_player_statistics(best_avg)['avg_score']
                st.metric("最高平均", f"{best_avg}", f"{best_avg_score:,.0f}点")
        
        # プレイヤー別詳細統計
        st.subheader("プレイヤー別詳細統計")
        
        if all_players:
            player_stats = []
            for player_name in all_players:
                stats = player_manager.get_player_statistics(player_name)
                if stats['total_games'] > 0:
                    player_stats.append({
                        'プレイヤー': player_name,
                        '対局数': f"{stats['total_games']}回",
                        '平均点数': f"{stats['avg_score']:,.0f}点",
                        '平均順位': f"{stats['avg_rank']:.2f}位",
                        '1位率': f"{stats['win_rate']:.1f}%",
                        '最高点数': f"{stats['max_score']:,.0f}点",
                        '最低点数': f"{stats['min_score']:,.0f}点"
                    })
            
            if player_stats:
                stats_df = pd.DataFrame(player_stats)
                st.dataframe(stats_df, use_container_width=True, hide_index=True)
            else:
                st.info("統計データがありません")
        else:
            st.info("プレイヤーデータがありません")
        
        # 閉じるボタン
        if st.button("統計表示を閉じる", use_container_width=True, key="close_stats_modal_btn"):
            st.session_state['show_stats'] = False
            st.rerun()
    
    else:
        st.info("統計を表示するデータがありません")
        if st.button("統計表示を閉じる", key="close_empty_stats_modal_btn"):
            st.session_state['show_stats'] = False
            st.rerun()