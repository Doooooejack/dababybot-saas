"""
DababyBot SaaS - User Portal Frontend
HTML/CSS/JS dashboard for traders to control their bots
"""

TRADER_PORTAL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DababyBot Trader Portal</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --primary: #FF6B35;
            --secondary: #004E89;
            --accent: #00D4FF;
            --success: #1DD1A1;
            --danger: #FF5757;
            --dark: #0F0F1E;
            --light: #F8F9FA;
        }
        
        body {
            font-family: 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, var(--dark) 0%, #1a1a2e 100%);
            color: #fff;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* ===== HEADER ===== */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px;
            margin-bottom: 30px;
            background: linear-gradient(135deg, var(--primary), #FF8A50);
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(255, 107, 53, 0.3);
        }
        
        .logo {
            font-size: 24px;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .user-info {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .plan-badge {
            padding: 8px 15px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }
        
        .logout-btn {
            padding: 8px 16px;
            background: rgba(255, 255, 255, 0.3);
            border: none;
            border-radius: 8px;
            color: white;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .logout-btn:hover {
            background: rgba(255, 255, 255, 0.5);
        }
        
        /* ===== GRID LAYOUT ===== */
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }
        }
        
        .grid-full {
            grid-column: 1 / -1;
        }
        
        /* ===== CARDS ===== */
        .card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .card h2 {
            margin-bottom: 20px;
            font-size: 18px;
            color: var(--accent);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        /* ===== BOT STATUS ===== */
        .bot-status {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding: 15px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: var(--danger);
            animation: pulse 1s infinite;
        }
        
        .status-dot.active {
            background: var(--success);
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .status-text {
            font-weight: bold;
        }
        
        /* ===== BUTTONS ===== */
        button {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
            font-size: 14px;
        }
        
        .btn-primary {
            background: var(--primary);
            color: white;
        }
        
        .btn-primary:hover {
            background: #E85A2C;
            transform: translateY(-2px);
        }
        
        .btn-success {
            background: var(--success);
            color: white;
        }
        
        .btn-success:hover {
            background: #18a872;
        }
        
        .btn-danger {
            background: var(--danger);
            color: white;
        }
        
        .btn-danger:hover {
            background: #E44343;
        }
        
        .btn-secondary {
            background: var(--secondary);
            color: white;
        }
        
        .btn-group {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        /* ===== SYMBOLS SECTION ===== */
        .symbols-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }
        
        .symbol-chip {
            padding: 10px;
            background: rgba(0, 212, 255, 0.1);
            border: 2px solid var(--accent);
            border-radius: 8px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            position: relative;
        }
        
        .symbol-chip:hover {
            background: rgba(0, 212, 255, 0.2);
        }
        
        .symbol-chip.active {
            background: var(--accent);
            color: #000;
        }
        
        .symbol-chip .remove {
            position: absolute;
            top: 2px;
            right: 5px;
            cursor: pointer;
            font-weight: bold;
        }
        
        /* ===== STATS ===== */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-top: 15px;
        }
        
        .stat-box {
            background: rgba(0, 0, 0, 0.2);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        
        .stat-label {
            font-size: 12px;
            color: #aaa;
            margin-bottom: 5px;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: var(--accent);
        }
        
        .stat-value.positive {
            color: var(--success);
        }
        
        .stat-value.negative {
            color: var(--danger);
        }
        
        /* ===== TRADES TABLE ===== */
        .trades-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            font-size: 13px;
        }
        
        .trades-table th {
            background: rgba(0, 212, 255, 0.1);
            padding: 10px;
            text-align: left;
            border-bottom: 2px solid var(--accent);
        }
        
        .trades-table td {
            padding: 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .trades-table tr:hover {
            background: rgba(255, 255, 255, 0.05);
        }
        
        .trade-status {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }
        
        .trade-status.open {
            background: rgba(0, 212, 255, 0.2);
            color: var(--accent);
        }
        
        .trade-status.closed {
            background: rgba(29, 209, 161, 0.2);
            color: var(--success);
        }
        
        /* ===== FORMS ===== */
        .form-group {
            margin-bottom: 15px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            font-size: 14px;
        }
        
        .form-group input,
        .form-group textarea {
            width: 100%;
            padding: 10px;
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            color: white;
            font-family: inherit;
        }
        
        .form-group input::placeholder {
            color: #888;
        }
        
        /* ===== MODAL ===== */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        
        .modal.active {
            display: flex;
        }
        
        .modal-content {
            background: var(--dark);
            border: 2px solid var(--primary);
            border-radius: 15px;
            padding: 30px;
            max-width: 500px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .modal-header h3 {
            color: var(--primary);
        }
        
        .close-btn {
            background: none;
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
        }
        
        /* ===== LOADING ===== */
        .loading {
            display: inline-block;
            width: 12px;
            height: 12px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* ===== ALERTS ===== */
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            display: none;
        }
        
        .alert.show {
            display: block;
        }
        
        .alert.error {
            background: rgba(255, 87, 87, 0.2);
            color: #FF9999;
            border-left: 4px solid var(--danger);
        }
        
        .alert.success {
            background: rgba(29, 209, 161, 0.2);
            color: #5FE3D0;
            border-left: 4px solid var(--success);
        }
    </style>
</head>
<body>
    <header>
        <div class="logo">
            🤖 DababyBot Trader Portal
        </div>
        <div class="user-info">
            <span id="username">User</span>
            <span class="plan-badge" id="plan-badge">FREE</span>
            <button class="logout-btn" onclick="logout()">Logout</button>
        </div>
    </header>
    
    <div class="container">
        <!-- ALERTS -->
        <div class="alert" id="alert-error"></div>
        <div class="alert alert-success" id="alert-success"></div>
        
        <!-- BOT CONTROL SECTION -->
        <div class="grid">
            <div class="card">
                <h2>🎮 Bot Control</h2>
                
                <div class="bot-status">
                    <div class="status-indicator">
                        <div class="status-dot" id="status-dot"></div>
                        <div>
                            <div class="status-text" id="status-text">Stopped</div>
                            <small id="status-time"></small>
                        </div>
                    </div>
                    <div class="btn-group">
                        <button class="btn-success" id="start-btn" onclick="startBot()">▶ Start</button>
                        <button class="btn-danger" id="stop-btn" onclick="stopBot()" style="display: none;">⏹ Stop</button>
                    </div>
                </div>
                
                <div style="margin-top: 15px;">
                    <h3 style="font-size: 14px; margin-bottom: 10px;">Quick Actions</h3>
                    <div class="btn-group">
                        <button class="btn-secondary" onclick="openMT5Setup()">🔌 Setup MT5</button>
                        <button class="btn-secondary" onclick="openSymbolConfig()">⚙️ Configure</button>
                    </div>
                </div>
            </div>
            
            <!-- TRADING SYMBOLS -->
            <div class="card">
                <h2>📊 Trading Symbols</h2>
                <p style="font-size: 12px; color: #aaa; margin-bottom: 10px;" id="symbol-info">
                    Select up to 5 symbols
                </p>
                <div class="symbols-grid" id="symbols-grid">
                    <!-- Populated by JS -->
                </div>
                <button class="btn-primary" style="margin-top: 15px; width: 100%;" onclick="saveSymbols()">
                    Save Symbols
                </button>
            </div>
        </div>
        
        <!-- STATS SECTION -->
        <div class="grid">
            <div class="card">
                <h2>📈 Trade Statistics</h2>
                <div class="stats-grid">
                    <div class="stat-box">
                        <div class="stat-label">Total Trades</div>
                        <div class="stat-value" id="stat-total">0</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Win Rate</div>
                        <div class="stat-value" id="stat-winrate">0%</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Total P&L</div>
                        <div class="stat-value positive" id="stat-pnl">$0</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Avg P&L</div>
                        <div class="stat-value" id="stat-avg">$0</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>💰 Account Info</h2>
                <div class="form-group">
                    <label>Subscription Plan</label>
                    <input type="text" id="plan" readonly style="cursor: not-allowed;">
                </div>
                <div class="form-group">
                    <label>Max Symbols</label>
                    <input type="text" id="max-symbols" readonly style="cursor: not-allowed;">
                </div>
                <div class="form-group">
                    <label>Member Since</label>
                    <input type="text" id="member-since" readonly style="cursor: not-allowed;">
                </div>
            </div>
        </div>
        
        <!-- RECENT TRADES -->
        <div class="card grid-full">
            <h2>📋 Recent Trades (Last 10)</h2>
            <table class="trades-table">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Direction</th>
                        <th>Entry</th>
                        <th>Exit</th>
                        <th>P&L</th>
                        <th>Status</th>
                        <th>Time</th>
                    </tr>
                </thead>
                <tbody id="trades-body">
                    <tr><td colspan="7" style="text-align: center; color: #aaa;">No trades yet</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <!-- MODALS -->
    
    <!-- MT5 Setup Modal -->
    <div class="modal" id="mt5-modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>🔌 Setup MT5 Connection</h3>
                <button class="close-btn" onclick="closeModal('mt5-modal')">&times;</button>
            </div>
            <div class="form-group">
                <label>MT5 Server</label>
                <input type="text" id="mt5-server" placeholder="e.g., MetaQuotes-Demo" value="MetaQuotes-Demo">
            </div>
            <div class="form-group">
                <label>Account Number</label>
                <input type="text" id="mt5-account" placeholder="Your MT5 account number">
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" id="mt5-password" placeholder="Your MT5 password">
            </div>
            <button class="btn-primary" style="width: 100%;" onclick="saveMT5Connection()">
                Connect MT5
            </button>
        </div>
    </div>
    
    <!-- Symbol Config Modal -->
    <div class="modal" id="symbol-modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>⚙️ Configure Trading</h3>
                <button class="close-btn" onclick="closeModal('symbol-modal')">&times;</button>
            </div>
            <div class="form-group">
                <label>Strategy Settings (Coming Soon)</label>
                <textarea id="strategy-config" rows="8" placeholder="Advanced settings will be available soon..."></textarea>
            </div>
            <button class="btn-primary" style="width: 100%;" onclick="closeModal('symbol-modal')">
                Close
            </button>
        </div>
    </div>
    
    <script>
        const API_BASE = '/api';
        let authToken = localStorage.getItem('auth_token');
        let user = null;
        
        // ===== INITIALIZATION =====
        window.addEventListener('load', () => {
            if (!authToken) {
                window.location.href = '/login';
                return;
            }
            loadUserProfile();
            loadTradeStats();
            loadRecentTrades();
            loadBotStatus();
            initSymbols();
            setInterval(loadBotStatus, 5000);  // Refresh bot status every 5 seconds
        });
        
        // ===== API CALLS =====
        async function apiCall(endpoint, method = 'GET', data = null) {
            const options = {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                }
            };
            
            if (data) {
                options.body = JSON.stringify(data);
            }
            
            try {
                const response = await fetch(API_BASE + endpoint, options);
                if (response.status === 401) {
                    logout();
                    return;
                }
                return await response.json();
            } catch (error) {
                showError('API Error: ' + error.message);
                console.error(error);
            }
        }
        
        async function loadUserProfile() {
            const data = await apiCall('/user/profile');
            if (data) {
                user = data;
                document.getElementById('username').textContent = user.username;
                document.getElementById('plan-badge').textContent = user.subscription_plan.toUpperCase();
                document.getElementById('plan').value = user.subscription_plan;
                document.getElementById('member-since').value = new Date(user.created_at).toLocaleDateString();
            }
        }
        
        async function loadBotStatus() {
            const data = await apiCall('/bot/status');
            if (data) {
                const dot = document.getElementById('status-dot');
                const text = document.getElementById('status-text');
                const startBtn = document.getElementById('start-btn');
                const stopBtn = document.getElementById('stop-btn');
                
                if (data.running) {
                    dot.classList.add('active');
                    text.textContent = '🔴 RUNNING';
                    startBtn.style.display = 'none';
                    stopBtn.style.display = 'inline-block';
                } else {
                    dot.classList.remove('active');
                    text.textContent = '⚫ STOPPED';
                    startBtn.style.display = 'inline-block';
                    stopBtn.style.display = 'none';
                }
            }
        }
        
        async function loadTradeStats() {
            const data = await apiCall('/trades/stats');
            if (data) {
                document.getElementById('stat-total').textContent = data.total_trades;
                document.getElementById('stat-winrate').textContent = Math.round(data.win_rate) + '%';
                const pnlEl = document.getElementById('stat-pnl');
                pnlEl.textContent = '$' + data.total_pnl.toFixed(2);
                pnlEl.classList.toggle('positive', data.total_pnl > 0);
                pnlEl.classList.toggle('negative', data.total_pnl < 0);
                
                document.getElementById('stat-avg').textContent = '$' + data.avg_pnl.toFixed(2);
            }
        }
        
        async function loadRecentTrades() {
            const data = await apiCall('/trades');
            if (data && data.length > 0) {
                const tbody = document.getElementById('trades-body');
                tbody.innerHTML = data.slice(0, 10).map(trade => `
                    <tr>
                        <td><strong>${trade.symbol}</strong></td>
                        <td>${trade.direction}</td>
                        <td>${trade.entry_price?.toFixed(2) || '-'}</td>
                        <td>${trade.exit_price?.toFixed(2) || '-'}</td>
                        <td style="color: ${trade.pnl > 0 ? '#5FE3D0' : '#FF9999'}">
                            $${trade.pnl?.toFixed(2) || '0'}
                        </td>
                        <td>
                            <span class="trade-status ${trade.status.toLowerCase()}">
                                ${trade.status}
                            </span>
                        </td>
                        <td>${new Date(trade.entry_time).toLocaleDateString()}</td>
                    </tr>
                `).join('');
            }
        }
        
        function initSymbols() {
            const symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'XAUUSD', 'NZDUSD'];
            const grid = document.getElementById('symbols-grid');
            grid.innerHTML = symbols.map(sym => `
                <div class="symbol-chip" onclick="toggleSymbol(this, '${sym}')" data-symbol="${sym}">
                    ${sym}
                </div>
            `).join('');
            document.getElementById('max-symbols').value = user?.subscription_plan === 'elite' ? '10' : 
                                                          user?.subscription_plan === 'pro' ? '5' : '1';
        }
        
        function toggleSymbol(el, symbol) {
            el.classList.toggle('active');
        }
        
        async function saveSymbols() {
            const selected = Array.from(document.querySelectorAll('.symbol-chip.active')).map(el => el.dataset.symbol);
            const data = await apiCall('/user/symbols', 'POST', { symbols: selected });
            if (data) {
                showSuccess('Symbols updated!');
            }
        }
        
        async function startBot() {
            const data = await apiCall('/bot/start', 'POST');
            if (data) {
                showSuccess('Bot started!');
                loadBotStatus();
            }
        }
        
        async function stopBot() {
            const data = await apiCall('/bot/stop', 'POST');
            if (data) {
                showSuccess('Bot stopped!');
                loadBotStatus();
            }
        }
        
        async function saveMT5Connection() {
            const server = document.getElementById('mt5-server').value;
            const account = document.getElementById('mt5-account').value;
            const password = document.getElementById('mt5-password').value;
            
            if (!account || !password) {
                showError('Fill all MT5 fields');
                return;
            }
            
            const data = await apiCall('/user/mt5-connect', 'POST', {
                server, account, password
            });
            
            if (data) {
                showSuccess('MT5 connected!');
                closeModal('mt5-modal');
            }
        }
        
        // ===== UI HELPERS =====
        function openMT5Setup() {
            document.getElementById('mt5-modal').classList.add('active');
        }
        
        function openSymbolConfig() {
            document.getElementById('symbol-modal').classList.add('active');
        }
        
        function closeModal(id) {
            document.getElementById(id).classList.remove('active');
        }
        
        function showError(msg) {
            const el = document.getElementById('alert-error');
            el.textContent = '❌ ' + msg;
            el.classList.add('show');
            setTimeout(() => el.classList.remove('show'), 5000);
        }
        
        function showSuccess(msg) {
            const el = document.getElementById('alert-success');
            el.textContent = '✅ ' + msg;
            el.classList.add('show');
            setTimeout(() => el.classList.remove('show'), 5000);
        }
        
        function logout() {
            localStorage.removeItem('auth_token');
            window.location.href = '/login';
        }
        
        // Close modal on outside click
        window.onclick = (e) => {
            if (e.target.classList.contains('modal')) {
                e.target.classList.remove('active');
            }
        };
    </script>
</body>
</html>
"""

# Use this in Flask:
# @app.route('/dashboard')
# @jwt_required()
# def dashboard():
#     return render_template_string(TRADER_PORTAL_HTML)
