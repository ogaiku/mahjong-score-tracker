/**
 * アプリケーション設定ファイル
 * 
 * このファイルを編集して、GAS Web AppのURLとGoogleフォームのURLを設定してください
 */

const APP_CONFIG = {
  // GAS Web App URL（デプロイ後に取得）
  // 例: 'https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec'
  GAS_API_URL: 'YOUR_GAS_WEB_APP_URL_HERE',
  
  // Googleフォーム URL（対戦記録入力用）
  // 例: 'https://docs.google.com/forms/d/e/YOUR_FORM_ID/viewform'
  GAME_FORM_URL: 'YOUR_GAME_FORM_URL_HERE',
  
  // Googleフォーム URL（プレイヤー管理用）
  PLAYER_FORM_URL: 'YOUR_PLAYER_FORM_URL_HERE',
  
  // デフォルト設定
  DEFAULT_RECENT_GAMES_LIMIT: 20,
  REFRESH_INTERVAL: 60000, // 60秒（自動更新間隔）
  
  // デバッグモード
  DEBUG_MODE: false
};

// URLが設定されているかチェック
function checkConfig() {
  if (APP_CONFIG.GAS_API_URL === 'YOUR_GAS_WEB_APP_URL_HERE') {
    console.warn('⚠️ GAS Web App URLが設定されていません。config.jsを編集してください。');
    return false;
  }
  return true;
}
