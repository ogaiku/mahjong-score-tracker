# config_manager.py - URL指定方式対応版
import json
import os
from typing import Dict, Optional, Union
import streamlit as st

class ConfigManager:
    """設定ファイルを管理するクラス（URL指定方式対応）"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        
        # セッション状態で設定を管理
        if 'config_data' not in st.session_state:
            st.session_state['config_data'] = self.load_config()
        
        self.config = st.session_state['config_data']
    
    def load_config(self) -> Dict:
        """設定ファイルまたはStreamlit Secretsから設定を読み込み"""
        # まずStreamlit Secretsから読み込みを試行
        if hasattr(st, 'secrets') and len(st.secrets) > 0:
            base_config = self.load_from_secrets()
        else:
            # Secretsがない場合は従来のconfig.jsonから読み込み
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        base_config = json.load(f)
                except Exception as e:
                    st.error(f"設定ファイル読み込みエラー: {e}")
                    base_config = self.get_default_config()
            else:
                base_config = self.get_default_config()
        
        # 設定スプレッドシートからシーズン情報を読み込み
        self._load_seasons_from_spreadsheet(base_config)
        
        return base_config
    
    def _load_seasons_from_spreadsheet(self, config: Dict):
        """設定スプレッドシートからシーズン情報を読み込み"""
        try:
            # Google Sheets認証情報が利用可能な場合のみ実行
            sheets_creds = self._get_sheets_credentials_dict(config)
            if not sheets_creds:
                return
            
            from config_spreadsheet_manager import ConfigSpreadsheetManager
            
            config_manager = ConfigSpreadsheetManager(sheets_creds)
            if config_manager.connect():
                user_seasons = config_manager.load_user_seasons()
                
                if user_seasons:
                    # Google Sheetsの設定をローカル設定に統合
                    if "google_sheets" not in config:
                        config["google_sheets"] = {}
                    
                    config["google_sheets"]["seasons"] = user_seasons.get('seasons', {})
                    config["google_sheets"]["current_season"] = user_seasons.get('current_season', '')
                    
                    # セッション状態に保存（設定スプレッドシートとの同期済みフラグ）
                    st.session_state['config_synced_with_spreadsheet'] = True
                else:
                    # 設定スプレッドシートにデータがない場合はローカル設定を維持
                    if "google_sheets" not in config:
                        config["google_sheets"] = {"seasons": {}, "current_season": ""}
                    
        except Exception as e:
            # エラーが発生してもローカル設定は維持
            if "google_sheets" not in config:
                config["google_sheets"] = {"seasons": {}, "current_season": ""}
    
    def _get_sheets_credentials_dict(self, config: Dict) -> Optional[Dict]:
        """Google Sheets認証情報を取得"""
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
                
            except Exception:
                pass
        
        # Secretsがない場合はJSONファイルから読み込み
        creds_file = config.get("google_sheets", {}).get("credentials_file", "")
        if creds_file and os.path.exists(creds_file):
            try:
                with open(creds_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return None
    
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
                    "seasons": {},
                    "current_season": ""
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
    
    def get_default_config(self) -> Dict:
        """デフォルト設定を返す（空のシーズン設定）"""
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
                "seasons": {},
                "current_season": ""
            },
            "app": {
                "default_game_type": "四麻半荘",
                "auto_save_to_sheets": True
            }
        }
    
    def save_config(self, config: Optional[Dict] = None) -> bool:
        """設定を保存（セッション状態とスプレッドシート両方）"""
        config_to_save = config if config is not None else self.config
        
        # セッション状態を更新
        st.session_state['config_data'] = config_to_save
        self.config = config_to_save
        
        # 設定スプレッドシートにシーズン情報を保存
        self._save_seasons_to_spreadsheet(config_to_save)
        
        # Streamlit Cloud環境ではローカルファイル保存しない
        if hasattr(st, 'secrets') and len(st.secrets) > 0:
            return True
        
        # ローカル環境ではファイルにも保存
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            st.error(f"設定ファイル保存エラー: {e}")
            return False
    
    def _save_seasons_to_spreadsheet(self, config: Dict):
        """シーズン情報を設定スプレッドシートに保存"""
        try:
            sheets_creds = self._get_sheets_credentials_dict(config)
            if not sheets_creds:
                return
            
            from config_spreadsheet_manager import ConfigSpreadsheetManager
            
            config_manager = ConfigSpreadsheetManager(sheets_creds)
            if config_manager.connect():
                seasons = config.get("google_sheets", {}).get("seasons", {})
                current_season = config.get("google_sheets", {}).get("current_season", "")
                
                # 各シーズンを設定スプレッドシートに保存
                for season_key, season_info in seasons.items():
                    is_current = (season_key == current_season)
                    config_manager.save_season_config(
                        season_key=season_key,
                        season_name=season_info.get('name', season_key),
                        spreadsheet_id=season_info.get('spreadsheet_id', ''),
                        spreadsheet_url=season_info.get('url', ''),
                        is_current=is_current
                    )
                
        except Exception as e:
            # エラーが発生してもローカル設定は保存
            pass
    
    def add_season(self, season_key: str, name: str, spreadsheet_url: str) -> bool:
        """新しいシーズンを追加（URL指定方式）"""
        try:
            # 既存のシーズンキーをチェック
            existing_seasons = self.get_all_seasons()
            if season_key in existing_seasons:
                st.error(f"シーズンキー '{season_key}' は既に存在します")
                return False
            
            # スプレッドシートIDを抽出
            spreadsheet_id = self.extract_spreadsheet_id(spreadsheet_url)
            if not spreadsheet_id:
                st.error("有効なGoogle SheetsのURLを入力してください")
                return False
            
            # スプレッドシートの接続テストと初期化
            sheets_creds = self.load_sheets_credentials()
            if not sheets_creds:
                st.error("Google Sheets認証情報が設定されていません")
                return False
            
            from spreadsheet_manager import SpreadsheetManager
            sheet_manager = SpreadsheetManager(sheets_creds)
            
            if not sheet_manager.connect(spreadsheet_id):
                st.error("スプレッドシートに接続できません。URLとアクセス権限を確認してください")
                return False
            
            # ヘッダーを初期化
            if not sheet_manager.initialize_headers():
                st.warning("ヘッダーの初期化に失敗しましたが、シーズンは作成されます")
            
            # シーズン情報を追加
            if "google_sheets" not in self.config:
                self.config["google_sheets"] = {}
            if "seasons" not in self.config["google_sheets"]:
                self.config["google_sheets"]["seasons"] = {}
            
            self.config["google_sheets"]["seasons"][season_key] = {
                "name": name,
                "spreadsheet_id": spreadsheet_id,
                "url": spreadsheet_url,
                "created_at": self._get_current_timestamp()
            }
            
            # 初回シーズンの場合は現在のシーズンに設定
            current_season = self.get_current_season()
            if not current_season:
                self.config["google_sheets"]["current_season"] = season_key
            
            # 設定を保存（設定スプレッドシートにも保存される）
            return self.save_config()
        except Exception as e:
            st.error(f"シーズン追加エラー: {e}")
            return False
    
    def set_current_season(self, season_key: str) -> bool:
        """現在のシーズンを変更（設定スプレッドシート対応）"""
        try:
            seasons = self.get_all_seasons()
            if season_key not in seasons:
                st.error(f"シーズン '{season_key}' が見つかりません")
                return False
            
            self.config.setdefault("google_sheets", {})["current_season"] = season_key
            
            # 設定スプレッドシートにも保存
            sheets_creds = self._get_sheets_credentials_dict(self.config)
            if sheets_creds:
                try:
                    from config_spreadsheet_manager import ConfigSpreadsheetManager
                    config_manager = ConfigSpreadsheetManager(sheets_creds)
                    if config_manager.connect():
                        config_manager.set_current_season(season_key)
                except Exception:
                    pass  # エラーが発生してもローカル設定は更新
            
            return self.save_config()
        except Exception as e:
            st.error(f"シーズン変更エラー: {e}")
            return False
    
    def delete_season(self, season_key: str) -> bool:
        """シーズンを削除（設定スプレッドシート対応）"""
        try:
            current_season = self.get_current_season()
            if season_key == current_season:
                st.error("現在のシーズンは削除できません")
                return False
            
            seasons = self.get_all_seasons()
            if season_key not in seasons:
                st.error(f"シーズン '{season_key}' が見つかりません")
                return False
            
            # ローカル設定からシーズンを削除
            del self.config["google_sheets"]["seasons"][season_key]
            
            # 設定スプレッドシートからも削除
            sheets_creds = self._get_sheets_credentials_dict(self.config)
            if sheets_creds:
                try:
                    from config_spreadsheet_manager import ConfigSpreadsheetManager
                    config_manager = ConfigSpreadsheetManager(sheets_creds)
                    if config_manager.connect():
                        config_manager.delete_season(season_key)
                except Exception:
                    pass  # エラーが発生してもローカル設定は更新
            
            return self.save_config()
            
        except Exception as e:
            st.error(f"シーズン削除エラー: {e}")
            return False
    
    # 以下は既存のメソッド（変更なし）
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
        return self.config.get("google_sheets", {}).get("current_season", "")
    
    def get_all_seasons(self) -> Dict:
        """すべてのシーズン情報を取得"""
        return self.config.get("google_sheets", {}).get("seasons", {})
    
    def get_season_info(self, season_key: str) -> Dict:
        """指定したシーズンの情報を取得"""
        seasons = self.get_all_seasons()
        return seasons.get(season_key, {})
    
    def extract_spreadsheet_id(self, url: str) -> str:
        """スプレッドシートURLからIDを抽出"""
        import re
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
        return self._get_sheets_credentials_dict(self.config)
    
    def get_auto_save_to_sheets(self) -> bool:
        """Google Sheetsへの自動保存設定を取得"""
        return self.config.get("app", {}).get("auto_save_to_sheets", True)
    
    def get_default_game_type(self) -> str:
        """デフォルトの対戦タイプを取得"""
        return self.config.get("app", {}).get("default_game_type", "四麻半荘")
    
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
            "seasons": seasons,
            "config_spreadsheet_synced": st.session_state.get('config_synced_with_spreadsheet', False)
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
            "seasons": {},
            "current_season": ""
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