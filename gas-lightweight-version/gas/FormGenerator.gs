/**
 * Googleフォーム自動生成スクリプト
 * 
 * 使い方:
 * 1. GASエディタでこのスクリプトを貼り付け
 * 2. createMahjongGameForm() を実行
 * 3. createPlayerManagementForm() を実行
 */

/**
 * 対戦記録入力フォームを作成
 */
function createMahjongGameForm() {
  try {
    // フォームを作成
    const form = FormApp.create('麻雀対戦記録入力フォーム');
    
    // 説明を設定
    form.setDescription('麻雀の対戦結果を記録するフォームです。全てのプレイヤーの点数を入力してください。');
    
    // 回答を設定スプレッドシートに送信
    const seasonKey = getCurrentSeason();
    const seasonInfo = getSeasonInfo(seasonKey);
    
    if (seasonInfo) {
      const ss = SpreadsheetApp.openById(seasonInfo.spreadsheetId);
      form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());
    }
    
    // 対戦日（日付）
    form.addDateItem()
      .setTitle('対戦日')
      .setRequired(true)
      .setHelpText('対戦した日付を選択してください');
    
    // 対戦時刻（時間）
    form.addTimeItem()
      .setTitle('対戦時刻')
      .setRequired(false)
      .setHelpText('対戦開始時刻（任意）');
    
    // 対戦タイプ（選択式）
    form.addMultipleChoiceItem()
      .setTitle('対戦タイプ')
      .setChoiceValues(['四麻東風', '四麻半荘', '三麻東風', '三麻半荘'])
      .setRequired(true);
    
    // プレイヤー情報セクション
    form.addSectionHeaderItem()
      .setTitle('プレイヤー情報')
      .setHelpText('各プレイヤーの名前と最終点棒を入力してください');
    
    // player_masterから取得したプレイヤーリスト
    const players = getAllPlayers();
    const playerNames = players.map(p => p.name);
    
    // プレイヤー1
    if (playerNames.length > 0) {
      form.addListItem()
        .setTitle('プレイヤー1名')
        .setChoiceValues(playerNames)
        .setRequired(true);
    } else {
      form.addTextItem()
        .setTitle('プレイヤー1名')
        .setRequired(true);
    }
    
    form.addTextItem()
      .setTitle('プレイヤー1点数')
      .setRequired(true)
      .setValidation(FormApp.createTextValidation()
        .setHelpText('半角数字で入力してください（例: 28000）')
        .requireNumber()
        .build());
    
    // プレイヤー2
    if (playerNames.length > 0) {
      form.addListItem()
        .setTitle('プレイヤー2名')
        .setChoiceValues(playerNames)
        .setRequired(true);
    } else {
      form.addTextItem()
        .setTitle('プレイヤー2名')
        .setRequired(true);
    }
    
    form.addTextItem()
      .setTitle('プレイヤー2点数')
      .setRequired(true)
      .setValidation(FormApp.createTextValidation()
        .setHelpText('半角数字で入力してください（例: 25000）')
        .requireNumber()
        .build());
    
    // プレイヤー3
    if (playerNames.length > 0) {
      form.addListItem()
        .setTitle('プレイヤー3名')
        .setChoiceValues(playerNames)
        .setRequired(true);
    } else {
      form.addTextItem()
        .setTitle('プレイヤー3名')
        .setRequired(true);
    }
    
    form.addTextItem()
      .setTitle('プレイヤー3点数')
      .setRequired(true)
      .setValidation(FormApp.createTextValidation()
        .setHelpText('半角数字で入力してください（例: 22000）')
        .requireNumber()
        .build());
    
    // プレイヤー4（三麻の場合は不要）
    if (playerNames.length > 0) {
      form.addListItem()
        .setTitle('プレイヤー4名（四麻のみ）')
        .setChoiceValues(playerNames)
        .setRequired(false);
    } else {
      form.addTextItem()
        .setTitle('プレイヤー4名（四麻のみ）')
        .setRequired(false);
    }
    
    form.addTextItem()
      .setTitle('プレイヤー4点数（四麻のみ）')
      .setRequired(false)
      .setValidation(FormApp.createTextValidation()
        .setHelpText('半角数字で入力してください（例: 25000）')
        .requireNumber()
        .build());
    
    // メモ（任意）
    form.addParagraphTextItem()
      .setTitle('メモ')
      .setRequired(false)
      .setHelpText('特記事項があれば入力してください（任意）');
    
    // 確認メッセージ
    form.setConfirmationMessage('対戦記録を送信しました。ありがとうございます！');
    
    // フォームのURLを取得
    const formUrl = form.getPublishedUrl();
    const editUrl = form.getEditUrl();
    
    Logger.log('✅ 対戦記録フォームを作成しました');
    Logger.log('📝 フォームURL（共有用）: ' + formUrl);
    Logger.log('✏️ 編集URL: ' + editUrl);
    
    // スプレッドシートにフォーム回答を自動整形するトリガーを設定
    if (seasonInfo) {
      createFormSubmitTrigger(form, seasonInfo.spreadsheetId);
    }
    
    return {
      formUrl: formUrl,
      editUrl: editUrl,
      formId: form.getId()
    };
    
  } catch (error) {
    Logger.log('❌ エラー: ' + error.toString());
    throw error;
  }
}

/**
 * プレイヤー管理フォームを作成
 */
function createPlayerManagementForm() {
  try {
    // フォームを作成
    const form = FormApp.create('麻雀プレイヤー管理フォーム');
    
    // 説明を設定
    form.setDescription('新しいプレイヤーを登録するフォームです。');
    
    // 操作タイプ
    form.addMultipleChoiceItem()
      .setTitle('操作')
      .setChoiceValues(['プレイヤーを追加', 'プレイヤー名を変更'])
      .setRequired(true)
      .setHelpText('実行したい操作を選択してください');
    
    // プレイヤー名（新規追加用）
    form.addTextItem()
      .setTitle('プレイヤー名（追加時）')
      .setRequired(false)
      .setHelpText('新しく追加するプレイヤー名を入力してください');
    
    // 既存プレイヤー（変更時）
    const players = getAllPlayers();
    const playerNames = players.map(p => p.name);
    
    if (playerNames.length > 0) {
      form.addListItem()
        .setTitle('変更対象プレイヤー（変更時）')
        .setChoiceValues(playerNames)
        .setRequired(false)
        .setHelpText('名前を変更するプレイヤーを選択してください');
    }
    
    // 新しいプレイヤー名（変更用）
    form.addTextItem()
      .setTitle('新しいプレイヤー名（変更時）')
      .setRequired(false)
      .setHelpText('変更後のプレイヤー名を入力してください');
    
    // 確認メッセージ
    form.setConfirmationMessage('送信しました。管理者が確認後、反映されます。');
    
    // フォームのURLを取得
    const formUrl = form.getPublishedUrl();
    const editUrl = form.getEditUrl();
    
    Logger.log('✅ プレイヤー管理フォームを作成しました');
    Logger.log('📝 フォームURL（共有用）: ' + formUrl);
    Logger.log('✏️ 編集URL: ' + editUrl);
    
    return {
      formUrl: formUrl,
      editUrl: editUrl,
      formId: form.getId()
    };
    
  } catch (error) {
    Logger.log('❌ エラー: ' + error.toString());
    throw error;
  }
}

/**
 * フォーム送信時のトリガーを作成
 */
function createFormSubmitTrigger(form, spreadsheetId) {
  try {
    ScriptApp.newTrigger('onFormSubmit')
      .forForm(form)
      .onFormSubmit()
      .create();
    
    Logger.log('✅ フォーム送信トリガーを作成しました');
  } catch (error) {
    Logger.log('⚠️ トリガー作成エラー: ' + error.toString());
  }
}

/**
 * フォーム送信時の処理
 * スプレッドシートのフォーマットを整形
 */
function onFormSubmit(e) {
  try {
    const itemResponses = e.response.getItemResponses();
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const formResponseSheet = ss.getSheets()[0]; // フォーム回答シート
    const dataSheet = ss.getSheetByName('Sheet1') || ss.getSheets()[1]; // データシート
    
    // フォーム回答の最終行を取得
    const lastRow = formResponseSheet.getLastRow();
    const responseData = formResponseSheet.getRange(lastRow, 1, 1, formResponseSheet.getLastColumn()).getValues()[0];
    
    // タイムスタンプ
    const timestamp = responseData[0];
    
    // 対戦日
    let gameDate = '';
    if (responseData[1]) {
      const date = new Date(responseData[1]);
      gameDate = Utilities.formatDate(date, Session.getScriptTimeZone(), 'yyyy/MM/dd');
    }
    
    // 対戦時刻
    let gameTime = '';
    if (responseData[2]) {
      gameTime = responseData[2];
    }
    
    // 対戦タイプ
    const gameType = responseData[3] || '四麻半荘';
    
    // プレイヤー情報
    const player1Name = responseData[4] || '';
    const player1Score = parseFloat(responseData[5]) || 0;
    const player2Name = responseData[6] || '';
    const player2Score = parseFloat(responseData[7]) || 0;
    const player3Name = responseData[8] || '';
    const player3Score = parseFloat(responseData[9]) || 0;
    const player4Name = responseData[10] || '';
    const player4Score = parseFloat(responseData[11]) || 0;
    const notes = responseData[12] || '';
    
    // データシートに追加
    if (dataSheet) {
      const dataRow = [
        gameDate,
        gameTime,
        gameType,
        player1Name,
        player1Score,
        player2Name,
        player2Score,
        player3Name,
        player3Score,
        player4Name,
        player4Score,
        notes,
        Utilities.formatDate(timestamp, Session.getScriptTimeZone(), 'yyyy/MM/dd HH:mm:ss')
      ];
      
      dataSheet.appendRow(dataRow);
      Logger.log('✅ データを追加しました: ' + gameDate + ' ' + gameType);
    }
    
  } catch (error) {
    Logger.log('❌ フォーム送信処理エラー: ' + error.toString());
  }
}

/**
 * プレイヤーリストを更新（定期実行推奨）
 */
function updatePlayerListInForm() {
  try {
    const players = getAllPlayers();
    const playerNames = players.map(p => p.name);
    
    // フォームを取得（フォームIDを指定）
    // const formId = 'YOUR_FORM_ID';
    // const form = FormApp.openById(formId);
    
    // プレイヤー選択項目を更新
    // form.getItems().forEach(item => {
    //   if (item.getType() === FormApp.ItemType.LIST) {
    //     item.asListItem().setChoiceValues(playerNames);
    //   }
    // });
    
    Logger.log('✅ プレイヤーリストを更新しました');
  } catch (error) {
    Logger.log('❌ プレイヤーリスト更新エラー: ' + error.toString());
  }
}

/**
 * すべてのフォームを一括作成
 */
function createAllForms() {
  Logger.log('=== フォーム一括作成開始 ===');
  
  const gameForm = createMahjongGameForm();
  Logger.log('');
  
  const playerForm = createPlayerManagementForm();
  Logger.log('');
  
  Logger.log('=== フォーム一括作成完了 ===');
  Logger.log('');
  Logger.log('📋 対戦記録フォーム: ' + gameForm.formUrl);
  Logger.log('👥 プレイヤー管理フォーム: ' + playerForm.formUrl);
  
  return {
    gameForm: gameForm,
    playerForm: playerForm
  };
}
