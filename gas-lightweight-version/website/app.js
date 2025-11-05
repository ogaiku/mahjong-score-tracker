/**
 * 麻雀スコアボード - メインJavaScriptファイル
 * 軽量・高速・モダンな実装
 */

// ========================================
// グローバル状態管理
// ========================================

const AppState = {
  currentSeason: null,
  seasons: [],
  players: [],
  rankings: [],
  recentGames: [],
  allGames: [],
  selectedPlayer: null,
  charts: {}
};

// ========================================
// 初期化
// ========================================

document.addEventListener('DOMContentLoaded', async () => {
  // 設定チェック
  if (!checkConfig()) {
    showError('設定ファイル（config.js）を編集してGAS Web App URLを設定してください。');
    hideLoading();
    return;
  }
  
  // イベントリスナー設定
  setupEventListeners();
  
  // 初期データ読み込み
  await loadInitialData();
  
  // ローディング非表示
  hideLoading();
  
  // 自動更新設定（オプション）
  if (APP_CONFIG.REFRESH_INTERVAL > 0) {
    setInterval(refreshData, APP_CONFIG.REFRESH_INTERVAL);
  }
});

// ========================================
// イベントリスナー
// ========================================

function setupEventListeners() {
  // タブ切り替え
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      switchTab(e.target.dataset.tab);
    });
  });
  
  // シーズン選択
  const seasonSelect = document.getElementById('season-select');
  seasonSelect.addEventListener('change', async (e) => {
    AppState.currentSeason = e.target.value;
    await loadSeasonData();
  });
  
  // 更新ボタン
  document.getElementById('refresh-btn').addEventListener('click', refreshData);
  
  // プレイヤー選択（統計タブ）
  document.getElementById('player-select').addEventListener('change', async (e) => {
    AppState.selectedPlayer = e.target.value;
    if (AppState.selectedPlayer) {
      await loadPlayerStats(AppState.selectedPlayer);
    }
  });
  
  // 検索入力
  const searchInput = document.getElementById('search-input');
  searchInput.addEventListener('input', (e) => {
    filterGames(e.target.value);
  });
  
  // 対戦タイプフィルター
  const gameTypeFilter = document.getElementById('game-type-filter');
  gameTypeFilter.addEventListener('change', (e) => {
    filterGamesByType(e.target.value);
  });
  
  // 対戦比較
  document.getElementById('compare-btn').addEventListener('click', async () => {
    const player1 = document.getElementById('player1-select').value;
    const player2 = document.getElementById('player2-select').value;
    
    if (player1 && player2) {
      await comparePlayers(player1, player2);
    } else {
      showMessage('2人のプレイヤーを選択してください', 'warning');
    }
  });
  
  // フォームリンク
  document.getElementById('form-link').href = APP_CONFIG.GAME_FORM_URL;
}

// ========================================
// データ読み込み
// ========================================

async function loadInitialData() {
  try {
    showLoading();
    
    // シーズン情報を取得
    await loadSeasons();
    
    // プレイヤーマスターを取得
    await loadPlayers();
    
    // 現在のシーズンのデータを読み込み
    if (AppState.currentSeason) {
      await loadSeasonData();
    }
    
  } catch (error) {
    console.error('初期データ読み込みエラー:', error);
    showError('データの読み込みに失敗しました: ' + error.message);
  }
}

async function loadSeasons() {
  try {
    const response = await fetch(`${APP_CONFIG.GAS_API_URL}?action=api&endpoint=seasons`);
    const data = await response.json();
    
    if (data.error) {
      throw new Error(data.error);
    }
    
    AppState.seasons = data.seasons || [];
    AppState.currentSeason = data.currentSeason;
    
    // シーズン選択ドロップダウンを更新
    updateSeasonSelect();
    
  } catch (error) {
    console.error('シーズン読み込みエラー:', error);
    throw error;
  }
}

async function loadPlayers() {
  try {
    const response = await fetch(`${APP_CONFIG.GAS_API_URL}?action=api&endpoint=all_players`);
    const data = await response.json();
    
    if (data.error) {
      throw new Error(data.error);
    }
    
    AppState.players = Array.isArray(data) ? data : [];
    
    // プレイヤー選択ドロップダウンを更新
    updatePlayerSelects();
    
  } catch (error) {
    console.error('プレイヤー読み込みエラー:', error);
    throw error;
  }
}

async function loadSeasonData() {
  if (!AppState.currentSeason) {
    return;
  }
  
  try {
    showLoading();
    
    // 並列でデータを取得
    const [rankingsData, recentGamesData, allGamesData] = await Promise.all([
      fetchAPI('rankings', { season: AppState.currentSeason }),
      fetchAPI('recent_games', { season: AppState.currentSeason, limit: APP_CONFIG.DEFAULT_RECENT_GAMES_LIMIT }),
      fetchAPI('game_records', { season: AppState.currentSeason })
    ]);
    
    AppState.rankings = rankingsData;
    AppState.recentGames = recentGamesData;
    AppState.allGames = allGamesData;
    
    // UI更新
    updateRankingsUI();
    updateRecentGamesUI();
    updateLastUpdatedTime();
    
    hideLoading();
    
  } catch (error) {
    console.error('シーズンデータ読み込みエラー:', error);
    showError('データの読み込みに失敗しました');
    hideLoading();
  }
}

async function loadPlayerStats(playerName) {
  try {
    showLoading();
    
    const stats = await fetchAPI('player_stats', { 
      season: AppState.currentSeason, 
      player: playerName 
    });
    
    renderPlayerStats(stats);
    
    hideLoading();
    
  } catch (error) {
    console.error('プレイヤー統計読み込みエラー:', error);
    showError('プレイヤー統計の読み込みに失敗しました');
    hideLoading();
  }
}

async function comparePlayers(player1, player2) {
  try {
    showLoading();
    
    const comparison = await fetchAPI('head_to_head', { 
      season: AppState.currentSeason, 
      player1: player1,
      player2: player2
    });
    
    renderComparison(comparison);
    
    hideLoading();
    
  } catch (error) {
    console.error('対戦比較読み込みエラー:', error);
    showError('対戦比較の読み込みに失敗しました');
    hideLoading();
  }
}

// ========================================
// API通信
// ========================================

async function fetchAPI(endpoint, params = {}) {
  const url = new URL(APP_CONFIG.GAS_API_URL);
  url.searchParams.set('action', 'api');
  url.searchParams.set('endpoint', endpoint);
  
  Object.keys(params).forEach(key => {
    url.searchParams.set(key, params[key]);
  });
  
  const response = await fetch(url.toString());
  const data = await response.json();
  
  if (data.error) {
    throw new Error(data.error);
  }
  
  return data;
}

// ========================================
// UI更新
// ========================================

function updateSeasonSelect() {
  const select = document.getElementById('season-select');
  select.innerHTML = '<option value="">シーズン選択...</option>';
  
  AppState.seasons.forEach(season => {
    const option = document.createElement('option');
    option.value = season.key;
    option.textContent = season.name;
    option.selected = season.key === AppState.currentSeason;
    select.appendChild(option);
  });
}

function updatePlayerSelects() {
  const selects = [
    document.getElementById('player-select'),
    document.getElementById('player1-select'),
    document.getElementById('player2-select')
  ];
  
  selects.forEach(select => {
    const placeholder = select.options[0].text;
    select.innerHTML = `<option value="">${placeholder}</option>`;
    
    AppState.players.forEach(player => {
      const option = document.createElement('option');
      option.value = player.name;
      option.textContent = player.name;
      select.appendChild(option);
    });
  });
}

function updateRankingsUI() {
  const tbody = document.getElementById('rankings-tbody');
  tbody.innerHTML = '';
  
  if (!AppState.rankings || AppState.rankings.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="no-data">データがありません</td></tr>';
    return;
  }
  
  // 統計サマリーを更新
  updateStatsSummary();
  
  // ランキングテーブルを構築
  AppState.rankings.forEach((player, index) => {
    const tr = document.createElement('tr');
    
    // 順位
    const rankTd = document.createElement('td');
    const rankBadge = document.createElement('span');
    rankBadge.className = `rank-badge ${getRankBadgeClass(index + 1)}`;
    rankBadge.textContent = index + 1;
    rankTd.appendChild(rankBadge);
    tr.appendChild(rankTd);
    
    // プレイヤー名
    const nameTd = document.createElement('td');
    nameTd.textContent = player.name;
    nameTd.style.fontWeight = '600';
    tr.appendChild(nameTd);
    
    // 対戦数
    const gamesTod = document.createElement('td');
    gamesTod.textContent = player.totalGames;
    tr.appendChild(gamesTod);
    
    // 平均スコア
    const avgScoreTd = document.createElement('td');
    const scoreSpan = document.createElement('span');
    scoreSpan.textContent = formatScore(player.avgScore);
    scoreSpan.className = player.avgScore >= 0 ? 'score-positive' : 'score-negative';
    avgScoreTd.appendChild(scoreSpan);
    tr.appendChild(avgScoreTd);
    
    // 平均順位
    const avgRankTd = document.createElement('td');
    avgRankTd.textContent = player.avgRank.toFixed(2);
    tr.appendChild(avgRankTd);
    
    // 1位率
    const winRateTd = document.createElement('td');
    winRateTd.textContent = player.winRate.toFixed(1) + '%';
    tr.appendChild(winRateTd);
    
    // 順位分布
    const distTd = document.createElement('td');
    const distDiv = document.createElement('div');
    distDiv.className = 'rank-distribution';
    
    [1, 2, 3, 4].forEach(rank => {
      const count = player.rankDistribution[rank] || 0;
      if (count > 0) {
        const span = document.createElement('span');
        span.className = 'rank-count';
        span.textContent = `${rank}位:${count}`;
        distDiv.appendChild(span);
      }
    });
    
    distTd.appendChild(distDiv);
    tr.appendChild(distTd);
    
    // クリックでプレイヤー統計へ
    tr.style.cursor = 'pointer';
    tr.addEventListener('click', () => {
      document.getElementById('player-select').value = player.name;
      AppState.selectedPlayer = player.name;
      switchTab('players');
      loadPlayerStats(player.name);
    });
    
    tbody.appendChild(tr);
  });
  
  // グラフを更新
  updateRankingCharts();
}

function updateStatsSummary() {
  const summary = document.getElementById('stats-summary');
  
  if (!AppState.rankings || AppState.rankings.length === 0) {
    summary.innerHTML = '';
    return;
  }
  
  const totalPlayers = AppState.rankings.length;
  const totalGames = AppState.allGames ? AppState.allGames.length : 0;
  
  summary.innerHTML = `
    <div>プレイヤー数: <span>${totalPlayers}</span></div>
    <div>総対戦数: <span>${totalGames}</span></div>
  `;
}

function updateRecentGamesUI() {
  const container = document.getElementById('recent-games-list');
  container.innerHTML = '';
  
  if (!AppState.recentGames || AppState.recentGames.length === 0) {
    container.innerHTML = '<div class="card"><p class="no-data">対戦記録がありません</p></div>';
    return;
  }
  
  AppState.recentGames.forEach(game => {
    const card = createGameCard(game);
    container.appendChild(card);
  });
}

function createGameCard(game) {
  const card = document.createElement('div');
  card.className = 'game-card';
  
  // ゲームヘッダー
  const header = document.createElement('div');
  header.className = 'game-header';
  
  const dateSpan = document.createElement('span');
  dateSpan.className = 'game-date';
  dateSpan.textContent = `${game.date} ${game.time || ''}`;
  
  const typeBadge = document.createElement('span');
  typeBadge.className = 'game-type-badge';
  typeBadge.textContent = game.gameType;
  
  header.appendChild(dateSpan);
  header.appendChild(typeBadge);
  
  // プレイヤーグリッド
  const playersGrid = document.createElement('div');
  playersGrid.className = 'players-grid';
  
  const players = [];
  for (let i = 1; i <= 4; i++) {
    const name = game[`player${i}Name`];
    const score = game[`player${i}Score`];
    
    if (name && name.trim()) {
      players.push({ name, score, position: i });
    }
  }
  
  // スコア順にソート
  players.sort((a, b) => b.score - a.score);
  
  players.forEach((player, index) => {
    const playerDiv = document.createElement('div');
    playerDiv.className = `player-result rank-${index + 1}`;
    
    const nameSpan = document.createElement('span');
    nameSpan.className = 'player-name';
    nameSpan.textContent = `${index + 1}. ${player.name}`;
    
    const scoreSpan = document.createElement('span');
    scoreSpan.className = 'player-score';
    scoreSpan.textContent = player.score.toLocaleString();
    
    playerDiv.appendChild(nameSpan);
    playerDiv.appendChild(scoreSpan);
    playersGrid.appendChild(playerDiv);
  });
  
  // メモ（あれば）
  if (game.notes && game.notes.trim()) {
    const notesDiv = document.createElement('div');
    notesDiv.style.marginTop = 'var(--spacing-sm)';
    notesDiv.style.fontSize = '0.875rem';
    notesDiv.style.color = 'var(--text-secondary)';
    notesDiv.textContent = `📝 ${game.notes}`;
    card.appendChild(notesDiv);
  }
  
  card.appendChild(header);
  card.appendChild(playersGrid);
  
  return card;
}

function updateLastUpdatedTime() {
  const timeSpan = document.getElementById('last-updated-time');
  const now = new Date();
  timeSpan.textContent = now.toLocaleString('ja-JP');
}

// ========================================
// グラフ描画
// ========================================

function updateRankingCharts() {
  // 平均スコアチャート
  updateAvgScoreChart();
  
  // 順位分布チャート
  updateRankDistributionChart();
}

function updateAvgScoreChart() {
  const canvas = document.getElementById('avg-score-chart');
  const ctx = canvas.getContext('2d');
  
  // 既存のチャートを破棄
  if (AppState.charts.avgScore) {
    AppState.charts.avgScore.destroy();
  }
  
  if (!AppState.rankings || AppState.rankings.length === 0) {
    return;
  }
  
  // 上位10名
  const topPlayers = AppState.rankings.slice(0, 10);
  
  AppState.charts.avgScore = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: topPlayers.map(p => p.name),
      datasets: [{
        label: '平均スコア',
        data: topPlayers.map(p => p.avgScore),
        backgroundColor: '#3b82f6',
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: (context) => `平均スコア: ${formatScore(context.parsed.y)}`
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: '平均スコア (pt)'
          }
        }
      }
    }
  });
}

function updateRankDistributionChart() {
  const canvas = document.getElementById('rank-distribution-chart');
  const ctx = canvas.getContext('2d');
  
  // 既存のチャートを破棄
  if (AppState.charts.rankDist) {
    AppState.charts.rankDist.destroy();
  }
  
  if (!AppState.rankings || AppState.rankings.length === 0) {
    return;
  }
  
  // 上位10名
  const topPlayers = AppState.rankings.slice(0, 10);
  
  const datasets = [
    {
      label: '1位',
      data: topPlayers.map(p => p.rankDistribution[1] || 0),
      backgroundColor: '#fbbf24'
    },
    {
      label: '2位',
      data: topPlayers.map(p => p.rankDistribution[2] || 0),
      backgroundColor: '#c0c0c0'
    },
    {
      label: '3位',
      data: topPlayers.map(p => p.rankDistribution[3] || 0),
      backgroundColor: '#cd7f32'
    },
    {
      label: '4位',
      data: topPlayers.map(p => p.rankDistribution[4] || 0),
      backgroundColor: '#9ca3af'
    }
  ];
  
  AppState.charts.rankDist = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: topPlayers.map(p => p.name),
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          display: true,
          position: 'top'
        }
      },
      scales: {
        x: {
          stacked: true
        },
        y: {
          stacked: true,
          beginAtZero: true,
          title: {
            display: true,
            text: '回数'
          }
        }
      }
    }
  });
}

// ========================================
// プレイヤー統計表示
// ========================================

function renderPlayerStats(stats) {
  const container = document.getElementById('player-stats-content');
  
  if (!stats || stats.totalGames === 0) {
    container.innerHTML = '<div class="card"><p class="no-data">データがありません</p></div>';
    return;
  }
  
  container.innerHTML = '';
  
  // 統計カード
  const statsCard = document.createElement('div');
  statsCard.className = 'card';
  
  const statsGrid = document.createElement('div');
  statsGrid.className = 'player-stats-grid';
  
  const statItems = [
    { label: '対戦数', value: stats.totalGames, class: '' },
    { label: '平均スコア', value: formatScore(stats.avgScore), class: stats.avgScore >= 0 ? 'success' : 'error' },
    { label: '平均順位', value: stats.avgRank.toFixed(2), class: 'primary' },
    { label: '1位率', value: stats.winRate.toFixed(1) + '%', class: 'success' },
    { label: '最高点棒', value: stats.maxScore.toLocaleString(), class: '' },
    { label: '最低点棒', value: stats.minScore.toLocaleString(), class: '' }
  ];
  
  statItems.forEach(item => {
    const statBox = document.createElement('div');
    statBox.className = 'stat-box';
    
    const label = document.createElement('div');
    label.className = 'stat-label';
    label.textContent = item.label;
    
    const value = document.createElement('div');
    value.className = `stat-value ${item.class}`;
    value.textContent = item.value;
    
    statBox.appendChild(label);
    statBox.appendChild(value);
    statsGrid.appendChild(statBox);
  });
  
  statsCard.appendChild(statsGrid);
  container.appendChild(statsCard);
  
  // グラフ
  const chartsGrid = document.createElement('div');
  chartsGrid.className = 'charts-grid';
  
  // スコア推移グラフ
  const trendCard = document.createElement('div');
  trendCard.className = 'card';
  trendCard.innerHTML = '<h3>スコア推移</h3><canvas id="player-trend-chart"></canvas>';
  chartsGrid.appendChild(trendCard);
  
  // 順位分布グラフ
  const rankCard = document.createElement('div');
  rankCard.className = 'card';
  rankCard.innerHTML = '<h3>順位分布</h3><canvas id="player-rank-chart"></canvas>';
  chartsGrid.appendChild(rankCard);
  
  container.appendChild(chartsGrid);
  
  // チャートを描画
  setTimeout(() => {
    drawPlayerTrendChart(stats);
    drawPlayerRankChart(stats);
  }, 100);
}

function drawPlayerTrendChart(stats) {
  const canvas = document.getElementById('player-trend-chart');
  if (!canvas) return;
  
  const ctx = canvas.getContext('2d');
  
  // 累積スコアを計算
  let cumulative = 0;
  const cumulativeScores = stats.records.map(record => {
    cumulative += record.gameScore;
    return cumulative;
  });
  
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: stats.records.map((_, index) => `${index + 1}戦目`),
      datasets: [{
        label: '累積スコア',
        data: cumulativeScores,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          title: {
            display: true,
            text: '累積スコア (pt)'
          }
        }
      }
    }
  });
}

function drawPlayerRankChart(stats) {
  const canvas = document.getElementById('player-rank-chart');
  if (!canvas) return;
  
  const ctx = canvas.getContext('2d');
  
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['1位', '2位', '3位', '4位'],
      datasets: [{
        data: [
          stats.ranks[1] || 0,
          stats.ranks[2] || 0,
          stats.ranks[3] || 0,
          stats.ranks[4] || 0
        ],
        backgroundColor: ['#fbbf24', '#c0c0c0', '#cd7f32', '#9ca3af']
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: 'bottom'
        }
      }
    }
  });
}

// ========================================
// 対戦比較表示
// ========================================

function renderComparison(comparison) {
  const container = document.getElementById('compare-content');
  
  if (!comparison || comparison.totalGames === 0) {
    container.innerHTML = '<div class="card"><p class="no-data">直接対決の記録がありません</p></div>';
    return;
  }
  
  container.innerHTML = '';
  
  // サマリーカード
  const summaryCard = document.createElement('div');
  summaryCard.className = 'card';
  
  const summaryGrid = document.createElement('div');
  summaryGrid.className = 'head-to-head-summary';
  
  // プレイヤー1
  const player1Div = document.createElement('div');
  player1Div.className = 'player-comparison';
  player1Div.innerHTML = `
    <div class="comparison-name">${comparison.player1}</div>
    <div class="comparison-wins">${comparison.player1Wins}勝</div>
    <div class="stat-label">勝率 ${((comparison.player1Wins / comparison.totalGames) * 100).toFixed(1)}%</div>
  `;
  
  // 総対戦数
  const totalDiv = document.createElement('div');
  totalDiv.className = 'player-comparison';
  totalDiv.innerHTML = `
    <div class="comparison-name">総対戦数</div>
    <div class="comparison-wins">${comparison.totalGames}</div>
    <div class="stat-label">引き分け ${comparison.draws}回</div>
  `;
  
  // プレイヤー2
  const player2Div = document.createElement('div');
  player2Div.className = 'player-comparison';
  player2Div.innerHTML = `
    <div class="comparison-name">${comparison.player2}</div>
    <div class="comparison-wins">${comparison.player2Wins}勝</div>
    <div class="stat-label">勝率 ${((comparison.player2Wins / comparison.totalGames) * 100).toFixed(1)}%</div>
  `;
  
  summaryGrid.appendChild(player1Div);
  summaryGrid.appendChild(totalDiv);
  summaryGrid.appendChild(player2Div);
  summaryCard.appendChild(summaryGrid);
  container.appendChild(summaryCard);
  
  // 直接対決の詳細
  const gamesCard = document.createElement('div');
  gamesCard.className = 'card';
  gamesCard.innerHTML = '<h3>直接対決一覧</h3>';
  
  const gamesList = document.createElement('div');
  gamesList.className = 'games-list';
  
  comparison.games.forEach(game => {
    const gameDiv = document.createElement('div');
    gameDiv.className = 'game-card';
    
    const winner = game.winner === 'draw' ? '引き分け' : `${game.winner}の勝利`;
    const winnerClass = game.winner === comparison.player1 ? 'score-positive' : 
                        game.winner === comparison.player2 ? 'score-negative' : '';
    
    gameDiv.innerHTML = `
      <div class="game-header">
        <span class="game-date">${game.date} ${game.time || ''}</span>
        <span class="game-type-badge">${game.gameType}</span>
      </div>
      <div style="display: flex; justify-content: space-around; margin-top: var(--spacing-sm);">
        <div>
          <div class="player-name">${comparison.player1}</div>
          <div class="player-score">${game.player1Score.toLocaleString()}</div>
        </div>
        <div style="align-self: center; font-size: 1.5rem; color: var(--text-secondary);">VS</div>
        <div>
          <div class="player-name">${comparison.player2}</div>
          <div class="player-score">${game.player2Score.toLocaleString()}</div>
        </div>
      </div>
      <div style="text-align: center; margin-top: var(--spacing-sm);">
        <span class="${winnerClass}" style="font-weight: 600;">${winner}</span>
      </div>
    `;
    
    gamesList.appendChild(gameDiv);
  });
  
  gamesCard.appendChild(gamesList);
  container.appendChild(gamesCard);
}

// ========================================
// フィルター機能
// ========================================

function filterGames(searchText) {
  const filtered = AppState.recentGames.filter(game => {
    const text = searchText.toLowerCase();
    
    for (let i = 1; i <= 4; i++) {
      const name = game[`player${i}Name`];
      if (name && name.toLowerCase().includes(text)) {
        return true;
      }
    }
    
    return false;
  });
  
  displayFilteredGames(filtered);
}

function filterGamesByType(gameType) {
  if (!gameType) {
    updateRecentGamesUI();
    return;
  }
  
  const filtered = AppState.recentGames.filter(game => game.gameType === gameType);
  displayFilteredGames(filtered);
}

function displayFilteredGames(games) {
  const container = document.getElementById('recent-games-list');
  container.innerHTML = '';
  
  if (games.length === 0) {
    container.innerHTML = '<div class="card"><p class="no-data">該当する対戦記録がありません</p></div>';
    return;
  }
  
  games.forEach(game => {
    const card = createGameCard(game);
    container.appendChild(card);
  });
}

// ========================================
// タブ切り替え
// ========================================

function switchTab(tabName) {
  // ナビゲーションボタンを更新
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.classList.remove('active');
    if (btn.dataset.tab === tabName) {
      btn.classList.add('active');
    }
  });
  
  // タブコンテンツを更新
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.remove('active');
  });
  
  document.getElementById(`${tabName}-tab`).classList.add('active');
}

// ========================================
// データ更新
// ========================================

async function refreshData() {
  showLoading();
  
  try {
    await loadSeasonData();
    showMessage('データを更新しました', 'success');
  } catch (error) {
    showError('データの更新に失敗しました');
  }
  
  hideLoading();
}

// ========================================
// UI ヘルパー
// ========================================

function showLoading() {
  document.getElementById('loading').classList.remove('hidden');
}

function hideLoading() {
  document.getElementById('loading').classList.add('hidden');
}

function showMessage(message, type = 'info') {
  // 簡易的なトースト通知（実装は省略可能）
  console.log(`[${type.toUpperCase()}] ${message}`);
}

function showError(message) {
  showMessage(message, 'error');
  alert('エラー: ' + message);
}

function formatScore(score) {
  return score >= 0 ? `+${score.toFixed(2)}` : score.toFixed(2);
}

function getRankBadgeClass(rank) {
  if (rank === 1) return 'gold';
  if (rank === 2) return 'silver';
  if (rank === 3) return 'bronze';
  return 'default';
}

// ========================================
// エクスポート（デバッグ用）
// ========================================

if (APP_CONFIG.DEBUG_MODE) {
  window.AppState = AppState;
  window.debugLoadData = loadInitialData;
  window.debugRefresh = refreshData;
}
