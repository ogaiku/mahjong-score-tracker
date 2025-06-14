# spreadsheet_manager.py - プレイヤー名一括更新機能完全版
import gspread
from google.oauth2.service_account import Credentials
from typing import Dict, List, Tuple
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
    
    def batch_update_player_names(self, old_name: str, new_name: str) -> Tuple[bool, int]:
        """指定されたプレイヤー名を一括で新しい名前に更新"""
        try:
            if not self.sheet:
                return False, 0
            
            # シートの全データを取得
            all_values = self.sheet.get_all_values()
            
            if not all_values:
                return False, 0
            
            # ヘッダー行を除いて処理
            headers = all_values[0] if all_values else []
            data_rows = all_values[1:] if len(all_values) > 1 else []
            
            # プレイヤー名のカラムインデックスを特定
            player_name_columns = []
            for i, header in enumerate(headers):
                if any(keyword in header for keyword in ["プレイヤー1名", "プレイヤー2名", "プレイヤー3名", "プレイヤー4名"]):
                    player_name_columns.append(i)
            
            if not player_name_columns:
                return False, 0
            
            # 更新するセルを特定
            updates = []
            update_count = 0
            
            for row_idx, row in enumerate(data_rows):
                for col_idx in player_name_columns:
                    if col_idx < len(row) and row[col_idx] == old_name:
                        # セルの位置を計算（1-based index + ヘッダー行考慮）
                        cell_address = f"{self._column_index_to_letter(col_idx + 1)}{row_idx + 2}"
                        updates.append({
                            'range': cell_address,
                            'values': [[new_name]]
                        })
                        update_count += 1
            
            # 一括更新を実行
            if updates:
                # gspreadのbatch_update機能を使用
                batch_data = []
                for update in updates:
                    batch_data.append({
                        'range': update['range'],
                        'values': update['values']
                    })
                
                self.sheet.batch_update(batch_data)
                return True, update_count
            else:
                # 該当するプレイヤー名が見つからない場合
                return True, 0
                
        except Exception as e:
            st.error(f"プレイヤー名一括更新エラー: {e}")
            return False, 0
    
    def _column_index_to_letter(self, column_index: int) -> str:
        """カラムインデックス（1-based）をアルファベットに変換"""
        column_letter = ""
        while column_index > 0:
            column_index -= 1
            column_letter = chr(column_index % 26 + ord('A')) + column_letter
            column_index //= 26
        return column_letter
    
    def find_and_replace_player_name(self, old_name: str, new_name: str) -> Tuple[bool, int]:
        """プレイヤー名を検索して置換し、更新件数を返す"""
        try:
            if not self.sheet:
                return False, 0
            
            # まずgspreadのfind_replace機能を試行
            try:
                # 検索・置換を実行
                updated_cells = self.sheet.find_replace(old_name, new_name)
                if updated_cells is not None:
                    return True, len(updated_cells)
                else:
                    return True, 0
                    
            except (AttributeError, TypeError):
                # find_replace機能が利用できない場合はbatch_updateを使用
                return self.batch_update_player_names(old_name, new_name)
                
        except Exception as e:
            st.error(f"プレイヤー名検索・置換エラー: {e}")
            return False, 0
    
    def get_player_name_statistics(self) -> Dict[str, int]:
        """各プレイヤー名の出現回数を取得"""
        try:
            if not self.sheet:
                return {}
            
            all_values = self.sheet.get_all_values()
            
            if not all_values:
                return {}
            
            headers = all_values[0] if all_values else []
            data_rows = all_values[1:] if len(all_values) > 1 else []
            
            # プレイヤー名のカラムインデックスを特定
            player_name_columns = []
            for i, header in enumerate(headers):
                if any(keyword in header for keyword in ["プレイヤー1名", "プレイヤー2名", "プレイヤー3名", "プレイヤー4名"]):
                    player_name_columns.append(i)
            
            # プレイヤー名の出現回数をカウント
            player_counts = {}
            for row in data_rows:
                for col_idx in player_name_columns:
                    if col_idx < len(row) and row[col_idx].strip():
                        player_name = row[col_idx].strip()
                        player_counts[player_name] = player_counts.get(player_name, 0) + 1
            
            return player_counts
            
        except Exception as e:
            st.error(f"プレイヤー統計取得エラー: {e}")
            return {}
    
    def validate_sheet_structure(self) -> Dict:
        """シートの構造を検証"""
        try:
            if not self.sheet:
                return {'valid': False, 'error': 'シートに接続されていません'}
            
            headers = self.sheet.row_values(1)
            
            expected_headers = [
                "対局日", "対局時刻", "対局タイプ",
                "プレイヤー1名", "プレイヤー1点数",
                "プレイヤー2名", "プレイヤー2点数", 
                "プレイヤー3名", "プレイヤー3点数",
                "プレイヤー4名", "プレイヤー4点数",
                "メモ", "登録日時"
            ]
            
            if not headers:
                return {'valid': False, 'error': 'ヘッダー行が見つかりません'}
            
            missing_headers = []
            for expected in expected_headers:
                if expected not in headers:
                    missing_headers.append(expected)
            
            if missing_headers:
                return {
                    'valid': False, 
                    'error': f'不足しているヘッダー: {", ".join(missing_headers)}'
                }
            
            return {
                'valid': True,
                'headers': headers,
                'row_count': len(self.sheet.get_all_values()) - 1  # ヘッダー行を除く
            }
            
        except Exception as e:
            return {'valid': False, 'error': f'検証エラー: {e}'}
    
    def update_cell(self, row: int, col: int, value) -> bool:
        """指定されたセルを更新"""
        try:
            if not self.sheet:
                return False
            
            self.sheet.update_cell(row, col, value)
            return True
            
        except Exception as e:
            st.error(f"セル更新エラー: {e}")
            return False
    
    def update_range(self, range_name: str, values: List[List]) -> bool:
        """指定された範囲を更新"""
        try:
            if not self.sheet:
                return False
            
            self.sheet.update(range_name, values)
            return True
            
        except Exception as e:
            st.error(f"範囲更新エラー: {e}")
            return False
    
    def clear_range(self, range_name: str) -> bool:
        """指定された範囲をクリア"""
        try:
            if not self.sheet:
                return False
            
            self.sheet.batch_clear([range_name])
            return True
            
        except Exception as e:
            st.error(f"範囲クリアエラー: {e}")
            return False
    
    def get_worksheet_info(self) -> Dict:
        """ワークシート情報を取得"""
        try:
            if not self.sheet:
                return {}
            
            return {
                'title': self.sheet.title,
                'row_count': self.sheet.row_count,
                'col_count': self.sheet.col_count,
                'id': self.sheet.id,
                'url': self.sheet.url
            }
            
        except Exception as e:
            st.error(f"ワークシート情報取得エラー: {e}")
            return {}
    
    def backup_sheet_data(self) -> List[List]:
        """シートデータの完全バックアップを取得"""
        try:
            if not self.sheet:
                return []
            
            return self.sheet.get_all_values()
            
        except Exception as e:
            st.error(f"バックアップ取得エラー: {e}")
            return []
    
    def restore_sheet_data(self, backup_data: List[List]) -> bool:
        """バックアップからシートデータを復元"""
        try:
            if not self.sheet or not backup_data:
                return False
            
            # シートをクリア
            self.sheet.clear()
            
            # データを復元
            if backup_data:
                # 一括でデータを更新
                end_col = chr(ord('A') + len(backup_data[0]) - 1) if backup_data[0] else 'A'
                range_name = f"A1:{end_col}{len(backup_data)}"
                self.sheet.update(range_name, backup_data)
            
            return True
            
        except Exception as e:
            st.error(f"データ復元エラー: {e}")
            return False