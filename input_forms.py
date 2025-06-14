# input_forms.py - 簡素化版（プレイヤー登録分離）
import streamlit as st
import pandas as pd
from datetime import datetime, date
import pytz
from player_manager import PlayerManager

def create_player_input_fields_simple(prefix="default", default_names=None):
    """シンプルなプレイヤー選択フィールド（既存プレイヤーのみ）"""
    if default_names is None:
        default_names = ['', '', '', '']
    
    existing_players = get_registered_players()
    
    cols = st.columns(4)
    player_names = []
    
    for i, col in enumerate(cols):
        with col:
            default_name = default_names[i] if i < len(default_names) else ''
            
            if existing_players:
                # デフォルト値のインデックスを設定
                if default_name and default_name in existing_players:
                    default_index = existing_players.index(default_name) + 1
                else:
                    default_index = 0
                
                selected_player = st.selectbox(
                    "プレイヤー選択",
                    [""] + existing_players,
                    index=default_index,
                    key=f"{prefix}_player_{i}",
                    label_visibility="collapsed"
                )
                player_names.append(selected_player)
            else:
                st.info("プレイヤーを先に登録してください")
                player_names.append("")
    
    return player_names

def create_player_input_fields_with_registration(prefix="default", default_names=None):
    """スクショ解析用：既存選択＋新規登録機能付き"""
    if default_names is None:
        default_names = ['', '', '', '']
    
    existing_players = get_registered_players()
    
    cols = st.columns(4)
    player_names = []
    
    for i, col in enumerate(cols):
        with col:
            default_name = default_names[i] if i < len(default_names) else ''
            
            if existing_players:
                # デフォルト値のインデックスを設定
                if default_name and default_name in existing_players:
                    default_index = existing_players.index(default_name) + 1
                else:
                    default_index = 0
                
                selected_player = st.selectbox(
                    "プレイヤー選択",
                    [""] + existing_players,
                    index=default_index,
                    key=f"{prefix}_player_{i}",
                    label_visibility="collapsed"
                )
                
                # 解析結果で新しい名前が検出された場合の登録ボタン
                if default_name and default_name not in existing_players and default_name.strip():
                    if st.button("登録", key=f"{prefix}_register_{i}", use_container_width=True):
                        register_new_player(default_name)
                        st.rerun()
                
                player_names.append(selected_player)
            else:
                # 既存プレイヤーがいない場合
                if default_name and default_name.strip():
                    st.info(f"'{default_name}' を登録しますか？")
                    if st.button("登録", key=f"{prefix}_register_first_{i}", use_container_width=True):
                        register_new_player(default_name)
                        st.rerun()
                else:
                    st.info("プレイヤーを登録してください")
                player_names.append("")
    
    return player_names

def register_new_player(player_name):
    """新しいプレイヤーを登録（プレイヤーリストのみ管理）"""
    try:
        # セッション状態でプレイヤーリストを管理
        if 'registered_players' not in st.session_state:
            st.session_state['registered_players'] = []
        
        # 既存チェック
        if player_name.strip() in st.session_state['registered_players']:
            st.error(f"'{player_name}' は既に登録されています")
            return
        
        # プレイヤーリストに追加
        st.session_state['registered_players'].append(player_name.strip())
        st.success(f"プレイヤー '{player_name}' を登録しました")
        
    except Exception as e:
        st.error(f"プレイヤー登録エラー: {e}")

def get_registered_players():
    """登録済みプレイヤーリストを取得"""
    # セッション状態のプレイヤーリスト
    session_players = st.session_state.get('registered_players', [])
    
    # 対局記録から抽出したプレイヤー
    game_players = []
    if 'game_records' in st.session_state and st.session_state['game_records']:
        player_manager = PlayerManager(st.session_state['game_records'])
        game_players = player_manager.get_all_player_names()
    
    # 重複を除いて統合
    all_players = list(set(session_players + game_players))
    return sorted(all_players)

def show_player_management():
    """プレイヤー管理セクション"""
    if 'game_records' in st.session_state and st.session_state['game_records']:
        player_manager = PlayerManager(st.session_state['game_records'])
        existing_players = player_manager.get_all_player_names()
    else:
        existing_players = []
    
    tab1, tab2 = st.tabs(["プレイヤー登録", "登録済みプレイヤー"])
    
    with tab1:
        with st.form("player_registration_form"):
            new_player_name = st.text_input("プレイヤー名", placeholder="ニックネームを入力")
            submitted = st.form_submit_button("登録")
            
            if submitted and new_player_name.strip():
                if new_player_name.strip() in existing_players:
                    st.error(f"'{new_player_name}' は既に登録されています")
                else:
                    register_new_player(new_player_name.strip())
                    st.rerun()
            elif submitted:
                st.error("プレイヤー名を入力してください")
    
    with tab2:
        if existing_players:
            # プレイヤーリストを表示
            player_stats = []
            for player_name in existing_players:
                if 'game_records' in st.session_state and st.session_state['game_records']:
                    player_manager = PlayerManager(st.session_state['game_records'])
                    stats = player_manager.get_player_statistics(player_name)
                    player_stats.append({
                        "プレイヤー名": player_name,
                        "対局数": stats['total_games'],
                        "平均スコア": f"{stats['avg_score']:+.1f}pt" if stats['total_games'] > 0 else "0.0pt"
                    })
                else:
                    player_stats.append({
                        "プレイヤー名": player_name,
                        "対局数": 0,
                        "平均スコア": "0.0pt"
                    })
            
            df = pd.DataFrame(player_stats)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # プレイヤー削除機能
            with st.expander("プレイヤー削除"):
                st.warning("プレイヤーを削除すると、対局記録から該当プレイヤーの情報のみが除外されます（他の参加者の記録は保持されます）")
                
                if st.button("削除モードを有効にする", key="enable_delete_mode"):
                    st.session_state['delete_mode_enabled'] = True
                    st.rerun()
                
                if st.session_state.get('delete_mode_enabled', False):
                    player_to_delete = st.selectbox(
                        "削除するプレイヤー",
                        [""] + existing_players,
                        key="delete_player_select"
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if player_to_delete and st.button("削除実行", type="primary", use_container_width=True):
                            delete_player_completely(player_to_delete)
                            st.session_state['delete_mode_enabled'] = False
                            st.rerun()
                    with col2:
                        if st.button("キャンセル", use_container_width=True):
                            st.session_state['delete_mode_enabled'] = False
                            st.rerun()
        else:
            st.info("登録されているプレイヤーはいません")

def delete_player_completely(player_name):
    """プレイヤーを削除（対局記録からは該当プレイヤーのみ除外）"""
    try:
        modified_count = 0
        
        # セッション状態のプレイヤーリストから削除
        if 'registered_players' in st.session_state:
            if player_name in st.session_state['registered_players']:
                st.session_state['registered_players'].remove(player_name)
        
        # 対局記録から該当プレイヤーのみ除外（記録自体は保持）
        if 'game_records' in st.session_state and st.session_state['game_records']:
            for record in st.session_state['game_records']:
                record_modified = False
                
                for i in range(1, 5):
                    name_key = f'player{i}_name'
                    score_key = f'player{i}_score'
                    
                    if record.get(name_key) == player_name:
                        # 該当プレイヤーの情報のみクリア
                        record[name_key] = ''
                        record[score_key] = 0
                        record_modified = True
                
                if record_modified:
                    modified_count += 1
        
        # Google Sheetsからも削除が必要な場合の処理は省略
        # 実際の運用では、Google Sheetsとの同期が必要
        
        if modified_count > 0:
            st.success(f"プレイヤー '{player_name}' を削除しました（{modified_count} 件の対局記録から除外）")
        else:
            st.success(f"プレイヤー '{player_name}' を削除しました")
        
    except Exception as e:
        st.error(f"削除エラー: {e}")

def create_score_input_fields(player_names, default_scores=None, prefix="default"):
    """点数入力フィールド"""
    if default_scores is None:
        default_scores = [25000, 25000, 25000, 25000]
    
    cols = st.columns(4)
    scores = []
    
    for i, (col, name, default_score) in enumerate(zip(cols, player_names, default_scores)):
        with col:
            # プレイヤー名をキャプションとして表示（選択されている場合のみ）
            if name.strip():
                st.caption(name)
            
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
    """対局情報入力フィールド（日本時間対応）"""
    from config_manager import ConfigManager
    
    # 日本時間を取得
    jst = pytz.timezone('Asia/Tokyo')
    now_jst = datetime.now(jst)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        game_date = st.date_input("対局日", value=now_jst.date(), key=f"{prefix}_date")
    
    with col2:
        game_time = st.time_input("対局時刻", value=now_jst.time(), key=f"{prefix}_time")
    
    with col3:
        # デフォルト値を設定から取得
        config_manager = ConfigManager()
        default_game_type = config_manager.get_default_game_type()
        game_types = ["四麻東風", "四麻半荘", "三麻東風", "三麻半荘"]
        default_index = game_types.index(default_game_type) if default_game_type in game_types else 1
        
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
        st.warning("少なくとも1名のプレイヤーを選択してください")
        return False

def save_game_record(player_names, scores, game_date, game_time, game_type, notes=""):
    """対局記録保存（自動同期対応版）"""
    from ui_components import save_game_record_with_names
    
    players_data = []
    for name, score in zip(player_names, scores):
        players_data.append({"name": name.strip(), "score": score})
    
    valid_players = [p for p in players_data if p['name']]
    if len(valid_players) < 1:
        st.error("少なくとも1名のプレイヤーを選択してください")
        return False
    
    return save_game_record_with_names(players_data, game_date, game_time, game_type, notes)