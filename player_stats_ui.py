# player_stats_ui.py
import streamlit as st
import pandas as pd
from player_manager import PlayerManager
from data_analyzer import MahjongDataAnalyzer

def show_player_statistics_modal():
    st.subheader("プレイヤー統計")
    
    if 'game_records' not in st.session_state or not st.session_state['game_records']:
        st.info("統計を表示するデータがありません")
        return
    
    player_manager = PlayerManager(st.session_state['game_records'])
    analyzer = MahjongDataAnalyzer(st.session_state['game_records'])
    
    all_players = player_manager.get_all_player_names()
    
    if not all_players:
        st.info("プレイヤーデータがありません")
        return
    
    tab1, tab2, tab3 = st.tabs(["ランキング", "個人統計", "対戦成績"])
    
    with tab1:
        show_ranking_tab(player_manager, analyzer)
    
    with tab2:
        show_individual_stats_tab(player_manager, analyzer, all_players)
    
    with tab3:
        show_head_to_head_tab(player_manager, all_players)

def show_ranking_tab(player_manager: PlayerManager, analyzer: MahjongDataAnalyzer):
    # プレイヤー統計を取得して合計スコア順にソート
    all_players = player_manager.get_all_player_names()
    
    if not all_players:
        st.info("ランキングデータがありません")
        return
    
    player_stats = []
    for player_name in all_players:
        stats = player_manager.get_player_statistics(player_name)
        if stats['total_games'] > 0:
            player_stats.append({
                'プレイヤー名': player_name,
                '合計スコア': stats['total_score'],
                '対戦数': stats['total_games']
            })
    
    if not player_stats:
        st.info("ランキングデータがありません")
        return
    
    # 合計スコア順にソート
    player_stats.sort(key=lambda x: x['合計スコア'], reverse=True)
    
    # 全対戦を時系列順に取得
    all_games = st.session_state['game_records']
    all_games_sorted = sorted(all_games, key=lambda x: (x['date'], x['time']))
    
    # ランキング表のデータを作成
    ranking_data = []
    
    for rank, player_data in enumerate(player_stats, 1):
        row = {
            '順位': rank,
            'プレイヤー名': player_data['プレイヤー名'],
            '合計スコア': f"{player_data['合計スコア']:+.1f}pt",
            '対戦数': f"{player_data['対戦数']}回"
        }
        
        # 各対戦（第1戦、第2戦...）でのこのプレイヤーのスコアを追加
        for game_idx, game in enumerate(all_games_sorted):
            game_col = f"第{game_idx+1}戦"
            
            # このプレイヤーがこの対戦に参加していたかチェック
            player_score = None
            for i in range(1, 5):
                name_key = f'player{i}_name'
                score_key = f'player{i}_score'
                
                if game.get(name_key) == player_data['プレイヤー名']:
                    # 新スコア計算のため、対戦記録を作成
                    other_players = []
                    for j in range(1, 5):
                        if j != i:
                            other_name = game.get(f'player{j}_name', '')
                            other_score = game.get(f'player{j}_score', 0)
                            if other_name:
                                other_players.append({
                                    'name': other_name,
                                    'score': other_score
                                })
                    
                    record = {
                        'score': game.get(score_key, 0),
                        'other_players': other_players,
                        'game_type': game.get('game_type', '四麻半荘')
                    }
                    
                    game_score = player_manager.calculate_player_game_score(record, player_data['プレイヤー名'])
                    player_score = f"{game_score:+.1f}pt"
                    break
            
            if player_score is not None:
                row[game_col] = player_score
            else:
                row[game_col] = ""  # このプレイヤーは参加していない
        
        ranking_data.append(row)
    
    # DataFrameを作成して表示
    ranking_df = pd.DataFrame(ranking_data)
    st.dataframe(ranking_df, use_container_width=True, hide_index=True)
    
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
        """)
    
    ranking_chart = analyzer.create_player_ranking_chart()
    if ranking_chart.data:
        st.plotly_chart(ranking_chart, use_container_width=True)
    
    rank_dist_chart = analyzer.create_rank_distribution_chart()
    if rank_dist_chart.data:
        st.plotly_chart(rank_dist_chart, use_container_width=True)

def show_individual_stats_tab(player_manager: PlayerManager, analyzer: MahjongDataAnalyzer, all_players: list):
    selected_player = st.selectbox("プレイヤーを選択", all_players)
    
    if selected_player:
        stats = player_manager.get_player_statistics(selected_player)
        
        if stats['total_games'] > 0:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("総対戦数", f"{stats['total_games']}回")
            with col2:
                st.metric("平均スコア", f"{stats['avg_score']:+.2f}pt")  # 新スコア
            with col3:
                st.metric("平均順位", f"{stats['avg_rank']:.2f}位")
            with col4:
                st.metric("1位率", f"{stats['win_rate']:.1f}%")
            
            # 追加情報
            col5, col6 = st.columns(2)
            with col5:
                st.metric("平均点棒", f"{stats['avg_raw_score']:,.0f}点")  # 従来の点棒
            with col6:
                st.metric("総スコア", f"{stats['total_score']:+.1f}pt")  # 新スコアの合計
            
            trend_chart = analyzer.create_score_trend_chart(selected_player)
            if trend_chart.data:
                st.plotly_chart(trend_chart, use_container_width=True)
            
            # 最近の対戦記録（詳細版）
            st.subheader("最近の対戦記録")
            recent_records = stats['records'][-10:]
            if recent_records:
                record_data = []
                for record in reversed(recent_records):
                    # 新スコア計算
                    game_score = player_manager.calculate_player_game_score(record, selected_player)
                    
                    record_data.append({
                        "日付": record['date'],
                        "タイプ": record['game_type'],
                        "点棒": f"{record['score']:,.0f}点",
                        "スコア": f"{game_score:+.1f}pt"
                    })
                
                records_df = pd.DataFrame(record_data)
                st.dataframe(records_df, hide_index=True, use_container_width=True)
        else:
            st.info(f"{selected_player} の対戦記録がありません")

def show_head_to_head_tab(player_manager: PlayerManager, all_players: list):
    if len(all_players) < 2:
        st.info("対戦成績を表示するには最低2名のプレイヤーが必要です")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        player1 = st.selectbox("プレイヤー1", all_players, key="h2h_player1")
    
    with col2:
        player2_options = [p for p in all_players if p != player1]
        if player2_options:
            player2 = st.selectbox("プレイヤー2", player2_options, key="h2h_player2")
        else:
            player2 = None
    
    if player1 and player2:
        h2h_stats = player_manager.get_head_to_head_stats(player1, player2)
        
        if h2h_stats['total_games'] > 0:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("総対戦数", f"{h2h_stats['total_games']}回")
            with col2:
                st.metric(f"{player1}勝利", f"{h2h_stats['player1_wins']}回")
            with col3:
                st.metric(f"{player2}勝利", f"{h2h_stats['player2_wins']}回")
            with col4:
                st.metric("引き分け", f"{h2h_stats['draws']}回")
            
            if h2h_stats['games']:
                history_data = []
                for game in h2h_stats['games']:
                    winner_display = "引き分け" if game['winner'] == 'draw' else game['winner']
                    history_data.append({
                        "日付": game['date'],
                        "タイプ": game['game_type'],
                        f"{player1}点数": f"{game[player1]['score']:,.0f}点",
                        f"{player2}点数": f"{game[player2]['score']:,.0f}点",
                        "勝者": winner_display
                    })
                
                history_df = pd.DataFrame(history_data)
                st.dataframe(history_df, hide_index=True, use_container_width=True)
        else:
            st.info(f"{player1} と {player2} の直接対戦記録はありません")