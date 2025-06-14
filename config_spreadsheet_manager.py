# config_spreadsheet_manager.py - プレイヤーマスタ管理機能完全版
import gspread
from google.oauth2.service_account import Credentials
from typing import Dict, List, Optional
import streamlit as st
import json
from datetime import datetime

class ConfigSpreadsheetManager:
    """設定用スプレッドシート管理クラス（プレイヤーマスタ対応）"""
    
    def __init__(self, credentials_dict: Dict = None):
        self.credentials_dict = credentials_dict
        self.client = None
        self.config_sheet = None
        self.player_sheet = None
        
        # 設定用スプレッドシートID（固定）
        self.config_spreadsheet_id = "10UTxzbPu-yARrO0vcyWC8a529zlDYLZRN9d6kqC2w3g"
        
        # Google Sheets APIのスコープ
        self.scopes = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
    
    def connect(self) -> bool:
        """設定用スプレッドシートに接続"""
        try:
            if not self.credentials_dict:
                return False
                
            # サービスアカウント認証情報から認証オブジェクト作成
            credentials = Credentials.from_service_account_info(
                self.credentials_dict,
                scopes=self.scopes
            )
            
            # gspreadクライアント初期化
            self.client = gspread.authorize(credentials)
            
            # 設定用スプレッドシートを開く
            spreadsheet = self.client.open_by_key(self.config_spreadsheet_id)
            
            # シーズン設定シート（既存）
            self.config_sheet = spreadsheet.sheet1
            
            # プレイヤーマスタシートを取得または作成
            try:
                self.player_sheet = spreadsheet.worksheet('プレイヤーマスタ')
            except gspread.WorksheetNotFound:
                # プレイヤーマスタシートが存在しない場合は作成
                self.player_sheet = spreadsheet.add_worksheet(title='プレイヤーマスタ', rows=1000, cols=5)
                self._initialize_player_sheet()
            
            # 初回アクセス時にヘッダーを設定
            self._initialize_headers()
            
            return True
            
        except Exception as e:
            st.error(f"設定スプレッドシート接続エラー: {e}")
            return False
    
    def _initialize_headers(self) -> bool:
        """設定スプレッドシートのヘッダーを初期化"""
        try:
            # 既存のヘッダーをチェック
            existing_headers = self.config_sheet.row_values(1)
            
            if not existing_headers or len(existing_headers) < 7:
                # ヘッダー行を設定
                headers = [
                    "user_id",           # ユーザーID（サービスアカウントのemail）
                    "season_key",        # シーズンキー
                    "season_name",       # シーズン名
                    "spreadsheet_id",    # スプレッドシートID
                    "spreadsheet_url",   # スプレッドシートURL
                    "is_current",        # 現在のシーズンかどうか
                    "created_at",        # 作成日時
                    "updated_at"         # 更新日時
                ]
                self.config_sheet.clear()
                self.config_sheet.append_row(headers)
                
            return True
            
        except Exception as e:
            st.error(f"設定ヘッダー初期化エラー: {e}")
            return False
    
    def _initialize_player_sheet(self) -> bool:
        """プレイヤーマスタシートのヘッダーを初期化"""
        try:
            headers = [
                "user_id",           # ユーザーID（サービスアカウントのemail）
                "player_name",       # プレイヤー名
                "created_at",        # 作成日時
                "updated_at"         # 更新日時
            ]
            self.player_sheet.clear()
            self.player_sheet.append_row(headers)
            return True
            
        except Exception as e:
            st.error(f"プレイヤーシートヘッダー初期化エラー: {e}")
            return False
    
    def get_user_id(self) -> str:
        """ユーザーIDを取得（サービスアカウントのemail）"""
        if self.credentials_dict:
            return self.credentials_dict.get('client_email', 'unknown')
        return 'unknown'
    
    def add_player(self, player_name: str) -> bool:
        """プレイヤーをマスタリストに追加"""
        try:
            if not self.player_sheet:
                if not self.connect():
                    return False
            
            user_id = self.get_user_id()
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 既存チェック
            all_records = self.player_sheet.get_all_records()
            for record in all_records:
                if (record.get('user_id') == user_id and 
                    record.get('player_name') == player_name):
                    return False  # 既に存在する
            
            # 新しいプレイヤーを追加
            new_row_data = [
                user_id,
                player_name,
                current_time,
                current_time
            ]
            
            self.player_sheet.append_row(new_row_data)
            return True
            
        except Exception as e:
            st.error(f"プレイヤー追加エラー: {e}")
            return False
    
    def delete_player(self, player_name: str) -> bool:
        """プレイヤーをマスタリストから削除"""
        try:
            if not self.player_sheet:
                if not self.connect():
                    return False
            
            user_id = self.get_user_id()
            all_records = self.player_sheet.get_all_records()
            
            for i, record in enumerate(all_records):
                if (record.get('user_id') == user_id and 
                    record.get('player_name') == player_name):
                    row_index = i + 2  # ヘッダー行を考慮
                    self.player_sheet.delete_rows(row_index)
                    return True
            
            return False
            
        except Exception as e:
            st.error(f"プレイヤー削除エラー: {e}")
            return False
    
    def get_all_players(self) -> List[str]:
        """ユーザーの全プレイヤーリストを取得"""
        try:
            if not self.player_sheet:
                if not self.connect():
                    return []
            
            user_id = self.get_user_id()
            all_records = self.player_sheet.get_all_records()
            
            players = []
            for record in all_records:
                if record.get('user_id') == user_id:
                    player_name = record.get('player_name')
                    if player_name:
                        players.append(player_name)
            
            return sorted(players)
            
        except Exception as e:
            st.error(f"プレイヤーリスト取得エラー: {e}")
            return []
    
    def update_player(self, old_name: str, new_name: str) -> bool:
        """プレイヤー名を更新"""
        try:
            if not self.player_sheet:
                if not self.connect():
                    return False
            
            user_id = self.get_user_id()
            all_records = self.player_sheet.get_all_records()
            
            for i, record in enumerate(all_records):
                if (record.get('user_id') == user_id and 
                    record.get('player_name') == old_name):
                    row_index = i + 2  # ヘッダー行を考慮
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # プレイヤー名と更新日時を更新
                    self.player_sheet.update_cell(row_index, 2, new_name)      # player_name列
                    self.player_sheet.update_cell(row_index, 4, current_time)  # updated_at列
                    
                    return True
            
            return False
            
        except Exception as e:
            st.error(f"プレイヤー更新エラー: {e}")
            return False
    
    def player_exists(self, player_name: str) -> bool:
        """プレイヤーが存在するかチェック"""
        try:
            if not self.player_sheet:
                if not self.connect():
                    return False
            
            user_id = self.get_user_id()
            all_records = self.player_sheet.get_all_records()
            
            for record in all_records:
                if (record.get('user_id') == user_id and 
                    record.get('player_name') == player_name):
                    return True
            
            return False
            
        except Exception as e:
            st.error(f"プレイヤー存在チェックエラー: {e}")
            return False
    
    def get_player_info(self, player_name: str) -> Optional[Dict]:
        """プレイヤー情報を取得"""
        try:
            if not self.player_sheet:
                if not self.connect():
                    return None
            
            user_id = self.get_user_id()
            all_records = self.player_sheet.get_all_records()
            
            for record in all_records:
                if (record.get('user_id') == user_id and 
                    record.get('player_name') == player_name):
                    return {
                        'name': record.get('player_name'),
                        'created_at': record.get('created_at'),
                        'updated_at': record.get('updated_at')
                    }
            
            return None
            
        except Exception as e:
            st.error(f"プレイヤー情報取得エラー: {e}")
            return None
    
    # 既存のシーズン管理メソッド
    def save_season_config(self, season_key: str, season_name: str, 
                          spreadsheet_id: str, spreadsheet_url: str, 
                          is_current: bool = False) -> bool:
        """シーズン設定を保存"""
        try:
            if not self.config_sheet:
                if not self.connect():
                    return False
            
            user_id = self.get_user_id()
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 既存の記録をチェック
            all_records = self.config_sheet.get_all_records()
            existing_row = None
            row_index = None
            
            for i, record in enumerate(all_records):
                if (record.get('user_id') == user_id and 
                    record.get('season_key') == season_key):
                    existing_row = record
                    row_index = i + 2  # ヘッダー行を考慮
                    break
            
            # 現在のシーズンに設定する場合は、他のシーズンの current フラグを削除
            if is_current:
                self._unset_current_seasons(user_id)
            
            new_row_data = [
                user_id,
                season_key,
                season_name,
                spreadsheet_id,
                spreadsheet_url,
                "TRUE" if is_current else "FALSE",
                existing_row.get('created_at', current_time) if existing_row else current_time,
                current_time
            ]
            
            if existing_row and row_index:
                # 既存の記録を更新
                for col, value in enumerate(new_row_data, 1):
                    self.config_sheet.update_cell(row_index, col, value)
            else:
                # 新しい記録を追加
                self.config_sheet.append_row(new_row_data)
            
            return True
            
        except Exception as e:
            st.error(f"シーズン設定保存エラー: {e}")
            return False
    
    def _unset_current_seasons(self, user_id: str):
        """指定ユーザーの全シーズンの current フラグを削除"""
        try:
            all_records = self.config_sheet.get_all_records()
            
            for i, record in enumerate(all_records):
                if (record.get('user_id') == user_id and 
                    record.get('is_current') == True):
                    row_index = i + 2  # ヘッダー行を考慮
                    self.config_sheet.update_cell(row_index, 6, "FALSE")  # is_current列
                    
        except Exception as e:
            st.error(f"current フラグ削除エラー: {e}")
    
    def load_user_seasons(self) -> Dict:
        """ユーザーのシーズン設定を読み込み"""
        try:
            if not self.config_sheet:
                if not self.connect():
                    return {}
            
            user_id = self.get_user_id()
            all_records = self.config_sheet.get_all_records()
            
            seasons = {}
            current_season = ""
            
            for record in all_records:
                if record.get('user_id') == user_id:
                    season_key = record.get('season_key')
                    if season_key:
                        seasons[season_key] = {
                            'name': record.get('season_name', season_key),
                            'spreadsheet_id': record.get('spreadsheet_id', ''),
                            'url': record.get('spreadsheet_url', ''),
                            'created_at': record.get('created_at', ''),
                            'updated_at': record.get('updated_at', '')
                        }
                        
                        # 現在のシーズンをチェック
                        if record.get('is_current') in [True, 'TRUE', 'true']:
                            current_season = season_key
            
            return {
                'seasons': seasons,
                'current_season': current_season
            }
            
        except Exception as e:
            st.error(f"シーズン設定読み込みエラー: {e}")
            return {}
    
    def set_current_season(self, season_key: str) -> bool:
        """現在のシーズンを設定"""
        try:
            if not self.config_sheet:
                if not self.connect():
                    return False
            
            user_id = self.get_user_id()
            
            # まず全ての current フラグを削除
            self._unset_current_seasons(user_id)
            
            # 指定されたシーズンを current に設定
            all_records = self.config_sheet.get_all_records()
            
            for i, record in enumerate(all_records):
                if (record.get('user_id') == user_id and 
                    record.get('season_key') == season_key):
                    row_index = i + 2  # ヘッダー行を考慮
                    self.config_sheet.update_cell(row_index, 6, "TRUE")  # is_current列
                    # 更新日時も更新
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.config_sheet.update_cell(row_index, 8, current_time)  # updated_at列
                    return True
            
            return False
            
        except Exception as e:
            st.error(f"現在シーズン設定エラー: {e}")
            return False
    
    def delete_season(self, season_key: str) -> bool:
        """シーズンを削除"""
        try:
            if not self.config_sheet:
                if not self.connect():
                    return False
            
            user_id = self.get_user_id()
            all_records = self.config_sheet.get_all_records()
            
            for i, record in enumerate(all_records):
                if (record.get('user_id') == user_id and 
                    record.get('season_key') == season_key):
                    row_index = i + 2  # ヘッダー行を考慮
                    self.config_sheet.delete_rows(row_index)
                    return True
            
            return False
            
        except Exception as e:
            st.error(f"シーズン削除エラー: {e}")
            return False
    
    def get_season_info(self, season_key: str) -> Optional[Dict]:
        """特定のシーズン情報を取得"""
        try:
            user_seasons = self.load_user_seasons()
            return user_seasons.get('seasons', {}).get(season_key)
            
        except Exception as e:
            st.error(f"シーズン情報取得エラー: {e}")
            return None
    
    def validate_connection(self) -> bool:
        """設定スプレッドシートへの接続をテスト"""
        try:
            if not self.config_sheet:
                if not self.connect():
                    return False
            
            # 単純な読み取りテスト
            headers = self.config_sheet.row_values(1)
            return len(headers) > 0
            
        except Exception as e:
            return False
    
    def get_statistics(self) -> Dict:
        """統計情報を取得"""
        try:
            user_id = self.get_user_id()
            
            # シーズン統計
            seasons_data = self.load_user_seasons()
            seasons_count = len(seasons_data.get('seasons', {}))
            
            # プレイヤー統計
            players = self.get_all_players()
            players_count = len(players)
            
            return {
                'user_id': user_id,
                'seasons_count': seasons_count,
                'current_season': seasons_data.get('current_season', ''),
                'players_count': players_count,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            st.error(f"統計情報取得エラー: {e}")
            return {}