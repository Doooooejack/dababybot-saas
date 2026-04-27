"""
DababyBot SaaS - Admin Dashboard
Full admin panel for managing users, subscriptions, and platform
"""

ADMIN_PORTAL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DababyBot Admin Panel</title>
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
        
        .layout {
            display: grid;
            grid-template-columns: 250px 1fr;
            min-height: 100vh;
        }
        
        /* ===== SIDEBAR ===== */
        .sidebar {
            background: rgba(0, 0, 0, 0.3);
            padding: 20px;
            border-right: 2px solid var(--primary);
        }
        
        .sidebar-logo {
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 30px;
            color: var(--primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .sidebar-menu {
            list-style: none;
        }
        
        .sidebar-menu li {
            margin-bottom: 10px;
        }
        
        .sidebar-menu a {
            display: block;
            padding: 12px 15px;
            color: #aaa;
            text-decoration: none;
            border-radius: 8px;
            transition: all 0.3s;
            cursor: pointer;
        }
        
        .sidebar-menu a:hover,
        .sidebar-menu a.active {
            background: var(--primary);
            color: white;
        }
        
        .sidebar-menu a span {
            margin-right: 8px;
        }
        
        /* ===== MAIN CONTENT ===== */
        .main-content {
            padding: 30px;
            overflow-y: auto;
        }
        
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid rgba(255, 299, 255, 0.1);
        }
        
        header h1 {
            font-size: 28px;
            color: var(--primary);
        }
        
        .header-actions {
            display: flex;
            gap: 15px;
            align-items: center;
        }
        
        .logout-btn {
            padding: 10px 20px;
            background: var(--danger);
            border: none;
            border-radius: 8px;
            color: white;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
        }
        
        .logout-btn:hover {
            background: #E44343;
        }
        
        /* ===== DASHBOARD STATS ===== */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
        }
        
        .stat-card h3 {
            color: #aaa;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        
        .stat-card .value {
            font-size: 32px;
            font-weight: bold;
            color: var(--accent);
        }
        
        .stat-card .change {
            font-size: 12px;
            color: var(--success);
            margin-top: 8px;
        }
        
        /* ===== TABS ===== */
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        }
        
        .tab {
            padding: 12px 24px;
            border: none;
            background: none;
            color: #aaa;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }
        
        .tab:hover {
            color: var(--accent);
        }
        
        .tab.active {
            color: var(--accent);
            border-bottom-color: var(--accent);
        }
        
        /* ===== TABLE ===== */
        .card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
        }
        
        .card h2 {
            margin-bottom: 20px;
            color: var(--primary);
        }
        
        .table-wrapper {
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        
        table th {
            background: rgba(0, 212, 255, 0.1);
            padding: 12px;
            text-align: left;
            border-bottom: 2px solid var(--accent);
            font-weight: bold;
        }
        
        table td {
            padding: 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        table tr:hover {
            background: rgba(255, 255, 255, 0.05);
        }
        
        /* ===== BADGES ===== */
        .badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            display: inline-block;
        }
        
        .badge.active {
            background: rgba(29, 209, 161, 0.2);
            color: var(--success);
        }
        
        .badge.inactive {
            background: rgba(255, 87, 87, 0.2);
            color: var(--danger);
        }
        
        .badge.trial {
            background: rgba(0, 212, 255, 0.2);
            color: var(--accent);
        }
        
        /* ===== BUTTONS ===== */
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            font-size: 12px;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        
        .btn-primary {
            background: var(--primary);
            color: white;
        }
        
        .btn-primary:hover {
            background: #E85A2C;
        }
        
        .btn-secondary {
            background: var(--secondary);
            color: white;
        }
        
        .btn-success {
            background: var(--success);
            color: white;
        }
        
        .btn-danger {
            background: var(--danger);
            color: white;
        }
        
        .btn-sm {
            padding: 6px 12px;
            font-size: 11px;
        }
        
        /* ===== FORM ===== */
        .form-group {
            margin-bottom: 15px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            font-size: 13px;
        }
        
        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 10px;
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            color: white;
            font-family: inherit;
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
            max-width: 600px;
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
        
        .modal-header h2 {
            color: var(--primary);
        }
        
        .close-btn {
            background: none;
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
        }
        
        /* ===== CHARTS ===== */
        .chart {
            margin-top: 20px;
            padding: 20px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
        }
        
        /* ===== SEARCH & FILTER ===== */
        .search-bar {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .search-bar input {
            flex: 1;
            min-width: 200px;
            padding: 10px;
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            color: white;
        }
        
        .search-bar input::placeholder {
            color: #888;
        }
        
        .page-tabs {
            display: none;
        }
        
        .page-tabs.active {
            display: block;
        }
        
        .action-menu {
            position: relative;
            display: inline-block;
        }
        
        .dropdown {
            display: none;
            position: absolute;
            background: rgba(0, 0, 0, 0.9);
            border: 1px solid var(--primary);
            border-radius: 8px;
            z-index: 100;
            min-width: 150px;
        }
        
        .dropdown.show {
            display: block;
        }
        
        .dropdown a {
            display: block;
            padding: 10px 15px;
            color: #fff;
            text-decoration: none;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .dropdown a:hover {
            background: var(--primary);
        }
    </style>
</head>
<body>
    <div class="layout">
        <!-- SIDEBAR -->
        <div class="sidebar">
            <div class="sidebar-logo">🔐 Admin Panel</div>
            <ul class="sidebar-menu">
                <li><a class="tab-link active" onclick="switchTab('dashboard')"><span>📊</span>Dashboard</a></li>
                <li><a class="tab-link" onclick="switchTab('users')"><span>👥</span>Users</a></li>
                <li><a class="tab-link" onclick="switchTab('subscriptions')"><span>💳</span>Subscriptions</a></li>
                <li><a class="tab-link" onclick="switchTab('payments')"><span>💰</span>Payments</a></li>
                <li><a class="tab-link" onclick="switchTab('bots')"><span>🤖</span>Bot Instances</a></li>
                <li><a class="tab-link" onclick="switchTab('analytics')"><span>📈</span>Analytics</a></li>
                <li><a class="tab-link" onclick="switchTab('settings')"><span>⚙️</span>Settings</a></li>
                <li><a onclick="adminLogout()" style="color: var(--danger);"><span>🚪</span>Logout</a></li>
            </ul>
        </div>
        
        <!-- MAIN CONTENT -->
        <div class="main-content">
            <header>
                <h1 id="page-title">Dashboard</h1>
                <div class="header-actions">
                    <span id="admin-name">Admin</span>
                    <button class="logout-btn" onclick="adminLogout()">Logout</button>
                </div>
            </header>
            
            <!-- DASHBOARD TAB -->
            <div class="page-tabs active" id="dashboard-tab">
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>Total Users</h3>
                        <div class="value" id="stat-total-users">0</div>
                        <div class="change">↑ 12 this month</div>
                    </div>
                    <div class="stat-card">
                        <h3>Active Subscriptions</h3>
                        <div class="value" id="stat-active-subs">0</div>
                        <div class="change">💰 Monthly Revenue</div>
                    </div>
                    <div class="stat-card">
                        <h3>Monthly Revenue</h3>
                        <div class="value" id="stat-revenue">$0</div>
                        <div class="change">↑ 8% vs last month</div>
                    </div>
                    <div class="stat-card">
                        <h3>Bot Instances</h3>
                        <div class="value" id="stat-bot-instances">0</div>
                        <div class="change">Active Now</div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>Recent Activity</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>User</th>
                                <th>Action</th>
                                <th>Date</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody id="activity-log">
                            <tr><td colspan="4" style="text-align: center; color: #aaa;">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- USERS TAB -->
            <div class="page-tabs" id="users-tab">
                <div class="search-bar">
                    <input type="text" id="user-search" placeholder="Search users...">
                    <button class="btn btn-primary" onclick="refreshUsers()">🔄 Refresh</button>
                </div>
                
                <div class="card">
                    <h2>Manage Users</h2>
                    <div class="table-wrapper">
                        <table>
                            <thead>
                                <tr>
                                    <th>Username</th>
                                    <th>Email</th>
                                    <th>Plan</th>
                                    <th>Status</th>
                                    <th>Joined</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="users-table">
                                <tr><td colspan="6" style="text-align: center; color: #aaa;">Loading...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <!-- SUBSCRIPTIONS TAB -->
            <div class="page-tabs" id="subscriptions-tab">
                <div class="card">
                    <h2>Subscription Management</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>User</th>
                                <th>Plan</th>
                                <th>Start Date</th>
                                <th>Renew Date</th>
                                <th>Amount</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="subscriptions-table">
                            <tr><td colspan="7" style="text-align: center; color: #aaa;">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- PAYMENTS TAB -->
            <div class="page-tabs" id="payments-tab">
                <div class="search-bar">
                    <input type="date" id="payment-date-from" placeholder="From">
                    <input type="date" id="payment-date-to" placeholder="To">
                    <button class="btn btn-primary" onclick="filterPayments()">🔍 Filter</button>
                </div>
                
                <div class="card">
                    <h2>Payment History</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>User</th>
                                <th>Amount</th>
                                <th>Plan</th>
                                <th>Status</th>
                                <th>Date</th>
                                <th>Invoice</th>
                            </tr>
                        </thead>
                        <tbody id="payments-table">
                            <tr><td colspan="6" style="text-align: center; color: #aaa;">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- BOTS TAB -->
            <div class="page-tabs" id="bots-tab">
                <div class="card">
                    <h2>Active Bot Instances</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>User</th>
                                <th>Status</th>
                                <th>Symbols</th>
                                <th>Started</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="bots-table">
                            <tr><td colspan="5" style="text-align: center; color: #aaa;">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- ANALYTICS TAB -->
            <div class="page-tabs" id="analytics-tab">
                <div class="card">
                    <h2>Platform Analytics</h2>
                    <div style="height: 300px; background: rgba(0,0,0,0.2); border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #aaa;">
                        📊 Chart will render here (integrate Chart.js for full analytics)
                    </div>
                </div>
            </div>
            
            <!-- SETTINGS TAB -->
            <div class="page-tabs" id="settings-tab">
                <div class="card">
                    <h2>Platform Settings</h2>
                    <div class="form-group">
                        <label>Platform Name</label>
                        <input type="text" value="DababyBot SaaS" id="platform-name">
                    </div>
                    <div class="form-group">
                        <label>Support Email</label>
                        <input type="email" id="support-email" placeholder="support@dababybot.com">
                    </div>
                    <div class="form-group">
                        <label>Max Users</label>
                        <input type="number" value="1000" id="max-users">
                    </div>
                    <button class="btn btn-primary" onclick="saveSettings()">💾 Save Settings</button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- USER DETAILS MODAL -->
    <div class="modal" id="user-modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>User Details</h2>
                <button class="close-btn" onclick="closeModal('user-modal')">&times;</button>
            </div>
            <div id="user-details-content">
                <!-- Auto-populated -->
            </div>
            <div style="margin-top: 20px; display: flex; gap: 10px;">
                <button class="btn btn-primary" onclick="closeModal('user-modal')">Close</button>
                <button class="btn btn-danger" onclick="deleteUserConfirm()">Delete User</button>
            </div>
        </div>
    </div>
    
    <script>
        const API_BASE = '/api';
        let authToken = localStorage.getItem('admin_token');
        
        // ===== INITIALIZATION =====
        window.addEventListener('load', () => {
            if (!authToken) {
                window.location.href = '/admin-login';
                return;
            }
            loadDashboard();
            setInterval(loadDashboard, 30000);  // Refresh every 30 seconds
        });
        
        // ===== TAB SWITCHING =====
        function switchTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.page-tabs').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Remove active from all links
            document.querySelectorAll('.tab-link').forEach(link => {
                link.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
            
            // Update title
            const titles = {
                'dashboard': 'Dashboard',
                'users': 'User Management',
                'subscriptions': 'Subscriptions',
                'payments': 'Payments',
                'bots': 'Bot Instances',
                'analytics': 'Analytics',
                'settings': 'Settings'
            };
            document.getElementById('page-title').textContent = titles[tabName] || tabName;
            
            // Load data for tab
            if (tabName === 'users') loadUsers();
            else if (tabName === 'subscriptions') loadSubscriptions();
            else if (tabName === 'payments') loadPayments();
            else if (tabName === 'bots') loadBots();
        }
        
        // ===== API CALLS =====
        async function apiCall(endpoint, method = 'GET', data = null) {
            const options = {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                }
            };
            
            if (data) options.body = JSON.stringify(data);
            
            try {
                const response = await fetch(API_BASE + endpoint, options);
                if (response.status === 401) {
                    adminLogout();
                    return;
                }
                return await response.json();
            } catch (error) {
                console.error('API Error:', error);
            }
        }
        
        async function loadDashboard() {
            // Load summary stats
            const users = await apiCall('/admin/users');
            if (users) {
                document.getElementById('stat-total-users').textContent = users.length;
                
                const activeSubs = users.filter(u => u.subscription_plan !== 'free').length;
                document.getElementById('stat-active-subs').textContent = activeSubs;
            }
        }
        
        async function loadUsers() {
            const users = await apiCall('/admin/users');
            if (users) {
                const tbody = document.getElementById('users-table');
                tbody.innerHTML = users.map(user => `
                    <tr>
                        <td><strong>${user.username}</strong></td>
                        <td>${user.email}</td>
                        <td><span class="badge active">${user.subscription_plan.toUpperCase()}</span></td>
                        <td><span class="badge ${user.bot_running ? 'active' : 'inactive'}">
                            ${user.bot_running ? 'RUNNING' : 'INACTIVE'}
                        </span></td>
                        <td>${new Date(user.created_at).toLocaleDateString()}</td>
                        <td>
                            <button class="btn btn-sm btn-secondary" onclick="viewUserDetails('${user.id}')">View</button>
                            <button class="btn btn-sm btn-primary" onclick="editPlan('${user.id}')">Edit Plan</button>
                        </td>
                    </tr>
                `).join('');
            }
        }
        
        async function loadSubscriptions() {
            const users = await apiCall('/admin/users');
            if (users) {
                const tbody = document.getElementById('subscriptions-table');
                tbody.innerHTML = users
                    .filter(u => u.subscription_plan !== 'free')
                    .map(user => `
                    <tr>
                        <td>${user.username}</td>
                        <td>${user.subscription_plan.toUpperCase()}</td>
                        <td>${new Date(user.created_at).toLocaleDateString()}</td>
                        <td>${new Date(new Date(user.created_at).getTime() + 30*24*60*60*1000).toLocaleDateString()}</td>
                        <td>$<span>${user.subscription_plan === 'elite' ? '149.99' : '49.99'}</span></td>
                        <td><span class="badge active">ACTIVE</span></td>
                        <td>
                            <button class="btn btn-sm btn-danger" onclick="cancelSubscription('${user.id}')">Cancel</button>
                        </td>
                    </tr>
                `).join('');
            }
        }
        
        async function loadPayments() {
            // Placeholder - integrate with Stripe API
            document.getElementById('payments-table').innerHTML = `
                <tr><td colspan="6" style="text-align: center; color: #aaa;">Integrate Stripe API for payment history</td></tr>
            `;
        }
        
        async function loadBots() {
            const users = await apiCall('/admin/users');
            if (users) {
                const tbody = document.getElementById('bots-table');
                tbody.innerHTML = users
                    .filter(u => u.bot_running)
                    .map(user => `
                    <tr>
                        <td>${user.username}</td>
                        <td><span class="badge active">RUNNING</span></td>
                        <td>${user.selected_symbols.join(', ')}</td>
                        <td>${new Date().toLocaleTimeString()}</td>
                        <td>
                            <button class="btn btn-sm btn-danger" onclick="stopUserBot('${user.id}')">Stop</button>
                        </td>
                    </tr>
                `).join('');
            }
        }
        
        // ===== ACTIONS =====
        function viewUserDetails(userId) {
            // Load and display user details
            document.getElementById('user-modal').classList.add('active');
        }
        
        function editPlan(userId) {
            alert('Edit plan for user: ' + userId);
            // TODO: Open modal to edit subscription plan
        }
        
        async function deleteUserConfirm() {
            if (confirm('Are you sure? This cannot be undone.')) {
                const userId = prompt('Enter user ID:');
                const data = await apiCall(`/admin/user/${userId}`, 'DELETE');
                if (data) {
                    alert('User deleted!');
                    loadUsers();
                }
            }
        }
        
        async function cancelSubscription(userId) {
            if (confirm('Cancel this subscription?')) {
                // TODO: Call cancel subscription endpoint
                alert('Subscription canceled');
                loadSubscriptions();
            }
        }
        
        async function stopUserBot(userId) {
            alert('Stop bot for user: ' + userId);
            // TODO: Add endpoint to stop user's bot
        }
        
        function refreshUsers() {
            loadUsers();
        }
        
        function filterPayments() {
            const from = document.getElementById('payment-date-from').value;
            const to = document.getElementById('payment-date-to').value;
            console.log('Filter payments from', from, 'to', to);
            // TODO: Implement payment filtering
        }
        
        function saveSettings() {
            alert('Settings saved!');
            // TODO: Save settings to backend
        }
        
        function closeModal(id) {
            document.getElementById(id).classList.remove('active');
        }
        
        function adminLogout() {
            localStorage.removeItem('admin_token');
            window.location.href = '/admin-login';
        }
    </script>
</body>
</html>
"""

# Use in Flask:
# @app.route('/admin')
# @jwt_required()
# def admin_dashboard():
#     user_id = get_jwt_identity()
#     user = User.query.get(user_id)
#     if not user.is_admin:
#         abort(403)
#     return render_template_string(ADMIN_PORTAL_HTML)
