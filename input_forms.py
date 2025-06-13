# input_forms.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
from player_manager import PlayerManager

def create_player_input_fields(prefix="default"):
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
                    key=f"{prefix}_input_type_{i}",
                    horizontal=True,
                    label_visibility="collapsed"
                )
                
                if input_type == "既存選択":
                    selected_player = st.selectbox(
                        "プレイヤーを選択",
                        [""] + existing_players,
                        key=f"{prefix}_select_player_{i}",
                        label_visibility="collapsed"
                    )
                    player_names.append(selected_player)
                else:
                    new_name = st.text_input(
                        "名前",
                        key=f"{prefix}_new_player_{i}",
                        placeholder="ニックネーム",
                        label_visibility="collapsed"
                    )
                    player_names.append(new_name)
            else:
                new_name = st.text_input(
                    "名前",
                    key=f"{prefix}_new_player_{i}",
                    placeholder="ニックネーム",
                    label_visibility="collapsed"
                )
                player_names.append(new_name)
    
    return player_names

def create_player_input_fields_with_defaults(prefix="default", default_names=None):
    """プレイヤー名入力フィールド（デフォルト値付き）"""
    if default_names is None:
        default_names = ['', '', '', '']
    
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
            default_name = default_names[i] if i < len(default_names) else ''
            
            if existing_players and default_name in existing_players:
                # 既存プレイヤーの場合は選択済みに
                input_type = st.radio(
                    "入力方法",
                    ["新規入力", "既存選択"],
                    index=1,  # 既存選択をデフォルト
                    key=f"{prefix}_input_type_{i}",
                    horizontal=True,
                    label_visibility="collapsed"
                )
                
                if input_type == "既存選択":
                    try:
                        default_index = existing_players.index(default_name) + 1  # +1 because of empty option
                    except ValueError:
                        default_index = 0
                    
                    selected_player = st.selectbox(
                        "選択",
                        [""] + existing_players,
                        index=default_index,
                        key=f"{prefix}_select_player_{i}",
                        label_visibility="collapsed"
                    )
                    player_names.append(selected_player)
                else:
                    new_name = st.text_input(
                        "名前",
                        value=default_name,
                        key=f"{prefix}_new_player_{i}",
                        placeholder="ニックネーム",
                        label_visibility="collapsed"
                    )
                    player_names.append(new_name)
            else:
                # 新規プレイヤーまたは既存プレイヤーがいない場合
                if existing_players:
                    input_type = st.radio(
                        "入力方法",
                        ["新規入力", "既存選択"],
                        index=0,  # 新規入力をデフォルト
                        key=f"{prefix}_input_type_{i}",
                        horizontal=True,
                        label_visibility="collapsed"
                    )
                    
                    if input_type == "既存選択":
                        selected_player = st.selectbox(
                            "選択",
                            [""] + existing_players,
                            key=f"{prefix}_select_player_{i}",
                            label_visibility="collapsed"
                        )
                        player_names.append(selected_player)
                    else:
                        new_name = st.text_input(
                            "名前",
                            value=default_name,
                            key=f"{prefix}_new_player_{i}",
                            placeholder="ニックネーム",
                            label_visibility="collapsed"
                        )
                        player_names.append(new_name)
                else:
                    new_name = st.text_input(
                        "名前",
                        value=default_name,
                        key=f"{prefix}_new_player_{i}",
                        placeholder="ニックネーム",
                        label_visibility="collapsed"
                    )
                    player_names.append(new_name)
    
    return player_names
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
                    key=f"{prefix}_input_type_{i}",
                    horizontal=True,
                    label_visibility="collapsed"
                )
                
                if input_type == "既存選択":
                    selected_player = st.selectbox(
                        "選択",
                        [""] + existing_players,
                        key=f"{prefix}_select_player_{i}",
                        label_visibility="collapsed"
                    )
                    player_names.append(selected_player)
                else:
                    new_name = st.text_input(
                        "名前",
                        key=f"{prefix}_new_player_{i}",
                        placeholder="ニックネーム",
                        label_visibility="collapsed"
                    )
                    player_names.append(new_name)
            else:
                new_name = st.text_input(
                    "名前",
                    key=f"{prefix}_new_player_{i}",
                    placeholder="ニックネーム",
                    label_visibility="collapsed"
                )
                player_names.append(new_name)
    
    return player_names

def create_score_input_fields(player_names, default_scores=None, prefix="default"):
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
                key=f"{prefix}_score_{i}",
                label_visibility="collapsed"
            )
            scores.append(score)
    
    return scores

def create_game_info_fields(prefix="default"):
    """対局情報入力フィールド"""
    from config_manager import ConfigManager
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        game_date = st.date_input("対局日", value=date.today(), key=f"{prefix}_date")
    
    with col2:
        game_time = st.time_input("対局時刻", key=f"{prefix}_time")
    
    with col3:
        # デフォルト値を設定から取得
        config_manager = ConfigManager()
        default_game_type = config_manager.get_default_game_type()
        game_types = ["四麻東風", "四麻半荘", "三麻東風", "三麻半荘"]
        default_index = game_types.index(default_game_type) if default_game_type in game_types else 1  # 四麻半荘をデフォルト
        
        game_type = st.selectbox("対局タイプ", game_types, index=default_index, key=f"{prefix}_game_type")
    
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
        # 点数順にソート（高い順）
        confirmation_data.sort(key=lambda x: int(x["点数"].replace(",", "").replace("点", "")), reverse=True)
        conf_df = pd.DataFrame(confirmation_data)
        st.dataframe(conf_df, hide_index=True, use_container_width=True)
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