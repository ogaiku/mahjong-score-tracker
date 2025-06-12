# data_analyzer.py
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List
import streamlit as st

class MahjongDataAnalyzer:
    """麻雀対局データの分析クラス"""
    
    def __init__(self, game_records: List[Dict]):
        self.records = game_records
        self.df = pd.DataFrame(game_records) if game_records else pd.DataFrame()
    
    def calculate_basic_stats(self) -> Dict:
        """基本統計を計算"""
        if self.df.empty:
            return {}
        
        stats = {
            'total_games': len(self.df),
            'avg_scores': {},
            'total_scores': {},
            'max_scores': {},
            'min_scores': {}
        }
        
        # 各プレイヤーの統計
        for i in range(1, 5):
            score_col = f'player{i}_score'
            if score_col in self.df.columns:
                scores = pd.to_numeric(self.df[score_col], errors='coerce')
                stats['avg_scores'][f'player{i}'] = scores.mean()
                stats['total_scores'][f'player{i}'] = scores.sum()
                stats['max_scores'][f'player{i}'] = scores.max()
                stats['min_scores'][f'player{i}'] = scores.min()
        
        return stats
    
    def calculate_rank_stats(self) -> Dict:
        """順位統計を計算"""
        if self.df.empty:
            return {}
        
        rank_data = []
        
        # 各対局で順位を計算
        for _, row in self.df.iterrows():
            scores = []
            for i in range(1, 5):
                score_col = f'player{i}_score'
                if score_col in row:
                    scores.append(pd.to_numeric(row[score_col], errors='coerce'))
                else:
                    scores.append(0)
            
            # 順位計算（高い点数が上位）
            ranks = pd.Series(scores).rank(ascending=False, method='min')
            rank_data.append(ranks.tolist())
        
        rank_df = pd.DataFrame(rank_data, columns=[f'Player{i}' for i in range(1, 5)])
        
        # 順位分布を計算
        rank_distribution = {}
        for i in range(1, 5):
            player_col = f'Player{i}'
            if player_col in rank_df.columns:
                rank_counts = rank_df[player_col].value_counts().sort_index()
                rank_distribution[f'player{i}'] = rank_counts.to_dict()
        
        return {
            'rank_data': rank_data,
            'rank_distribution': rank_distribution
        }
    
    def create_score_trend_chart(self) -> go.Figure:
        """点数推移グラフを作成"""
        if self.df.empty:
            return go.Figure()
        
        # 日付順にソート
        df_sorted = self.df.copy()
        if 'date' in df_sorted.columns:
            df_sorted = df_sorted.sort_values('date')
        
        fig = go.Figure()
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
        
        for i in range(1, 5):
            score_col = f'player{i}_score'
            if score_col in df_sorted.columns:
                scores = pd.to_numeric(df_sorted[score_col], errors='coerce')
                
                fig.add_trace(go.Scatter(
                    x=list(range(len(df_sorted))),
                    y=scores,
                    mode='lines+markers',
                    name=f'プレイヤー{i}',
                    line=dict(width=2, color=colors[i-1]),
                    marker=dict(size=6)
                ))
        
        fig.update_layout(
            title="対局ごとの点数推移",
            xaxis_title="対局回数",
            yaxis_title="点数",
            hovermode='x unified',
            height=400
        )
        
        return fig
    
    def create_rank_distribution_chart(self) -> go.Figure:
        """順位分布グラフを作成"""
        rank_stats = self.calculate_rank_stats()
        
        if not rank_stats or 'rank_distribution' not in rank_stats:
            return go.Figure()
        
        fig = go.Figure()
        
        players = [f'プレイヤー{i}' for i in range(1, 5)]
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
        
        for i, (player_key, distribution) in enumerate(rank_stats['rank_distribution'].items()):
            ranks = list(range(1, 5))
            counts = [distribution.get(float(rank), 0) for rank in ranks]
            
            fig.add_trace(go.Bar(
                x=[f'{rank}位' for rank in ranks],
                y=counts,
                name=players[i],
                marker_color=colors[i]
            ))
        
        fig.update_layout(
            title="順位分布",
            xaxis_title="順位",
            yaxis_title="回数",
            barmode='group',
            height=400
        )
        
        return fig
    
    def create_average_score_chart(self) -> go.Figure:
        """平均点数比較グラフを作成"""
        stats = self.calculate_basic_stats()
        
        if not stats or 'avg_scores' not in stats:
            return go.Figure()
        
        players = [f'プレイヤー{i}' for i in range(1, 5)]
        avg_scores = [stats['avg_scores'].get(f'player{i}', 0) for i in range(1, 5)]
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
        
        fig = go.Figure(data=[
            go.Bar(
                x=players,
                y=avg_scores,
                marker_color=colors,
                text=[f'{score:,.0f}' for score in avg_scores],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title="プレイヤー別平均点数",
            xaxis_title="プレイヤー",
            yaxis_title="平均点数",
            height=400
        )
        
        return fig
    
    def get_summary_report(self) -> Dict:
        """サマリーレポートを生成"""
        if self.df.empty:
            return {}
        
        basic_stats = self.calculate_basic_stats()
        rank_stats = self.calculate_rank_stats()
        
        # 最も成績の良いプレイヤーを特定
        best_player = None
        best_avg = 0
        
        if 'avg_scores' in basic_stats:
            for player, avg_score in basic_stats['avg_scores'].items():
                if avg_score > best_avg:
                    best_avg = avg_score
                    best_player = player
        
        return {
            'basic_stats': basic_stats,
            'rank_stats': rank_stats,
            'best_player': best_player,
            'best_average': best_avg
        }