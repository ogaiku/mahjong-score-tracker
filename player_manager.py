# player_manager.py
import pandas as pd
from typing import Dict, List, Optional
from collections import defaultdict

class PlayerManager:
    def __init__(self, game_records: List[Dict]):
        self.records = game_records
        self.df = pd.DataFrame(game_records) if game_records else pd.DataFrame()
    
    def get_all_player_names(self) -> List[str]:
        if self.df.empty:
            return []
        
        all_names = []
        for i in range(1, 5):
            name_col = f'player{i}_name'
            if name_col in self.df.columns:
                names = self.df[name_col].dropna()
                all_names.extend(names.tolist())
        
        name_counts = pd.Series([name for name in all_names if name.strip()]).value_counts()
        return name_counts.index.tolist()
    
    def get_player_records(self, player_name: str) -> List[Dict]:
        if self.df.empty:
            return []
        
        player_records = []
        for _, row in self.df.iterrows():
            for i in range(1, 5):
                name_col = f'player{i}_name'
                score_col = f'player{i}_score'
                
                if name_col in row and score_col in row and row[name_col] == player_name:
                    other_players = []
                    for j in range(1, 5):
                        if j != i:
                            other_name_col = f'player{j}_name'
                            other_score_col = f'player{j}_score'
                            if other_name_col in row and other_score_col in row:
                                other_players.append({
                                    'name': row[other_name_col],
                                    'score': row[other_score_col]
                                })
                    
                    record = {
                        'date': row.get('date', ''),
                        'time': row.get('time', ''),
                        'game_type': row.get('game_type', ''),
                        'score': row[score_col],
                        'other_players': other_players,
                        'game_id': row.name
                    }
                    player_records.append(record)
                    break
        
        return player_records
    
    def calculate_player_rank(self, player_score: float, other_players: List[Dict]) -> int:
        all_scores = [player_score]
        for other in other_players:
            if other.get('score') is not None:
                all_scores.append(float(other['score']))
        
        sorted_scores = sorted(all_scores, reverse=True)
        return sorted_scores.index(player_score) + 1
    
    def get_player_statistics(self, player_name: str) -> Dict:
        records = self.get_player_records(player_name)
        
        if not records:
            return {
                'name': player_name,
                'total_games': 0,
                'avg_score': 0,
                'total_score': 0,
                'max_score': 0,
                'min_score': 0,
                'rank_distribution': {1: 0, 2: 0, 3: 0, 4: 0},
                'avg_rank': 0,
                'win_rate': 0,
                'records': []
            }
        
        scores = [float(record['score']) for record in records]
        ranks = []
        
        for record in records:
            rank = self.calculate_player_rank(
                float(record['score']), 
                record['other_players']
            )
            ranks.append(rank)
        
        rank_counts = pd.Series(ranks).value_counts().to_dict()
        rank_distribution = {1: 0, 2: 0, 3: 0, 4: 0}
        rank_distribution.update(rank_counts)
        
        return {
            'name': player_name,
            'total_games': len(records),
            'avg_score': sum(scores) / len(scores) if scores else 0,
            'total_score': sum(scores),
            'max_score': max(scores) if scores else 0,
            'min_score': min(scores) if scores else 0,
            'rank_distribution': rank_distribution,
            'avg_rank': sum(ranks) / len(ranks) if ranks else 0,
            'win_rate': (rank_distribution[1] / len(records) * 100) if records else 0,
            'records': records
        }
    
    def get_ranking_table(self) -> pd.DataFrame:
        all_players = self.get_all_player_names()
        
        if not all_players:
            return pd.DataFrame()
        
        ranking_data = []
        for player_name in all_players:
            stats = self.get_player_statistics(player_name)
            if stats['total_games'] > 0:
                ranking_data.append({
                    'プレイヤー名': player_name,
                    '対局数': stats['total_games'],
                    '平均点数': round(stats['avg_score'], 1),
                    '平均順位': round(stats['avg_rank'], 2),
                    '1位率': f"{stats['win_rate']:.1f}%",
                    '最高点数': int(stats['max_score']),
                    '最低点数': int(stats['min_score'])
                })
        
        df = pd.DataFrame(ranking_data)
        if not df.empty:
            df = df.sort_values('平均点数', ascending=False).reset_index(drop=True)
            df.index = df.index + 1
        
        return df
    
    def get_head_to_head_stats(self, player1: str, player2: str) -> Dict:
        if self.df.empty:
            return {}
        
        common_games = []
        for _, row in self.df.iterrows():
            players_in_game = []
            player_positions = {}
            
            for i in range(1, 5):
                name_col = f'player{i}_name'
                score_col = f'player{i}_score'
                
                if name_col in row and score_col in row:
                    player_name = row[name_col]
                    if player_name in [player1, player2]:
                        players_in_game.append(player_name)
                        player_positions[player_name] = {
                            'score': float(row[score_col]),
                            'position': i
                        }
            
            if len(players_in_game) == 2 and player1 in players_in_game and player2 in players_in_game:
                game_data = {
                    'date': row.get('date', ''),
                    'game_type': row.get('game_type', ''),
                    player1: player_positions[player1],
                    player2: player_positions[player2]
                }
                
                if player_positions[player1]['score'] > player_positions[player2]['score']:
                    game_data['winner'] = player1
                elif player_positions[player1]['score'] < player_positions[player2]['score']:
                    game_data['winner'] = player2
                else:
                    game_data['winner'] = 'draw'
                
                common_games.append(game_data)
        
        if not common_games:
            return {'total_games': 0, 'player1_wins': 0, 'player2_wins': 0, 'draws': 0}
        
        player1_wins = sum(1 for game in common_games if game['winner'] == player1)
        player2_wins = sum(1 for game in common_games if game['winner'] == player2)
        draws = sum(1 for game in common_games if game['winner'] == 'draw')
        
        return {
            'total_games': len(common_games),
            'player1_wins': player1_wins,
            'player2_wins': player2_wins,
            'draws': draws,
            'games': common_games
        }