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
        
        # データ削除に関する説明
        with st.expander("データの編集・削除について"):
            st.markdown("""
            **データの削除方法**:
            1. Google Sheetsを直接開く（サイドバーのシーズン管理から確認可能）
            2. 削除したい行を選択して右クリック → 「行を削除」
            3. このアプリで「データ同期」ボタンを押して更新
            
            **データの編集方法**:
            1. Google Sheetsで直接セルを編集
            2. このアプリで「データ同期」ボタンを押して更新
            
            **注意**: 
            - Google Sheetsでの変更は即座にアプリに反映されません
            - 変更後は必ず「データ同期」を実行してください
            - ヘッダー行（1行目）は削除しないでください
            """)
        
        
        # ボタン
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("閉じる", use_container_width=True, key="close_data_modal_btn"):
                st.session_state['show_data'] = False
                st.rerun()
        
        with col2:
            # データ同期ボタンを追加
            if st.button("データ同期", use_container_width=True, key="modal_sync_btn", help="Google Sheetsから最新データを読み込み"):
                from config_manager import ConfigManager
                from ui_components import sync_data_from_sheets
                config_manager = ConfigManager()
                sync_data_from_sheets(config_manager)
                st.rerun()
        
    else:
        st.info("表示する記録がありません")
        if st.button("閉じる", key="close_empty_data_modal_btn"):
            st.session_state['show_data'] = False
            st.rerun()

def show_statistics_modal():
    """統計表示モーダル（合計スコアランキング + 表で両方併記）"""
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
                # 最高合計スコアのプレイヤー（ランキング基準に合わせて変更）
                best_total = max(all_players, key=lambda p: player_manager.get_player_statistics(p)['total_score'])
                best_total_score = player_manager.get_player_statistics(best_total)['total_score']
                st.metric("最高合計スコア", f"{best_total}", f"{best_total_score:+.1f}pt")
        
        # プレイヤー別詳細統計（合計スコアランキング + 表で両方併記）
        st.subheader("プレイヤー別詳細統計")
        
        if all_players:
            player_stats = []
            for player_name in all_players:
                stats = player_manager.get_player_statistics(player_name)
                if stats['total_games'] > 0:
                    player_stats.append({
                        'プレイヤー': player_name,
                        '対局数': f"{stats['total_games']}回",
                        '合計スコア': f"{stats['total_score']:+.1f}pt",      # 合計スコア
                        '平均スコア': f"{stats['avg_score']:+.2f}pt",        # 平均スコア（新規追加）
                        '平均点棒': f"{stats['avg_raw_score']:,.0f}点",      # 従来の点棒
                        '平均順位': f"{stats['avg_rank']:.2f}位",
                        '1位率': f"{stats['win_rate']:.1f}%",
                        '最高点棒': f"{stats['max_score']:,.0f}点",
                        '最低点棒': f"{stats['min_score']:,.0f}点",
                        # ソート用の数値データ
                        '_total_score_num': stats['total_score']
                    })
            
            if player_stats:
                # 合計スコアでソート（ランキング基準は合計スコア）
                player_stats_sorted = sorted(player_stats, key=lambda x: x['_total_score_num'], reverse=True)
                
                # ソート用データを削除
                for stat in player_stats_sorted:
                    del stat['_total_score_num']
                
                # ランキング説明
                st.markdown("**ランキング基準: 合計スコア**")
                st.caption("継続参加 + 実力を総合的に評価。多く参加して好成績を残したプレイヤーが上位に表示されます。")
                
                # 統計表を表示（合計スコアと平均スコア両方を併記）
                stats_df = pd.DataFrame(player_stats_sorted)
                st.dataframe(stats_df, use_container_width=True, hide_index=True)
                
                # スコア計算説明
                with st.expander("スコア計算について"):
                    from scoring_config import SCORING_EXPLANATION
                    st.markdown(f"""
                    **計算式**: {SCORING_EXPLANATION['formula']}
                    
                    **詳細**:
                    - {SCORING_EXPLANATION['uma_4_player']}
                    - {SCORING_EXPLANATION['uma_3_player']}
                    - {SCORING_EXPLANATION['participation']}
                    - {SCORING_EXPLANATION['starting_points']}
                    
                    **表示項目の説明**:
                    - **合計スコア**: 全ゲームのスコアを合計（ランキング基準）
                    - **平均スコア**: 1ゲームあたりの平均スコア（実力指標）
                    - **平均点棒**: 従来の点棒による平均
                    """)
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