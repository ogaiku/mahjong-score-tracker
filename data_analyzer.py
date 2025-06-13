# data_analyzer.py (新スコア対応版)
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List
from player_manager import PlayerManager

class MahjongDataAnalyzer:
    def __init__(self, game_records: List[Dict]):
        self.records = game_records
        self.df = pd.DataFrame(game_records) if game_records else pd.DataFrame()
        self.player_manager = PlayerManager(game_records)
    
    def create_player_ranking_chart(self) -> go.Figure:
        all_players = self.player_manager.get_all_player_names()
        
        if not all_players:
            return go.Figure()
        
        players = []
        avg_scores = []
        game_counts = []
        
        for player_name in all_players:
            stats = self.player_manager.get_player_statistics(player_name)
            if stats['total_games'] > 0:
                players.append(player_name)
                avg_scores.append(stats['avg_score'])  # 新スコア
                game_counts.append(stats['total_games'])
        
        if not players:
            return go.Figure()
        
        sorted_data = sorted(zip(players, avg_scores, game_counts), 
                           key=lambda x: x[1], reverse=True)
        players, avg_scores, game_counts = zip(*sorted_data)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=list(players),
            y=list(avg_scores),
            text=[f'{score:+.1f}' for score in avg_scores],
            textposition='auto',
            marker_color='#3b82f6',
            hovertemplate='%{x}<br>平均スコア: %{y:+.2f}pt<br>対局数: %{customdata}回<extra></extra>',
            customdata=list(game_counts)
        ))
        
        fig.update_layout(
            title="プレイヤー別平均スコア",
            xaxis_title="プレイヤー",
            yaxis_title="平均スコア (pt)",
            height=400,
            showlegend=False
        )
        
        return fig
    
    def create_rank_distribution_chart(self) -> go.Figure:
        all_players = self.player_manager.get_all_player_names()
        
        if not all_players:
            return go.Figure()
        
        fig = go.Figure()
        colors = ['#fbbf24', '#c0c0c0', '#cd7f32', '#1f2937']
        
        for rank in [1, 2, 3, 4]:
            players = []
            counts = []
            
            for player_name in all_players:
                stats = self.player_manager.get_player_statistics(player_name)
                if stats['total_games'] > 0:
                    players.append(player_name)
                    counts.append(stats['rank_distribution'][rank])
            
            if players:
                fig.add_trace(go.Bar(
                    x=players,
                    y=counts,
                    name=f'{rank}位',
                    marker_color=colors[rank-1]
                ))
        
        fig.update_layout(
            title="順位分布",
            xaxis_title="プレイヤー",
            yaxis_title="回数",
            barmode='stack',
            height=400
        )
        
        return fig
    
    def create_score_trend_chart(self, player_name: str) -> go.Figure:
        records = self.player_manager.get_player_records(player_name)
        
        if not records:
            return go.Figure()
        
        records.sort(key=lambda x: (x['date'], x['time']))
        
        # 新スコア計算でトレンド作成
        scores = []
        cumulative_scores = []
        cumulative_total = 0
        
        for record in records:
            game_score = self.player_manager.calculate_player_game_score(record, player_name)
            scores.append(game_score)
            cumulative_total += game_score
            cumulative_scores.append(cumulative_total)
        
        games = list(range(1, len(scores) + 1))
        
        fig = go.Figure()
        
        # ゲームごとのスコア
        fig.add_trace(go.Scatter(
            x=games,
            y=scores,
            mode='lines+markers',
            name='ゲームスコア',
            line=dict(color='#3b82f6', width=2),
            marker=dict(size=6),
            yaxis='y'
        ))
        
        # 累積スコア
        fig.add_trace(go.Scatter(
            x=games,
            y=cumulative_scores,
            mode='lines+markers',
            name='累積スコア',
            line=dict(color='#ef4444', width=2),
            marker=dict(size=6),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title=f"{player_name} のスコア推移",
            xaxis_title="対局回数",
            yaxis=dict(
                title="ゲームスコア (pt)",
                side="left"
            ),
            yaxis2=dict(
                title="累積スコア (pt)",
                overlaying="y",
                side="right"
            ),
            height=400,
            legend=dict(x=0.02, y=0.98)
        )
        
        return fig
    
    def create_score_distribution_chart(self, player_name: str) -> go.Figure:
        """スコア分布チャート"""
        records = self.player_manager.get_player_records(player_name)
        
        if not records:
            return go.Figure()
        
        game_scores = []
        for record in records:
            game_score = self.player_manager.calculate_player_game_score(record, player_name)
            game_scores.append(game_score)
        
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=game_scores,
            nbinsx=20,
            name='スコア分布',
            marker_color='#3b82f6',
            opacity=0.7
        ))
        
        # 平均線を追加
        avg_score = sum(game_scores) / len(game_scores)
        fig.add_vline(
            x=avg_score,
            line_dash="dash",
            line_color="red",
            annotation_text=f"平均: {avg_score:+.1f}pt"
        )
        
        fig.update_layout(
            title=f"{player_name} のスコア分布",
            xaxis_title="スコア (pt)",
            yaxis_title="頻度",
            height=400
        )
        
        return fig