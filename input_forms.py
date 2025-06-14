# input_forms.py - プレイヤーマスタ管理完全対応版
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
                # プレイヤーが未登録の場合は空の選択フィールドを表示
                st.selectbox(
                    "プレイヤー選択",
                    [""],
                    index=0,
                    key=f"{prefix}_player_{i}",
                    label_visibility="collapsed",
                    disabled=True
                )
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
                
                # 解析結果で新しい名前が検出された場合は選択肢に追加
                if default_name and default_name not in existing_players and default_name.strip():
                    options = [""] + existing_players + [f"新規: {default_name}"]
                    if default_name not in existing_players:
                        default_index = len(options) - 1
                else:
                    options = [""] + existing_players
                
                selected_player = st.selectbox(
                    "プレイヤー選択",
                    options,
                    index=default_index,
                    key=f"{prefix}_player_{i}",
                    label_visibility="collapsed"
                )
                
                # 新規プレイヤーが選択された場合の処理
                if selected_player.startswith("新規: "):
                    new_player_name = selected_player.replace("新規: ", "")
                    # セッション状態に新規プレイヤーとして記録
                    if 'pending_new_players' not in st.session_state:
                        st.session_state['pending_new_players'] = []
                    if new_player_name not in st.session_state['pending_new_players']:
                        st.session_state['pending_new_players'].append(new_player_name)
                    player_names.append(new_player_name)
                else:
                    player_names.append(selected_player)
            else:
                # 既存プレイヤーがいない場合
                if default_name and default_name.strip():
                    options = ["", f"新規: {default_name}"]
                    selected_player = st.selectbox(
                        "プレイヤー選択",
                        options,
                        index=1,
                        key=f"{prefix}_player_{i}",
                        label_visibility="collapsed"
                    )
                    
                    if selected_player.startswith("新規: "):
                        new_player_name = selected_player.replace("新規: ", "")
                        if 'pending_new_players' not in st.session_state:
                            st.session_state['pending_new_players'] = []
                        if new_player_name not in st.session_state['pending_new_players']:
                            st.session_state['pending_new_players'].append(new_player_name)
                        player_names.append(new_player_name)
                    else:
                        player_names.append("")
                else:
                    # テキスト入力フィールドとして表示
                    player_name = st.text_input(
                        "プレイヤー名",
                        placeholder="プレイヤー名を入力",
                        key=f"{prefix}_text_player_{i}",
                        label_visibility="collapsed"
                    )
                    if player_name.strip():
                        if 'pending_new_players' not in st.session_state:
                            st.session_state['pending_new_players'] = []
                        if player_name.strip() not in st.session_state['pending_new_players']:
                            st.session_state['pending_new_players'].append(player_name.strip())
                    player_names.append(player_name)
    
    return player_names

def register_new_player(player_name):
    """新しいプレイヤーを登録（設定スプレッドシートに保存）"""
    try:
        # 既存チェック
        existing_players = get_registered_players()
        if player_name.strip() in existing_players:
            st.error(f"'{player_name}' は既に登録されています")
            return
        
        # 設定スプレッドシートに保存
        if save_player_to_config_sheet(player_name.strip()):
            # セッション状態のプレイヤーリストも更新
            if 'master_players' not in st.session_state:
                st.session_state['master_players'] = []
            st.session_state['master_players'].append(player_name.strip())
            
            st.success(f"プレイヤー '{player_name}' を登録しました")
        else:
            st.error(f"プレイヤー登録に失敗しました")
        
    except Exception as e:
        st.error(f"プレイヤー登録エラー: {e}")

def save_player_to_config_sheet(player_name):
    """プレイヤーを設定スプレッドシートに保存"""
    try:
        from config_manager import ConfigManager
        from config_spreadsheet_manager import ConfigSpreadsheetManager
        
        config_manager = ConfigManager()
        sheets_creds = config_manager.load_sheets_credentials()
        
        if not sheets_creds:
            return False
        
        config_sheet_manager = ConfigSpreadsheetManager(sheets_creds)
        if config_sheet_manager.connect():
            return config_sheet_manager.add_player(player_name)
        
        return False
        
    except Exception as e:
        st.error(f"設定スプレッドシート保存エラー: {e}")
        return False

def get_registered_players():
    """登録済みプレイヤーリストを取得（設定スプレッドシート優先）"""
    # 設定スプレッドシートからプレイヤーリストを取得
    master_players = load_players_from_config_sheet()
    
    # 対局記録から抽出したプレイヤー
    game_players = []
    if 'game_records' in st.session_state and st.session_state['game_records']:
        player_manager = PlayerManager(st.session_state['game_records'])
        game_players = player_manager.get_all_player_names()
    
    # 重複を除いて統合（マスタを優先）
    all_players = list(set(master_players + game_players))
    return sorted(all_players)

def load_players_from_config_sheet():
    """設定スプレッドシートからプレイヤーリストを読み込み"""
    try:
        # セッション状態にキャッシュがある場合はそれを使用
        if 'master_players' in st.session_state:
            return st.session_state['master_players']
        
        from config_manager import ConfigManager
        from config_spreadsheet_manager import ConfigSpreadsheetManager
        
        config_manager = ConfigManager()
        sheets_creds = config_manager.load_sheets_credentials()
        
        if not sheets_creds:
            st.session_state['master_players'] = []
            return []
        
        config_sheet_manager = ConfigSpreadsheetManager(sheets_creds)
        if config_sheet_manager.connect():
            players = config_sheet_manager.get_all_players()
            st.session_state['master_players'] = players
            return players
        
        st.session_state['master_players'] = []
        return []
        
    except Exception as e:
        st.session_state['master_players'] = []
        return []

def show_player_management():
    """プレイヤー管理セクション"""
    # 設定スプレッドシートからプレイヤーを読み込み
    master_players = load_players_from_config_sheet()
    
    # 対局記録からもプレイヤーを取得
    if 'game_records' in st.session_state and st.session_state['game_records']:
        player_manager = PlayerManager(st.session_state['game_records'])
        game_players = player_manager.get_all_player_names()
    else:
        game_players = []
    
    # 統合リスト
    all_players = list(set(master_players + game_players))
    all_players.sort()
    
    tab1, tab2 = st.tabs(["プレイヤー登録", "登録済みプレイヤー"])
    
    with tab1:
        with st.form("player_registration_form"):
            new_player_name = st.text_input("プレイヤー名", placeholder="ニックネームを入力")
            submitted = st.form_submit_button("登録")
            
            if submitted and new_player_name.strip():
                if new_player_name.strip() in all_players:
                    st.error(f"'{new_player_name}' は既に登録されています")
                else:
                    register_new_player(new_player_name.strip())
                    st.rerun()
            elif submitted:
                st.error("プレイヤー名を入力してください")
    
    with tab2:
        if all_players:
            # プレイヤーリストを表示
            player_stats = []
            for player_name in all_players:
                if 'game_records' in st.session_state and st.session_state['game_records']:
                    player_manager = PlayerManager(st.session_state['game_records'])
                    stats = player_manager.get_player_statistics(player_name)
                    player_stats.append({
                        "プレイヤー名": player_name,
                        "対局数": stats['total_games']
                    })
                else:
                    player_stats.append({
                        "プレイヤー名": player_name,
                        "対局数": 0
                    })
            
            df = pd.DataFrame(player_stats)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # プレイヤー削除機能
            with st.expander("プレイヤー削除"):
                st.warning("プレイヤーを削除すると、マスタリストと対局記録から完全に除外されます")
                
                if st.button("削除モードを有効にする", key="enable_delete_mode"):
                    st.session_state['delete_mode_enabled'] = True
                    st.rerun()
                
                if st.session_state.get('delete_mode_enabled', False):
                    player_to_delete = st.selectbox(
                        "削除するプレイヤー",
                        [""] + all_players,
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
    """プレイヤーを完全に削除（マスタリスト＋対局記録＋Google Sheets）"""
    try:
        modified_count = 0
        
        with st.spinner("削除中..."):
            # 1. マスタリストから削除
            master_deleted = delete_player_from_config_sheet(player_name)
            
            # 2. セッション状態のマスタリストからも削除
            if 'master_players' in st.session_state:
                if player_name in st.session_state['master_players']:
                    st.session_state['master_players'].remove(player_name)
            
            # 3. 対局記録から該当プレイヤーを除外
            if 'game_records' in st.session_state and st.session_state['game_records']:
                for record in st.session_state['game_records']:
                    record_modified = False
                    
                    for i in range(1, 5):
                        name_key = f'player{i}_name'
                        score_key = f'player{i}_score'
                        
                        if record.get(name_key) == player_name:
                            record[name_key] = ''
                            record[score_key] = 0
                            record_modified = True
                    
                    if record_modified:
                        modified_count += 1
            
            # 4. Google Sheetsからも該当プレイヤー名を削除
            sheets_update_success = update_player_name_in_sheets(player_name, "")
        
        # 結果表示
        success_parts = []
        if master_deleted:
            success_parts.append("マスタリスト")
        if modified_count > 0:
            success_parts.append(f"対局記録({modified_count}件)")
        if sheets_update_success:
            success_parts.append("Google Sheets")
        
        if success_parts:
            st.success(f"プレイヤー '{player_name}' を削除しました: {', '.join(success_parts)}")
            
            # データを再同期
            from config_manager import ConfigManager
            from ui_components import sync_data_from_sheets
            config_manager = ConfigManager()
            sync_data_from_sheets(config_manager)
        else:
            st.error("削除に失敗しました")
        
    except Exception as e:
        st.error(f"削除エラー: {e}")

def delete_player_from_config_sheet(player_name):
    """設定スプレッドシートからプレイヤーを削除"""
    try:
        from config_manager import ConfigManager
        from config_spreadsheet_manager import ConfigSpreadsheetManager
        
        config_manager = ConfigManager()
        sheets_creds = config_manager.load_sheets_credentials()
        
        if not sheets_creds:
            return False
        
        config_sheet_manager = ConfigSpreadsheetManager(sheets_creds)
        if config_sheet_manager.connect():
            return config_sheet_manager.delete_player(player_name)
        
        return False
        
    except Exception as e:
        st.error(f"マスタリスト削除エラー: {e}")
        return False

def update_player_name_in_sheets(old_name, new_name):
    """Google Sheetsで指定されたプレイヤー名を新しい名前に更新"""
    try:
        from config_manager import ConfigManager
        from spreadsheet_manager import SpreadsheetManager
        
        config_manager = ConfigManager()
        sheets_creds = config_manager.load_sheets_credentials()
        spreadsheet_id = config_manager.get_spreadsheet_id()
        
        if not sheets_creds or not spreadsheet_id:
            return False
        
        sheet_manager = SpreadsheetManager(sheets_creds)
        if not sheet_manager.connect(spreadsheet_id):
            return False
        
        success, update_count = sheet_manager.find_and_replace_player_name(old_name, new_name)
        
        if success and update_count > 0:
            st.info(f"Google Sheetsで {update_count} 箇所を更新しました")
        
        return success
        
    except Exception as e:
        st.error(f"Google Sheets更新エラー: {e}")
        return False

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