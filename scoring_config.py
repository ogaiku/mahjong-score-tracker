# scoring_config.py - 麻雀点数計算設定
"""
麻雀の点数計算に関する設定ファイル

計算式:
[点数] = ([ゲーム終了時の点棒] - [ゲーム開始時の点棒]) ÷ 1000 + [順位に応じたウマ] + [参加得点]
"""

# 基本設定
SCORING_CONFIG = {
    # ゲーム開始時の点棒
    "starting_points": {
        "四麻東風": 25000,
        "四麻半荘": 25000,
        "三麻東風": 35000,
        "三麻半荘": 35000
    },
    
    # 順位ウマ（4人麻雀）
    "uma_4_player": {
        1: 15,   # 1位: +15
        2: 5,    # 2位: +5
        3: -5,   # 3位: -5
        4: -15   # 4位: -15
    },
    
    # 順位ウマ（3人麻雀）
    "uma_3_player": {
        1: 15,   # 1位: +15
        2: 0,    # 2位: ±0
        3: -15   # 3位: -15
    },
    
    # 参加得点
    "participation_points": 10,
    
    # 点棒差分の除数
    "point_divisor": 1000
}

def get_starting_points(game_type: str) -> int:
    """ゲームタイプに応じた開始点棒を取得"""
    return SCORING_CONFIG["starting_points"].get(game_type, 25000)

def get_uma_points(rank: int, player_count: int) -> int:
    """順位と参加人数に応じたウマを取得"""
    if player_count == 3:
        return SCORING_CONFIG["uma_3_player"].get(rank, 0)
    else:  # 4人麻雀（デフォルト）
        return SCORING_CONFIG["uma_4_player"].get(rank, 0)

def calculate_game_score(final_points: int, game_type: str, rank: int, player_count: int) -> float:
    """
    麻雀の最終スコアを計算
    
    Args:
        final_points: ゲーム終了時の点棒
        game_type: ゲームタイプ（"四麻東風", "四麻半荘", etc.）
        rank: 順位（1-4）
        player_count: 参加人数
    
    Returns:
        計算された最終スコア
    """
    starting_points = get_starting_points(game_type)
    uma_points = get_uma_points(rank, player_count)
    participation_points = SCORING_CONFIG["participation_points"]
    divisor = SCORING_CONFIG["point_divisor"]
    
    # [点数] = ([ゲーム終了時の点棒] - [ゲーム開始時の点棒]) ÷ 1000 + [順位に応じたウマ] + [参加得点]
    score = (final_points - starting_points) / divisor + uma_points + participation_points
    
    return score

def get_player_count_from_game_type(game_type: str) -> int:
    """ゲームタイプから参加人数を判定"""
    if "三麻" in game_type:
        return 3
    else:
        return 4

# 設定の詳細説明
SCORING_EXPLANATION = {
    "formula": "[点数] = ([ゲーム終了時の点棒] - [ゲーム開始時の点棒]) ÷ 1000 + [順位に応じたウマ] + [参加得点]",
    "uma_4_player": "4人麻雀: 1位+15, 2位+5, 3位-5, 4位-15",
    "uma_3_player": "3人麻雀: 1位+15, 2位±0, 3位-15",
    "participation": "参加得点: +10",
    "starting_points": "開始点棒: 四麻25000点, 三麻35000点"
}