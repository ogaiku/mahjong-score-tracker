# config_manager.py - Streamlit Secrets対応版
import json
import os
from typing import Dict, Optional, Union
import streamlit as st

class ConfigManager:
    """設定ファイルを管理するクラス（Streamlit Secrets対応）"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """設定ファイルまたはStreamlit Secretsから設定を読み込み"""
        # まずStreamlit Secretsから読み込みを試行
        if hasattr(st, 'secrets') and len(st.secrets) > 0:
            return self.load_from_secrets()
        
        # Secretsがない場合は従来のconfig.jsonから読み込み
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 古い設定形式から新しい形式に移行
                if self._needs_migration(config):
                    config = self._migrate_config(config)
                    self.save_config(config)
                
                return config
            except Exception as e:
                st.error(f"設定ファイル読み込みエラー: {e}")
                return self.get_default_config()
        else:
            # 設定ファイルが存在しない場合はデフォルト設定を作成
            default_config = self.get_default_config()
            self.save_config(default_config)
            return default_config
    
    def load_from_secrets(self) -> Dict:
        """Streamlit Secretsから設定を読み込み"""
        try:
            config = {
                "openai": {
                    "api_key": st.secrets.get("openai", {}).get("api_key", "").strip(' "'),
                    "model": "gpt-4o"
                },
                "google_vision": {
                    "api_key": st.secrets.get("google_vision", {}).get("api_key", "").strip(' "'),
                    "credentials_file": ""
                },
                "google_sheets": {
                    "credentials_file": "",
                    "seasons": {
                        "season1": {
                            "name": "mahjong-score-tracker season1",
                            "spreadsheet_id": "1CGkwnN-g6AUjbURXENZJADkmaep88RXq4fj1QQXuEfQ",
                            "url": "https://docs.google.com/spreadsheets/d/1CGkwnN-g6AUjbURXENZJADkmaep88RXq4fj1QQXuEfQ/edit?gid=0#gid=0"
                        }
                    },
                    "current_season": "season1"
                },
                "app": {
                    "default_game_type": "四麻半荘",
                    "auto_save_to_sheets": True
                }
            }
            
            return config
        except Exception as e:
            st.error(f"Secrets読み込みエラー: {e}")
            return self.get_default_config()
    
    def _needs_migration(self, config: Dict) -> bool:
        """設定の移行が必要かチェック"""
        # 古い形式（直接spreadsheet_idがある）かチェック
        sheets_config = config.get("google_sheets", {})
        return "spreadsheet_id" in sheets_config and "seasons" not in sheets_config
    
    def _migrate_config(self, config: Dict) -> Dict:
        """古い設定形式から新しい形式に移行"""
        sheets_config = config.get("google_sheets", {})
        old_spreadsheet_id = sheets_config.get("spreadsheet_id", "")
        
        if old_spreadsheet_id:
            # 古いIDをseason1として移行
            sheets_config["seasons"] = {
                "season1": {
                    "name": "mahjong-score-tracker season1",
                    "spreadsheet_id": old_spreadsheet_id,
                    "url": f"https://docs.google.com/spreadsheets/d/{old_spreadsheet_id}/edit"
                }
            }
            sheets_config["current_season"] = "season1"
            # 古いキーを削除
            del sheets_config["spreadsheet_id"]
        
        return config
    
    def get_default_config(self) -> Dict:
        """デフォルト設定を返す"""
        return {
            "openai": {
                "api_key": "",
                "model": "gpt-4o"
            },
            "google_vision": {
                "api_key": "",
                "credentials_file": ""
            },
            "google_sheets": {
                "credentials_file": "",
                "seasons": {
                    "season1": {
                        "name": "mahjong-score-tracker season1",
                        "spreadsheet_id": "1CGkwnN-g6AUjbURXENZJADkmaep88RXq4fj1QQXuEfQ",
                        "url": "https://docs.google.com/spreadsheets/d/1CGkwnN-g6AUjbURXENZJADkmaep88RXq4fj1QQXuEfQ/edit?gid=0#gid=0"
                    }
                },
                "current_season": "season1"
            },
            "app": {
                "default_game_type": "四麻半荘",
                "auto_save_to_sheets": True
            }
        }
    
    def save_config(self, config: Optional[Dict] = None) -> bool:
        """設定ファイルを保存（Streamlit Cloud環境では無効）"""
        # Streamlit Cloud環境では設定ファイルの保存は行わない
        if hasattr(st, 'secrets') and len(st.secrets) > 0:
            return True
        
        try:
            config_to_save = config if config is not None else self.config
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            st.error(f"設定ファイル保存エラー: {e}")
            return False
    
    def get_openai_api_key(self) -> str:
        """OpenAI API Keyを取得"""
        return self.config.get("openai", {}).get("api_key", "")
    
    def get_vision_api_key(self) -> str:
        """Vision API Keyを取得"""
        return self.config.get("google_vision", {}).get("api_key", "")
    
    def get_vision_credentials_file(self) -> str:
        """Vision API認証ファイルパスを取得"""
        return self.config.get("google_vision", {}).get("credentials_file", "")
    
    def get_sheets_credentials_file(self) -> str:
        """Sheets API認証ファイルパスを取得"""
        return self.config.get("google_sheets", {}).get("credentials_file", "")
    
    def get_spreadsheet_id(self) -> str:
        """現在のシーズンのスプレッドシートIDを取得"""
        current_season = self.get_current_season()
        seasons = self.config.get("google_sheets", {}).get("seasons", {})
        return seasons.get(current_season, {}).get("spreadsheet_id", "")
    
    def get_current_season(self) -> str:
        """現在のシーズンを取得"""
        return self.config.get("google_sheets", {}).get("current_season", "season1")
    
    def get_all_seasons(self) -> Dict:
        """すべてのシーズン情報を取得"""
        return self.config.get("google_sheets", {}).get("seasons", {})
    
    def get_season_info(self, season_key: str) -> Dict:
        """指定したシーズンの情報を取得"""
        seasons = self.get_all_seasons()
        return seasons.get(season_key, {})
    
    def add_season(self, season_key: str, name: str, auto_create: bool = True) -> bool:
        """新しいシーズンを追加（常に自動作成）"""
        try:
            # 既存のシーズンキーをチェック
            existing_seasons = self.get_all_seasons()
            if season_key in existing_seasons:
                st.error(f"シーズンキー '{season_key}' は既に存在します")
                return False
            
            # 自動でスプレッドシートを作成
            result = self._create_new_spreadsheet(name)
            if result['success']:
                spreadsheet_id = result['spreadsheet_id']
                url = result['url']
            else:
                st.error(f"スプレッドシート作成に失敗: {result.get('error', '不明なエラー')}")
                return False
            
            # シーズン情報を追加
            if "google_sheets" not in self.config:
                self.config["google_sheets"] = {}
            if "seasons" not in self.config["google_sheets"]:
                self.config["google_sheets"]["seasons"] = {}
            
            self.config["google_sheets"]["seasons"][season_key] = {
                "name": name,
                "spreadsheet_id": spreadsheet_id,
                "url": url,
                "created_at": self._get_current_timestamp()
            }
            
            return self.save_config()
        except Exception as e:
            st.error(f"シーズン追加エラー: {e}")
            return False
    
    def _create_new_spreadsheet(self, title: str) -> Dict:
        """新しいスプレッドシートを自動作成（公開設定）"""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            # 認証情報を取得
            creds_dict = self.load_sheets_credentials()
            if not creds_dict:
                return {
                    'success': False,
                    'error': "Google Sheets認証情報が見つかりません"
                }
            
            # サービスアカウント認証
            credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
            )
            
            # Google Sheets APIサービス
            sheets_service = build('sheets', 'v4', credentials=credentials)
            drive_service = build('drive', 'v3', credentials=credentials)
            
            # スプレッドシート作成
            spreadsheet_body = {
                'properties': {
                    'title': title
                },
                'sheets': [{
                    'properties': {
                        'title': 'Sheet1'
                    }
                }]
            }
            
            response = sheets_service.spreadsheets().create(body=spreadsheet_body).execute()
            spreadsheet_id = response['spreadsheetId']
            url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
            
            # スプレッドシートを公開設定にする
            try:
                permission = {
                    'type': 'anyone',
                    'role': 'writer'  # 編集可能
                }
                drive_service.permissions().create(
                    fileId=spreadsheet_id,
                    body=permission
                ).execute()
            except Exception as e:
                st.warning(f"公開設定に失敗しましたが、スプレッドシートは作成されました: {e}")
            
            # ヘッダー行を追加
            header_result = self._initialize_spreadsheet_headers(sheets_service, spreadsheet_id)
            if not header_result['success']:
                st.warning(f"ヘッダー初期化に問題がありました: {header_result.get('warning', '')}")
            
            return {
                'success': True,
                'spreadsheet_id': spreadsheet_id,
                'url': url,
                'message': f"新しいスプレッドシート '{title}' を作成しました（公開設定）"
            }
            
        except ImportError:
            return {
                'success': False,
                'error': "google-api-python-clientライブラリが必要です: pip install google-api-python-client"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"スプレッドシート作成エラー: {str(e)}"
            }
    
    def _initialize_spreadsheet_headers(self, sheets_service, spreadsheet_id: str) -> Dict:
        """スプレッドシートにヘッダー行を追加"""
        try:
            headers = [
                "対局日", "対局時刻", "対局タイプ",
                "プレイヤー1名", "プレイヤー1点数",
                "プレイヤー2名", "プレイヤー2点数", 
                "プレイヤー3名", "プレイヤー3点数",
                "プレイヤー4名", "プレイヤー4点数",
                "メモ", "登録日時"
            ]
            
            body = {
                'values': [headers]
            }
            
            sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='A1:M1',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            # ヘッダー行のフォーマット設定
            format_body = {
                'requests': [{
                    'repeatCell': {
                        'range': {
                            'sheetId': 0,
                            'startRowIndex': 0,
                            'endRowIndex': 1
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'backgroundColor': {
                                    'red': 0.9,
                                    'green': 0.9,
                                    'blue': 0.9
                                },
                                'textFormat': {
                                    'bold': True
                                }
                            }
                        },
                        'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                    }
                }]
            }
            
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=format_body
            ).execute()
            
            return {'success': True}
            
        except Exception as e:
            return {
                'success': False,
                'warning': f"ヘッダー初期化に失敗しましたが、スプレッドシートは作成されました: {e}"
            }
    
    def set_current_season(self, season_key: str) -> bool:
        """現在のシーズンを変更"""
        try:
            seasons = self.get_all_seasons()
            if season_key not in seasons:
                st.error(f"シーズン '{season_key}' が見つかりません")
                return False
            
            self.config.setdefault("google_sheets", {})["current_season"] = season_key
            success = self.save_config()
            
            if success:
                # 設定を再読み込み
                self.config = self.load_config()
            
            return success
        except Exception as e:
            st.error(f"シーズン変更エラー: {e}")
            return False
    
    def delete_season(self, season_key: str) -> bool:
        """シーズンを削除（現在のシーズンは削除不可）"""
        try:
            current_season = self.get_current_season()
            if season_key == current_season:
                st.error("現在のシーズンは削除できません")
                return False
            
            seasons = self.get_all_seasons()
            if season_key not in seasons:
                st.error(f"シーズン '{season_key}' が見つかりません")
                return False
            
            # シーズンを削除
            del self.config["google_sheets"]["seasons"][season_key]
            return self.save_config()
            
        except Exception as e:
            st.error(f"シーズン削除エラー: {e}")
            return False
    
    def extract_spreadsheet_id(self, url: str) -> str:
        """スプレッドシートURLからIDを抽出"""
        import re
        # https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/ のパターン
        pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
        match = re.search(pattern, url)
        return match.group(1) if match else ""
    
    def load_vision_credentials(self) -> Optional[Union[Dict, str]]:
        """Vision API認証情報を読み込み（APIキーまたはJSONファイル）"""
        # APIキーが設定されている場合はそれを優先
        api_key = self.get_vision_api_key()
        if api_key:
            return api_key
        
        # JSONファイルを試行
        creds_file = self.get_vision_credentials_file()
        if creds_file and os.path.exists(creds_file):
            try:
                with open(creds_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                st.error(f"Vision API認証ファイル読み込みエラー: {e}")
        return None
    
    def load_sheets_credentials(self) -> Optional[Dict]:
        """Sheets API認証情報を読み込み（Streamlit Secrets対応）"""
        # まずStreamlit Secretsから読み込みを試行
        if hasattr(st, 'secrets') and 'google_sheets' in st.secrets:
            try:
                sheets_secrets = st.secrets['google_sheets']
                
                # private_keyの改行を正しく処理
                private_key = sheets_secrets.get('private_key', '').strip(' "')
                if private_key and '\\n' in private_key:
                    private_key = private_key.replace('\\n', '\n')
                
                credentials_dict = {
                    "type": sheets_secrets.get('type', '').strip(' "'),
                    "project_id": sheets_secrets.get('project_id', '').strip(' "'),
                    "private_key": private_key,
                    "client_email": sheets_secrets.get('client_email', '').strip(' "'),
                    "client_id": "",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
                }
                
                # 必要なフィールドがすべて存在するかチェック
                required_fields = ['type', 'project_id', 'private_key', 'client_email']
                if all(credentials_dict.get(field) for field in required_fields):
                    return credentials_dict
                
            except Exception as e:
                st.error(f"Secrets からGoogle Sheets認証情報読み込みエラー: {e}")
        
        # Secretsがない場合はJSONファイルから読み込み
        creds_file = self.get_sheets_credentials_file()
        if creds_file and os.path.exists(creds_file):
            try:
                with open(creds_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                st.error(f"Sheets API認証ファイル読み込みエラー: {e}")
        else:
            # ファイルが見つからない場合はVision APIの認証情報を試用
            vision_creds = self.load_vision_credentials()
            if isinstance(vision_creds, dict):
                # Vision APIのJSONファイルがSheets APIにも使える場合がある
                return vision_creds
        return None
    
    def get_auto_save_to_sheets(self) -> bool:
        """Google Sheetsへの自動保存設定を取得"""
        return self.config.get("app", {}).get("auto_save_to_sheets", True)
    
    def get_default_game_type(self) -> str:
        """デフォルトの対局タイプを取得"""
        return self.config.get("app", {}).get("default_game_type", "四麻東風")
    
    def update_config(self, section: str, key: str, value) -> bool:
        """設定を更新"""
        try:
            if section not in self.config:
                self.config[section] = {}
            self.config[section][key] = value
            return self.save_config()
        except Exception as e:
            st.error(f"設定更新エラー: {e}")
            return False
    
    def _get_current_timestamp(self) -> str:
        """現在のタイムスタンプを取得"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def get_config_status(self) -> Dict:
        """設定状況を確認"""
        vision_creds = self.load_vision_credentials()
        current_season = self.get_current_season()
        seasons = self.get_all_seasons()
        
        status = {
            "openai_api_key": bool(self.get_openai_api_key()),
            "vision_credentials": bool(vision_creds),
            "vision_auth_type": "api_key" if isinstance(vision_creds, str) else "json_file" if vision_creds else "none",
            "sheets_credentials": bool(self.load_sheets_credentials()),
            "spreadsheet_id": bool(self.get_spreadsheet_id()),
            "current_season": current_season,
            "season_count": len(seasons),
            "seasons": seasons
        }
        return status
    
    def validate_season_data(self, season_key: str) -> Dict:
        """シーズンデータの整合性をチェック"""
        season_info = self.get_season_info(season_key)
        
        if not season_info:
            return {
                'valid': False,
                'errors': [f"シーズン '{season_key}' が見つかりません"]
            }
        
        errors = []
        warnings = []
        
        # 必須フィールドのチェック
        required_fields = ['name', 'spreadsheet_id', 'url']
        for field in required_fields:
            if not season_info.get(field):
                errors.append(f"'{field}' が設定されていません")
        
        # スプレッドシートIDとURLの整合性チェック
        spreadsheet_id = season_info.get('spreadsheet_id', '')
        url = season_info.get('url', '')
        
        if spreadsheet_id and url:
            extracted_id = self.extract_spreadsheet_id(url)
            if extracted_id != spreadsheet_id:
                warnings.append("URLから抽出されるIDと設定されているIDが一致しません")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'info': season_info
        }

def create_config_template():
    """設定ファイルのテンプレートを作成"""
    template = {
        "openai": {
            "api_key": "sk-your-openai-api-key-here",
            "model": "gpt-4o"
        },
        "google_vision": {
            "api_key": "",
            "credentials_file": ""
        },
        "google_sheets": {
            "credentials_file": "sheets_credentials.json",
            "seasons": {
                "season1": {
                    "name": "mahjong-score-tracker season1",
                    "spreadsheet_id": "1CGkwnN-g6AUjbURXENZJADkmaep88RXq4fj1QQXuEfQ",
                    "url": "https://docs.google.com/spreadsheets/d/1CGkwnN-g6AUjbURXENZJADkmaep88RXq4fj1QQXuEfQ/edit?gid=0#gid=0"
                },
                "season2": {
                    "name": "mahjong-score-tracker season2",
                    "spreadsheet_id": "your-season2-spreadsheet-id",
                    "url": "https://docs.google.com/spreadsheets/d/your-season2-spreadsheet-id/edit"
                }
            },
            "current_season": "season1"
        },
        "app": {
            "default_game_type": "四麻半荘",
            "auto_save_to_sheets": True
        }
    }
    
    config_file = "config_template.json"
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        return config_file
    except Exception as e:
        st.error(f"テンプレート作成エラー: {e}")
        return None