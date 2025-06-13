# score_extractor.py - Streamlit Cloud対応版
import numpy as np
import re
import json
import base64
from typing import List, Dict, Optional, Union
import streamlit as st
from PIL import Image, ImageEnhance
import io
import openai
import requests

class MahjongScoreExtractor:
    """雀魂スクリーンショットからニックネームと点数を抽出するクラス"""
    
    def __init__(self, vision_credentials: Union[Dict, str], openai_api_key: str):
        self.vision_credentials = vision_credentials
        self.openai_api_key = openai_api_key
        self.vision_client = None
        
        # Vision API認証方式を判定
        if isinstance(vision_credentials, str):
            # APIキー認証
            self.vision_api_key = vision_credentials
            self.use_api_key = True
        else:
            # サービスアカウント認証
            self.use_api_key = False
            self._initialize_vision_client()
    
    def _initialize_vision_client(self):
        """Google Vision APIクライアントを初期化（サービスアカウント用）"""
        try:
            from google.cloud import vision
            from google.oauth2 import service_account
            
            credentials = service_account.Credentials.from_service_account_info(
                self.vision_credentials
            )
            self.vision_client = vision.ImageAnnotatorClient(credentials=credentials)
        except ImportError:
            st.error("google-cloud-visionライブラリがインストールされていません")
            raise
    
    def preprocess_image_for_vision(self, image: np.ndarray) -> bytes:
        """Vision API用に画像を前処理して精度を向上（CV2を使わない版）"""
        # PILImageに変換
        if len(image.shape) == 3:
            pil_image = Image.fromarray(image.astype('uint8'))
        else:
            pil_image = Image.fromarray(image.astype('uint8'), mode='L')
        
        # 解像度向上（小さい画像の場合は拡大）
        width, height = pil_image.size
        if width < 1000:
            scale_factor = 1000 / width
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            # Streamlit Cloud対応: リサンプリング方法を変更
            try:
                pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            except AttributeError:
                # 古いPillowバージョン対応
                pil_image = pil_image.resize((new_width, new_height), Image.LANCZOS)
        
        # コントラスト調整
        enhancer = ImageEnhance.Contrast(pil_image)
        pil_image = enhancer.enhance(1.3)
        
        # 明度調整
        brightness_enhancer = ImageEnhance.Brightness(pil_image)
        pil_image = brightness_enhancer.enhance(1.1)
        
        # バイト形式に変換
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
    
    def extract_text_with_vision_api_key(self, image: np.ndarray) -> str:
        """Google Vision API（APIキー認証）でテキスト抽出"""
        try:
            # 画像を前処理
            image_bytes = self.preprocess_image_for_vision(image)
            
            # Base64エンコード
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Vision API REST リクエスト
            url = f"https://vision.googleapis.com/v1/images:annotate?key={self.vision_api_key}"
            
            payload = {
                "requests": [{
                    "image": {
                        "content": image_base64
                    },
                    "features": [{
                        "type": "TEXT_DETECTION",
                        "maxResults": 50
                    }],
                    "imageContext": {
                        "languageHints": ["ja", "en"]
                    }
                }]
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # エラーチェック
            if 'error' in result:
                raise Exception(f"Vision API エラー: {result['error']['message']}")
            
            # テキスト抽出
            responses = result.get('responses', [])
            if responses and 'textAnnotations' in responses[0]:
                text_annotations = responses[0]['textAnnotations']
                if text_annotations:
                    return text_annotations[0]['description']
            
            return ""
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Vision API リクエストエラー: {e}")
        except Exception as e:
            raise Exception(f"Vision API エラー: {e}")
    
    def extract_text_with_vision_client(self, image: np.ndarray) -> str:
        """Google Vision API（サービスアカウント認証）でテキスト抽出"""
        try:
            from google.cloud import vision
            
            # 画像を前処理
            image_bytes = self.preprocess_image_for_vision(image)
            
            # Vision APIリクエスト
            image_obj = vision.Image(content=image_bytes)
            
            # テキスト検出（日本語と英語対応）
            response = self.vision_client.text_detection(
                image=image_obj,
                image_context=vision.ImageContext(
                    language_hints=['ja', 'en']
                )
            )
            
            # エラーチェック
            if response.error.message:
                raise Exception(f'Vision API エラー: {response.error.message}')
            
            # テキスト抽出
            texts = response.text_annotations
            if texts:
                return texts[0].description
            else:
                return ""
        except Exception as e:
            raise Exception(f"Vision API エラー: {e}")
    
    def extract_text_with_vision_api(self, image: np.ndarray) -> str:
        """Vision APIでテキスト抽出（認証方式に応じて分岐）"""
        if self.use_api_key:
            return self.extract_text_with_vision_api_key(image)
        else:
            return self.extract_text_with_vision_client(image)
    
    def analyze_with_chatgpt(self, extracted_text: str, image_base64: str) -> Dict:
        """ChatGPT APIで画像とテキストを解析"""
        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            prompt = f"""
麻雀アプリ「雀魂」のスクリーンショットから、4名のプレイヤーのニックネームと点数を抽出してください。

抽出されたテキスト:
{extracted_text}

以下のJSON形式で結果を返してください:
{{
    "players": [
        {{"nickname": "プレイヤー名1", "score": 点数1}},
        {{"nickname": "プレイヤー名2", "score": 点数2}},
        {{"nickname": "プレイヤー名3", "score": 点数3}},
        {{"nickname": "プレイヤー名4", "score": 点数4}}
    ],
    "confidence": 0.9,
    "notes": "解析メモ"
}}

注意事項:
- 点数は通常25,000点から開始し、-50,000から+100,000の範囲
- プレイヤーが4名未満の場合は空のnicknameで埋める
- JSONのみを返してください
"""

            # ChatGPT APIリクエスト
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.1  # 一貫性を高めるため低い温度設定
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # JSON抽出
            try:
                # JSONブロックを探す
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result_json = json.loads(json_match.group())
                    return result_json
                else:
                    raise Exception("JSONレスポンスが見つかりません")
            except json.JSONDecodeError as e:
                raise Exception(f"JSON解析エラー: {e}")
        except Exception as e:
            raise Exception(f"ChatGPT API エラー: {e}")
    
    def image_to_base64(self, image: np.ndarray) -> str:
        """画像をBase64エンコード"""
        # numpy配列をPIL Imageに変換
        if image.dtype != np.uint8:
            image = image.astype(np.uint8)
        
        pil_image = Image.fromarray(image)
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def analyze_image(self, image: np.ndarray) -> Dict:
        """メイン解析関数"""
        try:
            # Step 1: Google Vision APIでテキスト抽出
            with st.spinner("画像からテキストを抽出中..."):
                extracted_text = self.extract_text_with_vision_api(image)
            
            if not extracted_text.strip():
                return {
                    'success': False,
                    'message': 'テキストが検出されませんでした',
                    'players': [],
                    'extracted_text': '',
                    'confidence': 0.0
                }
            
            # Step 2: 画像をBase64エンコード
            with st.spinner("画像を処理中..."):
                image_base64 = self.image_to_base64(image)
            
            # Step 3: ChatGPT APIで解析
            with st.spinner("AIが画像を解析中..."):
                ai_result = self.analyze_with_chatgpt(extracted_text, image_base64)
            
            # プレイヤーデータが4名未満の場合は空データで埋める
            players = ai_result.get('players', [])
            while len(players) < 4:
                players.append({'nickname': '', 'score': 25000})
            
            # 4名を超える場合は切り詰め
            players = players[:4]
            
            return {
                'success': True,
                'message': '解析完了',
                'players': players,
                'extracted_text': extracted_text,
                'confidence': ai_result.get('confidence', 0.8),
                'notes': ai_result.get('notes', '')
            }
            
        except Exception as e:
            error_message = str(e)
            st.error(f"解析エラー: {error_message}")
            
            return {
                'success': False,
                'message': f'解析エラー: {error_message}',
                'players': [
                    {'nickname': '', 'score': 25000},
                    {'nickname': '', 'score': 25000},
                    {'nickname': '', 'score': 25000},
                    {'nickname': '', 'score': 25000}
                ],
                'extracted_text': '',
                'confidence': 0.0
            }