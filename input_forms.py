# input_forms.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
from player_manager import PlayerManager

def create_player_input_fields():
    """プレイヤー名入力フィールド"""
    if 'game_records' in st.session_state and st.session_state['game_records']:
        player_manager = PlayerManager(st.session_state['game_records'])
        existing_players = player_manager.get_all_player_names()
    else:
        existing_players = []
    
    cols = st.columns(4)
    player_names = []
    
    for i, col in enumerate(cols):
        with col:
            st.caption(f"プレイヤー{i+1}")
            
            if existing_players:
                input_type = st.radio(
                    "入力方法",
                    ["新規入力", "既存選択"],
                    key=f"input_type_{i}",
                    horizontal=True,
                    label_visibility="collapsed"
                )
                
                if input_type == "既存選択":
                    selected_player = st.selectbox(
                        "選択",
                        [""] + existing_players,
                        key=f"select_player_{i}",
                        label_visibility="collapsed"
                    )
                    player_names.append(selected_player)
                else:
                    new_name = st.text_input(
                        "名前",
                        key=f"new_player_{i}",
                        placeholder="ニックネーム",
                        label_visibility="collapsed"
                    )
                    player_names.append(new_name)
            else:
                new_name = st.text_input(
                    "名前",
                    key=f"new_player_{i}",
                    placeholder="ニックネーム",
                    label_visibility="collapsed"
                )
                player_names.append(new_name)
    
    return player_names

def create_score_input_fields(player_names, default_scores=None):
    """点数入力フィールド"""
    if default_scores is None:
        default_scores = [25000, 25000, 25000, 25000]
    
    cols = st.columns(4)
    scores = []
    
    for i, (col, name, default_score) in enumerate(zip(cols, player_names, default_scores)):
        with col:
            label = name if name.strip() else f"プレイヤー{i+1}"
            st.caption(label)
            score = st.number_input(
                "点数",
                min_value=-100000,
                max_value=200000,
                value=int(default_score),
                step=100,
                key=f"score_{i}",
                label_visibility="collapsed"
            )
            scores.append(score)
    
    return scores

def create_game_info_fields():
    """対局情報入力フィールド"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        game_date = st.date_input("対局日", value=date.today())
    
    with col2:
        game_time = st.time_input("対局時刻")
    
    with col3:
        game_type = st.selectbox("対局タイプ", ["四麻東風", "四麻半荘", "三麻東風", "三麻半荘"])
    
    return game_date, game_time, game_type

def show_input_confirmation(player_names, scores):
    """入力内容確認表示"""
    confirmation_data = []
    for name, score in zip(player_names, scores):
        if name.strip():
            confirmation_data.append({
                "プレイヤー": name,
                "点数": f"{score:,}点"
            })
    
    if confirmation_data:
        conf_df = pd.DataFrame(confirmation_data)
        st.dataframe(conf_df, hide_index=True, use_container_width=True)
        
        # 順位プレビュー
        scores_for_ranking = [(name, score) for name, score in zip(player_names, scores) if name.strip()]
        if len(scores_for_ranking) > 1:
            sorted_players = sorted(scores_for_ranking, key=lambda x: x[1], reverse=True)
            st.write("順位プレビュー")
            rank_preview = []
            for rank, (name, score) in enumerate(sorted_players, 1):
                rank_preview.append({
                    "順位": f"{rank}位",
                    "プレイヤー": name,
                    "点数": f"{score:,}点"
                })
            
            rank_df = pd.DataFrame(rank_preview)
            st.dataframe(rank_df, hide_index=True, use_container_width=True)
        
        return True
    else:
        st.warning("少なくとも1名のプレイヤー名を入力してください")
        return False

def save_game_record(player_names, scores, game_date, game_time, game_type, notes=""):
    """対局記録保存"""
    from ui_components import save_game_record_with_names
    
    players_data = []
    for name, score in zip(player_names, scores):
        players_data.append({"name": name.strip(), "score": score})
    
    valid_players = [p for p in players_data if p['name']]
    if len(valid_players) < 1:
        st.error("少なくとも1名のプレイヤー名を入力してください")
        return False
    
    save_game_record_with_names(players_data, game_date, game_time, game_type, notes)
    return True