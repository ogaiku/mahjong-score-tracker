# spreadsheet_manager.py
import gspread
from google.oauth2.service_account import Credentials
from typing import Dict
import streamlit as st

class SpreadsheetManager:
    """Google Spreadsheet管理クラス"""
    
    def __init__(self, credentials_dict: Dict = None):
        self.credentials_dict = credentials_dict
        self.client = None
        self.sheet = None
        
        # Google Sheets APIのスコープ
        self.scopes = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
    
    def connect(self, spreadsheet_id: str) -> bool:
        """スプレッドシートに接続"""
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
            
            # スプレッドシートを開く（最初のシートを使用）
            self.sheet = self.client.open_by_key(spreadsheet_id).sheet1
            
            return True
            
        except Exception as e:
            st.error(f"スプレッドシート接続エラー: {e}")
            return False
    
    def initialize_headers(self) -> bool:
        """ヘッダー行を初期化（初回のみ）"""
        try:
            if not self.sheet:
                return False
            
            # 既存のヘッダーをチェック
            existing_headers = self.sheet.row_values(1)
            
            if not existing_headers:
                # ヘッダー行を設定
                headers = [
                    "対局日", "対局時刻", "対局タイプ",
                    "プレイヤー1名", "プレイヤー1点数",
                    "プレイヤー2名", "プレイヤー2点数", 
                    "プレイヤー3名", "プレイヤー3点数",
                    "プレイヤー4名", "プレイヤー4点数",
                    "メモ", "登録日時"
                ]
                self.sheet.append_row(headers)
                
            return True
            
        except Exception as e:
            st.error(f"ヘッダー初期化エラー: {e}")
            return False
    
    def add_record(self, game_data: Dict) -> bool:
        """対局記録を追加"""
        try:
            if not self.sheet:
                return False
            
            # ヘッダーが存在しない場合は初期化
            self.initialize_headers()
            
            # 記録データを行として追加
            row_data = [
                game_data.get('date', ''),
                game_data.get('time', ''),
                game_data.get('game_type', ''),
                game_data.get('player1_name', ''),
                game_data.get('player1_score', 0),
                game_data.get('player2_name', ''),
                game_data.get('player2_score', 0),
                game_data.get('player3_name', ''),
                game_data.get('player3_score', 0),
                game_data.get('player4_name', ''),
                game_data.get('player4_score', 0),
                game_data.get('notes', ''),
                game_data.get('timestamp', '')
            ]
            
            self.sheet.append_row(row_data)
            return True
            
        except Exception as e:
            st.error(f"記録追加エラー: {e}")
            return False
    
    def get_all_records(self) -> list:
        """全ての記録を取得"""
        try:
            if not self.sheet:
                return []
            
            # 全てのレコードを取得（ヘッダー行を除く）
            records = self.sheet.get_all_records()
            return records
            
        except Exception as e:
            st.error(f"記録取得エラー: {e}")
            return []
    
    def delete_record(self, row_number: int) -> bool:
        """指定した行の記録を削除"""
        try:
            if not self.sheet:
                return False
            
            # 行を削除（ヘッダー行を考慮して+2）
            self.sheet.delete_rows(row_number + 2)
            return True
            
        except Exception as e:
            st.error(f"記録削除エラー: {e}")
            return False