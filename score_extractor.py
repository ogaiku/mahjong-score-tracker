# score_extractor.py
import cv2
import numpy as np
import pytesseract
import re
from typing import List
import streamlit as st

class MahjongScoreExtractor:
    """雀魂スクリーンショットからニックネームと点数を抽出するクラス"""
    
    def __init__(self):
        self.score_patterns = [
            r'([+\-]?\d{1,3}(?:,\d{3})*)',  # 通常の点数パターン (例: 25,000, -6200)
            r'([+\-]?\d{4,6})',             # 4-6桁の数字 (例: 25000, -6200)
            r'([+\-]?\d{1,3}k)',            # k表記 (例: 25k)
        ]
        
        # ニックネーム抽出用パターン
        self.nickname_patterns = [
            r'([A-Za-z0-9_]+)',      # 英数字とアンダースコア
            r'([^\s\d+\-.,]+)',      # 空白、数字、記号以外の文字列
        ]
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """画像の前処理でOCR精度を向上"""
        # グレースケール変換
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        # コントラストを適応的に調整
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # メディアンフィルタでノイズ除去
        denoised = cv2.medianBlur(enhanced, 3)
        
        # Otsu法による自動二値化
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary
    
    def extract_text_from_image(self, image: np.ndarray) -> str:
        """Tesseract OCRを使用してテキストを抽出"""
        processed_image = self.preprocess_image(image)
        
        # Tesseract設定（ニックネームと点数両方を認識）
        # 英数字、日本語、記号を含む文字セット
        config = '--oem 3 --psm 6'
        
        try:
            # 日本語+英語で認識
            text = pytesseract.image_to_string(processed_image, config=config, lang='jpn+eng')
            return text
        except Exception as e:
            st.error(f"OCR処理エラー: {e}")
            return ""
    
    def extract_nicknames(self, text: str) -> List[str]:
        """抽出したテキストからニックネームを特定"""
        nicknames = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 既知のニックネームパターンをチェック
            known_names = ['SHIROKUMA3', 'rosuka_jp', 'ogaiku', 'Kawariku']
            for name in known_names:
                if name in line:
                    nicknames.append(name)
                    continue
            
            # 一般的なニックネームパターンで抽出
            for pattern in self.nickname_patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    # フィルタリング条件
                    if (len(match) >= 3 and 
                        not match.isdigit() and 
                        not re.match(r'^[+\-\d,\.]+$', match)):
                        nicknames.append(match)
        
        # 重複除去と結果返却
        return list(set(nicknames))
    
    def extract_scores(self, text: str) -> List[int]:
        """抽出したテキストから麻雀の点数を特定"""
        scores = []
        
        for pattern in self.score_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    # k表記の処理 (25k → 25000)
                    if 'k' in match.lower():
                        score = int(match.lower().replace('k', '').replace('+', '').replace('-', '')) * 1000
                        if match.startswith('-'):
                            score = -score
                    else:
                        # カンマを除去して数値化
                        score = int(match.replace(',', '').replace('+', ''))
                    
                    # 麻雀の点数として妥当な範囲かチェック (-100,000 ~ 200,000点)
                    if -100000 <= score <= 200000:
                        scores.append(score)
                except ValueError:
                    continue
        
        # 重複を除去して返す
        return list(set(scores))
    
    def analyze_image(self, image: np.ndarray) -> dict:
        """画像を解析してニックネームと点数を返す"""
        # テキスト抽出
        extracted_text = self.extract_text_from_image(image)
        
        # ニックネーム抽出
        nicknames = self.extract_nicknames(extracted_text)
        
        # 点数抽出
        scores = self.extract_scores(extracted_text)
        
        return {
            'extracted_text': extracted_text,
            'nicknames': nicknames,
            'scores': scores,
            'nickname_count': len(nicknames),
            'score_count': len(scores)
        }