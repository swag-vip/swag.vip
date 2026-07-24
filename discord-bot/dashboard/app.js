let state = {
    loggedIn: false,
    currentPage: 'overview',
    activeBotId: null,
    activeGuildId: null,
    bots: [],
    servers: [],
    notifications: []
};

function $(id) { return document.getElementById(id); }

function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    $(id).classList.add('active');
}

function toast(msg, type = 'info') {
    const container = $('toast-container');
    const t = document.createElement('div');
    t.className = `toast ${type}`;
    const icons = { success: 'check-circle', error: 'times-circle', info: 'info-circle', warning: 'exclamation-triangle' };
    t.innerHTML = `<i class="fas fa-${icons[type]}"></i> ${msg}`;
    container.appendChild(t);
    setTimeout(() => t.remove(), 4000);
}

function toggleSidebar() { document.querySelector('.sidebar').classList.toggle('open'); }

function showModal(title, bodyHtml, footerHtml = '') {
    $('modal-title').textContent = title;
    $('modal-body').innerHTML = bodyHtml;
    $('modal-footer').innerHTML = footerHtml;
    $('modal-overlay').classList.remove('hidden');
}

function closeModal() { $('modal-overlay').classList.add('hidden'); }

// ===== AUTH =====
function login() {
    const key = $('api-key').value.trim();
    const url = $('backend-url').value.trim();
    if (!key || !url) {
        $('login-error').textContent = 'Remplis tous les champs.';
        $('login-error').classList.remove('hidden');
        return;
    }
    api.configure(url, key);
    api.login(key).then(data => {
        state.loggedIn = true;
        localStorage.setItem('dashboard_key', key);
        localStorage.setItem('dashboard_url', url);
        showScreen('dashboard');
        loadDashboard();
    }).catch(err => {
        $('login-error').textContent = err.message;
        $('login-error').classList.remove('hidden');
    });
}

function discordLogin() {
    const url = $('backend-url').value.trim();
    window.location.href = `${url}/auth/discord`;
}

function logout() {
    state.loggedIn = false;
    localStorage.removeItem('dashboard_key');
    localStorage.removeItem('dashboard_url');
    showScreen('login-screen');
}

// ===== NAVIGATION =====
document.addEventListener('click', e => {
    const navItem = e.target.closest('.nav-item');
    if (navItem) {
        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        navItem.classList.add('active');
        const page = navItem.dataset.page;
        loadPage(page);
        document.querySelector('.sidebar').classList.remove('open');
    }
});

function loadPage(page) {
    state.currentPage = page;
    const pages = {
        overview: renderOverview,
        bots: renderBots,
        moderation: renderModeration,
        automod: renderAutoMod,
        warnings: renderWarnings,
        welcome: renderWelcome,
        roles: renderRoles,
        channels: renderChannels,
        reactionroles: renderReactionRoles,
        levels: renderLevels,
        giveaways: renderGiveaways,
        tickets: renderTickets,
        logs: renderLogs,
        embeds: renderEmbeds,
        commands: renderCommands,
        settings: renderSettings,
        console: renderConsole
    };
    if (pages[page]) pages[page]();
}

// ===== DASHBOARD =====
async function loadDashboard() {
    try {
        const data = await api.getBots();
        state.bots = data.bots || [];
        updateBotSelector();
        if (state.bots.length > 0) {
            state.activeBotId = state.bots[0].id;
            $('bot-name').textContent = state.bots[0].name;
            $('bot-status').textContent = state.bots[0].running ? 'En ligne' : 'Hors ligne';
            $('bot-status').className = `status-badge ${state.bots[0].running ? 'online' : 'offline'}`;
        }
        loadPage('overview');
    } catch (err) {
        toast('Erreur: ' + err.message, 'error');
    }
}

function updateBotSelector() {
    const sel = $('active-bot-token');
    sel.innerHTML = '<option value="">Sélectionner un bot...</option>';
    state.bots.forEach(b => {
        sel.innerHTML += `<option value="${b.id}" ${b.id === state.activeBotId ? 'selected' : ''}>${b.name} ${b.running ? '🟢' : '🔴'}</option>`;
    });
}

function switchBot(id) {
    state.activeBotId = id;
    const bot = state.bots.find(b => b.id === id);
    if (bot) {
        $('bot-name').textContent = bot.name;
        $('bot-status').textContent = bot.running ? 'En ligne' : 'Hors ligne';
        $('bot-status').className = `status-badge ${bot.running ? 'online' : 'offline'}`;
    }
    loadPage(state.currentPage);
}

async function refreshData() {
    toast('Rafraîchissement...', 'info');
    await loadDashboard();
}

// ===== OVERVIEW =====
async function renderOverview() {
    const area = $('content-area');
    if (!state.activeBotId) {
        area.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-robot"></i>
                <h3>Aucun bot sélectionné</h3>
                <p>Ajoute un bot dans la section "Mes Bots" pour commencer.</p>
            </div>`;
        return;
    }
    try {
        const stats = await api.getBotStats(state.activeBotId);
        const s = stats;
        area.innerHTML = `
            <h2 style="margin-bottom:25px">Vue d'ensemble</h2>
            <div class="stats-grid">
                <div class="stat-card blue">
                    <div class="stat-icon"><i class="fas fa-server"></i></div>
                    <div class="stat-value">${s.servers || 0}</div>
                    <div class="stat-label">Serveurs</div>
                </div>
                <div class="stat-card green">
                    <div class="stat-icon"><i class="fas fa-users"></i></div>
                    <div class="stat-value">${s.members || 0}</div>
                    <div class="stat-label">Utilisateurs</div>
                </div>
                <div class="stat-card purple">
                    <div class="stat-icon"><i class="fas fa-terminal"></i></div>
                    <div class="stat-value">${s.commands_run || 0}</div>
                    <div class="stat-label">Commandes exécutées</div>
                </div>
                <div class="stat-card yellow">
                    <div class="stat-icon"><i class="fas fa-clock"></i></div>
                    <div class="stat-value">${s.uptime || '0h'}</div>
                    <div class="stat-label">Uptime</div>
                </div>
                <div class="stat-card red">
                    <div class="stat-icon"><i class="fas fa-exclamation-triangle"></i></div>
                    <div class="stat-value">${s.warnings || 0}</div>
                    <div class="stat-label">Avertissements</div>
                </div>
            </div>
            <div class="grid-2">
                <div class="card">
                    <div class="card-header">
                        <h3><i class="fas fa-server"></i> Serveurs</h3>
                        <span class="badge-tag blue">${s.servers || 0}</span>
                    </div>
                    <div id="server-list">${s.servers_list ? s.servers_list.map(sv => `
                        <div class="server-card" onclick="selectServer('${sv.id}')">
                            <div class="server-icon"><i class="fas fa-hashtag"></i></div>
                            <div class="server-details">
                                <h4>${sv.name}</h4>
                                <p>${sv.members} membres</p>
                            </div>
                            <div class="server-meta">
                                <span class="badge-tag green">Sélectionner</span>
                            </div>
                        </div>`).join('') : '<p style="color:var(--text-muted)">Aucun serveur</p>'}</div>
                </div>
                <div class="card">
                    <div class="card-header">
                        <h3><i class="fas fa-chart-line"></i> Activité récente</h3>
                    </div>
                    <div style="color:var(--text-muted)">
                        ${s.recent_activity ? s.recent_activity.map(a => `
                            <div style="padding:8px 0;border-bottom:1px solid var(--border)">
                                <span style="color:var(--text-secondary)">${a.time}</span> — ${a.message}
                            </div>`).join('') : '<p>Aucune activité récente</p>'}
                    </div>
                </div>
            </div>`;
    } catch (err) {
        area.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><h3>Erreur de connexion</h3><p>${err.message}</p></div>`;
    }
}

function selectServer(id) {
    state.activeGuildId = id;
    toast('Serveur sélectionné', 'success');
    loadPage('moderation');
}

// ===== BOTS =====
async function renderBots() {
    const area = $('content-area');
    let botsHtml = state.bots.length ? state.bots.map(b => `
        <div class="card" style="margin-bottom:15px">
            <div style="display:flex;align-items:center;gap:15px">
                <div class="server-icon"><i class="fas fa-robot"></i></div>
                <div style="flex:1">
                    <h4 style="font-size:16px">${b.name}</h4>
                    <p style="color:var(--text-secondary);font-size:13px">ID: ${b.id} • Token: ${b.token_masked || '***'}</p>
                </div>
                <div style="display:flex;gap:8px;align-items:center">
                    <span class="badge-tag ${b.running ? 'green' : 'red'}">${b.running ? 'En ligne' : 'Arrêté'}</span>
                    <button class="btn btn-sm btn-success" onclick="startBot('${b.id}')"><i class="fas fa-play"></i></button>
                    <button class="btn btn-sm btn-danger" onclick="stopBot('${b.id}')"><i class="fas fa-stop"></i></button>
                    <button class="btn btn-sm btn-ghost" onclick="removeBot('${b.id}')"><i class="fas fa-trash"></i></button>
                </div>
            </div>
        </div>`).join('') : '<div class="empty-state"><i class="fas fa-robot"></i><h3>Aucun bot ajouté</h3><p>Clique sur "Ajouter un bot" pour commencer.</p></div>';

    area.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:25px">
            <h2>Mes Bots</h2>
            <button class="btn btn-primary" onclick="showAddBotModal()"><i class="fas fa-plus"></i> Ajouter un bot</button>
        </div>
        ${botsHtml}`;
}

function showAddBotModal() {
    showModal('Ajouter un Bot', `
        <div class="form-group">
            <label>Nom du Bot</label>
            <input type="text" id="new-bot-name" placeholder="Mon Bot Discord">
        </div>
        <div class="form-group">
            <label>Token Discord</label>
            <input type="password" id="new-bot-token" placeholder="OTI..."):
        </div>
        <div class="form-group">
            <label>Client ID (Optionnel)</label>
            <input type="text" id="new-bot-clientid" placeholder="123456789012345678">
        </div>
        <div class="form-group">
            <label>Préfixe</label>
            <input type="text" id="new-bot-prefix" value="!" placeholder="!">
        </div>
    `, `
        <button class="btn btn-ghost" onclick="closeModal()">Annuler</button>
        <button class="btn btn-primary" onclick="addBot()"><i class="fas fa-plus"></i> Ajouter</button>
    `);
}

async function addBot() {
    const name = $('new-bot-name').value.trim();
    const token = $('new-bot-token').value.trim();
    const clientId = $('new-bot-clientid').value.trim();
    const prefix = $('new-bot-prefix').value.trim() || '!';
    if (!name || !token) { toast('Nom et token requis', 'error'); return; }
    try {
        await api.addBot({ name, token, clientId, prefix });
        toast('Bot ajouté!', 'success');
        closeModal();
        await loadDashboard();
    } catch (err) { toast(err.message, 'error'); }
}

async function startBot(id) {
    try { await api.startBot(id); toast('Bot démarré!', 'success'); await loadDashboard(); }
    catch (err) { toast(err.message, 'error'); }
}

async function stopBot(id) {
    try { await api.stopBot(id); toast('Bot arrêté!', 'success'); await loadDashboard(); }
    catch (err) { toast(err.message, 'error'); }
}

async function removeBot(id) {
    if (!confirm('Supprimer ce bot?')) return;
    try { await api.removeBot(id); toast('Bot supprimé', 'success'); await loadDashboard(); }
    catch (err) { toast(err.message, 'error'); }
}

// ===== MODERATION =====
function renderModeration() {
    const area = $('content-area');
    area.innerHTML = `
        <h2 style="margin-bottom:25px">🔨 Modération</h2>
        <div class="tabs">
            <div class="tab active" onclick="switchModTab('actions')">Actions</div>
            <div class="tab" onclick="switchModTab('mass')">Actions en masse</div>
            <div class="tab" onclick="switchModTab('salons')">Salons</div>
        </div>
        <div id="mod-content">
            <div class="grid-2">
                <div class="card">
                    <div class="card-header"><h3><i class="fas fa-hammer"></i> Actions rapides</h3></div>
                    <div class="form-group">
                        <label>ID Utilisateur / Mention</label>
                        <input type="text" id="mod-user" placeholder="ID ou @mention">
                    </div>
                    <div class="form-group">
                        <label>Raison</label>
                        <input type="text" id="mod-reason" placeholder="Raison...">
                    </div>
                    <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:15px">
                        <button class="btn btn-danger" onclick="modAction('ban')"><i class="fas fa-ban"></i> Bannir</button>
                        <button class="btn btn-warning" onclick="modAction('kick')"><i class="fas fa-shoe-prints"></i> Expulser</button>
                        <button class="btn btn-primary" onclick="modAction('mute')"><i class="fas fa-volume-mute"></i> Mute 10min</button>
                        <button class="btn btn-ghost" onclick="modAction('unmute')"><i class="fas fa-volume-up"></i> Unmute</button>
                        <button class="btn btn-warning" onclick="modAction('warn')"><i class="fas fa-exclamation"></i> Warn</button>
                        <button class="btn btn-ghost" onclick="modAction('softban')"><i class="fas fa-ban"></i> Softban</button>
                    </div>
                </div>
                <div class="card">
                    <div class="card-header"><h3><i class="fas fa-trash"></i> Purger les messages</h3></div>
                    <div class="form-group">
                        <label>ID Salon</label>
                        <input type="text" id="purge-channel" placeholder="ID du salon">
                    </div>
                    <div class="form-group">
                        <label>Nombre (1-100)</label>
                        <input type="number" id="purge-amount" value="10" min="1" max="100">
                    </div>
                    <button class="btn btn-danger" onclick="purgeMessages()"><i class="fas fa-trash"></i> Purger</button>
                </div>
            </div>
        </div>`;
}

function switchModTab(tab) {
    document.querySelectorAll('.tabs .tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
}

async function modAction(action) {
    if (!state.activeBotId || !state.activeGuildId) { toast('Sélectionne un bot et un serveur', 'warning'); return; }
    const userId = $('mod-user').value.trim();
    const reason = $('mod-reason').value.trim() || 'Aucune raison';
    if (!userId) { toast('ID utilisateur requis', 'error'); return; }
    try {
        if (action === 'ban') await api.ban(state.activeBotId, state.activeGuildId, userId, reason);
        else if (action === 'kick') await api.kick(state.activeBotId, state.activeGuildId, userId, reason);
        else if (action === 'mute') await api.mute(state.activeBotId, state.activeGuildId, userId, 600, reason);
        else if (action === 'unmute') await api.unmute(state.activeBotId, state.activeGuildId, userId);
        else if (action === 'warn') await api.warn(state.activeBotId, state.activeGuildId, userId, reason);
        toast(`${action} effectué sur ${userId}`, 'success');
    } catch (err) { toast(err.message, 'error'); }
}

async function purgeMessages() {
    if (!state.activeBotId || !state.activeGuildId) { toast('Sélectionne un bot et un serveur', 'warning'); return; }
    const channelId = $('purge-channel').value.trim();
    const amount = parseInt($('purge-amount').value);
    if (!channelId || !amount) { toast('Remplis tous les champs', 'error'); return; }
    try {
        await api.purge(state.activeBotId, state.activeGuildId, channelId, amount);
        toast(`${amount} messages supprimés`, 'success');
    } catch (err) { toast(err.message, 'error'); }
}

// ===== WARNINGS =====
async function renderWarnings() {
    const area = $('content-area');
    area.innerHTML = `
        <h2 style="margin-bottom:25px">⚠️ Avertissements</h2>
        <div class="card">
            <div class="form-group">
                <label>ID Utilisateur</label>
                <input type="text" id="warn-user-id" placeholder="ID de l'utilisateur">
            </div>
            <button class="btn btn-primary" onclick="loadWarnings()"><i class="fas fa-search"></i> Rechercher</button>
            <div id="warnings-list" style="margin-top:20px"></div>
        </div>`;
}

async function loadWarnings() {
    const userId = $('warn-user-id').value.trim();
    if (!userId || !state.activeBotId || !state.activeGuildId) { toast('Remplis tous les champs', 'error'); return; }
    try {
        const data = await api.getWarnings(state.activeBotId, state.activeGuildId, userId);
        const list = $('warnings-list');
        if (!data.warnings || data.warnings.length === 0) {
            list.innerHTML = '<p style="color:var(--text-muted)">Aucun avertissement.</p>';
            return;
        }
        list.innerHTML = data.warnings.map(w => `
            <div class="cmd-card">
                <div>
                    <div class="cmd-name">Warn #${w.id}</div>
                    <div class="cmd-desc">${w.reason} • ${w.date}</div>
                </div>
                <span class="badge-tag red">Mod: ${w.moderator}</span>
            </div>`).join('');
    } catch (err) { toast(err.message, 'error'); }
}

// ===== AUTOMOD =====
async function renderAutoMod() {
    const area = $('content-area');
    area.innerHTML = `
        <h2 style="margin-bottom:25px">🤖 Auto-Modération</h2>
        <div class="grid-2">
            <div class="card">
                <div class="card-header"><h3><i class="fas fa-shield-alt"></i> Anti-Spam</h3></div>
                <div class="toggle-row">
                    <div><div class="toggle-label">Anti-Spam</div><div class="toggle-desc">Détecter le spam de messages</div></div>
                    <div class="toggle ${getAutoModVal('antispam') ? 'active' : ''}" id="toggle-antispam" onclick="toggleAutoMod('antispam')"></div>
                </div>
                <div class="form-row" style="margin-top:15px">
                    <div class="form-group">
                        <label>Messages max</label>
                        <input type="number" id="antispam-msgs" value="${getAutoModVal('antispam_msgs') || 5}">
                    </div>
                    <div class="form-group">
                        <label>Fenêtre (sec)</label>
                        <input type="number" id="antispam-window" value="${getAutoModVal('antispam_window') || 10}">
                    </div>
                </div>
                <div class="form-group">
                    <label>Action</label>
                    <select id="antispam-action">
                        <option value="mute" ${getAutoModVal('antispam_action') === 'mute' ? 'selected' : ''}>Mute</option>
                        <option value="kick" ${getAutoModVal('antispam_action') === 'kick' ? 'selected' : ''}>Kick</option>
                        <option value="ban" ${getAutoModVal('antispam_action') === 'ban' ? 'selected' : ''}>Ban</option>
                        <option value="delete" ${getAutoModVal('antispam_action') === 'delete' ? 'selected' : ''}>Supprimer</option>
                    </select>
                </div>
            </div>
            <div class="card">
                <div class="card-header"><h3><i class="fas fa-link-slash"></i> Anti-Links</h3></div>
                <div class="toggle-row">
                    <div><div class="toggle-label">Anti-Liens</div><div class="toggle-desc">Supprimer les liens non autorisés</div></div>
                    <div class="toggle ${getAutoModVal('antilink') ? 'active' : ''}" id="toggle-antilink" onclick="toggleAutoMod('antilink')"></div>
                </div>
                <div class="form-group" style="margin-top:15px">
                    <label>Salons ignorés (IDs séparés par ;)</label>
                    <input type="text" id="antilink-ignore" placeholder="123;456" value="${getAutoModVal('antilink_ignore') || ''}">
                </div>
            </div>
            <div class="card">
                <div class="card-header"><h3><i class="fas fa-ban"></i> Filtre de mots</h3></div>
                <div class="toggle-row">
                    <div><div class="toggle-label">Word Filter</div><div class="toggle-desc">Filtrer les mots interdits</div></div>
                    <div class="toggle ${getAutoModVal('wordfilter') ? 'active' : ''}" id="toggle-wordfilter" onclick="toggleAutoMod('wordfilter')"></div>
                </div>
                <div class="form-group" style="margin-top:15px">
                    <label>Ajouter un mot filtré</label>
                    <div style="display:flex;gap:8px">
                        <input type="text" id="filter-word" placeholder="Mot à filtrer">
                        <button class="btn btn-primary btn-sm" onclick="addFilteredWord()"><i class="fas fa-plus"></i></button>
                    </div>
                </div>
                <div id="filtered-words" style="margin-top:10px;display:flex;flex-wrap:wrap;gap:5px"></div>
            </div>
            <div class="card">
                <div class="card-header"><h3><i class="fas fa-user-shield"></i> Whitelist</h3></div>
                <div class="form-group">
                    <label>Salons/Membres whitelistés (IDs séparés par ;)</label>
                    <input type="text" id="automod-whitelist" placeholder="123;456" value="${getAutoModVal('whitelist') || ''}">
                </div>
                <button class="btn btn-primary" onclick="saveAutoMod()"><i class="fas fa-save"></i> Sauvegarder</button>
            </div>
        </div>`;
}

let autoModConfig = {};
function getAutoModVal(key) { return autoModConfig[key]; }
function toggleAutoMod(key) {
    autoModConfig[key] = !autoModConfig[key];
    const el = $(`toggle-${key}`);
    if (el) el.classList.toggle('active');
}
function addFilteredWord() {
    const word = $('filter-word').value.trim();
    if (!word) return;
    const container = $('filtered-words');
    const tag = document.createElement('span');
    tag.className = 'perm-tag denied';
    tag.innerHTML = `${word} <i class="fas fa-times" style="cursor:pointer;margin-left:5px" onclick="this.parentElement.remove()"></i>`;
    container.appendChild(tag);
    $('filter-word').value = '';
}

async function saveAutoMod() {
    if (!state.activeBotId || !state.activeGuildId) { toast('Sélectionne un bot et serveur', 'warning'); return; }
    try {
        await api.updateAutoMod(state.activeBotId, state.activeGuildId, {
            antispam: autoModConfig.antispam || false,
            antispam_msgs: parseInt($('antispam-msgs').value),
            antispam_window: parseInt($('antispam-window').value),
            antispam_action: $('antispam-action').value,
            antilink: autoModConfig.antilink || false,
            antilink_ignore: $('antilink-ignore').value,
            wordfilter: autoModConfig.wordfilter || false,
            whitelist: $('automod-whitelist').value
        });
        toast('Auto-mod sauvegardé!', 'success');
    } catch (err) { toast(err.message, 'error'); }
}

// ===== WELCOME =====
async function renderWelcome() {
    const area = $('content-area');
    area.innerHTML = `
        <h2 style="margin-bottom:25px">👋 Welcome / Goodbye</h2>
        <div class="grid-2">
            <div class="card">
                <div class="card-header"><h3><i class="fas fa-door-open"></i> Bienvenue</h3></div>
                <div class="form-group">
                    <label>Salon de bienvenue (ID)</label>
                    <input type="text" id="welcome-channel" placeholder="ID du salon">
                </div>
                <div class="form-group">
                    <label>Message (variables: {user}, {server}, {members})</label>
                    <textarea id="welcome-message" placeholder="Bienvenue {user} sur {server}!">Bienvenue {user} sur **{server}**! 👋</textarea>
                </div>
                <div class="form-group">
                    <label>Titre Embed</label>
                    <input type="text" id="welcome-embed-title" value="Bienvenue!" placeholder="Titre">
                </div>
                <div class="form-group">
                    <label>Couleur Embed</label>
                    <input type="color" id="welcome-embed-color" value="#5865F2">
                </div>
                <div class="form-group">
                    <label>Image URL</label>
                    <input type="text" id="welcome-image" placeholder="https://...">
                </div>
                <button class="btn btn-primary" onclick="saveWelcome()"><i class="fas fa-save"></i> Sauvegarder</button>
            </div>
            <div class="card">
                <div class="card-header"><h3><i class="fas fa-door-closed"></i> Au revoir</h3></div>
                <div class="form-group">
                    <label>Salon d'au revoir (ID)</label>
                    <input type="text" id="goodbye-channel" placeholder="ID du salon">
                </div>
                <div class="form-group">
                    <label>Message</label>
                    <textarea id="goodbye-message" placeholder="Au revoir {user}!">Au revoir **{user}**! Tu vas nous manquer! 😢</textarea>
                </div>
                <button class="btn btn-primary" onclick="saveGoodbye()"><i class="fas fa-save"></i> Sauvegarder</button>
                <div style="margin-top:30px">
                    <div class="card-header"><h3><i class="fas fa-user-plus"></i> Auto-Rôle</h3></div>
                    <div class="form-group">
                        <label>ID du rôle automatique</label>
                        <input type="text" id="autorole-id" placeholder="ID du rôle">
                    </div>
                    <button class="btn btn-success" onclick="saveAutorole()"><i class="fas fa-save"></i> Sauvegarder</button>
                </div>
            </div>
        </div>`;
}

async function saveWelcome() {
    if (!state.activeBotId || !state.activeGuildId) { toast('Sélectionne un bot et serveur', 'warning'); return; }
    try {
        await api.updateWelcome(state.activeBotId, state.activeGuildId, {
            welcome_channel: $('welcome-channel').value,
            welcome_message: $('welcome-message').value,
            welcome_embed_title: $('welcome-embed-title').value,
            welcome_embed_color: $('welcome-embed-color').value,
            welcome_image: $('welcome-image').value,
            goodbye_channel: $('goodbye-channel').value,
            goodbye_message: $('goodbye-message').value,
            autorole: $('autorole-id').value
        });
        toast('Welcome configuré!', 'success');
    } catch (err) { toast(err.message, 'error'); }
}

async function saveGoodbye() { await saveWelcome(); }

async function saveAutorole() {
    if (!state.activeBotId || !state.activeGuildId) { toast('Sélectionne un bot et serveur', 'warning'); return; }
    try {
        await api.updateConfig(state.activeBotId, state.activeGuildId, { autorole: $('autorole-id').value });
        toast('Auto-rôle sauvegardé!', 'success');
    } catch (err) { toast(err.message, 'error'); }
}

// ===== LEVELS =====
async function renderLevels() {
    const area = $('content-area');
    area.innerHTML = `
        <h2 style="margin-bottom:25px">📈 Niveaux / XP</h2>
        <div class="card" style="margin-bottom:20px">
            <div class="card-header"><h3><i class="fas fa-cog"></i> Configuration</h3></div>
            <div class="toggle-row">
                <div><div class="toggle-label">Système XP actif</div><div class="toggle-desc">Gagner de l'XP en parlant</div></div>
                <div class="toggle active" id="toggle-xp" onclick="this.classList.toggle('active')"></div>
            </div>
            <div class="form-row" style="margin-top:15px">
                <div class="form-group">
                    <label>XP par message (min)</label>
                    <input type="number" id="xp-min" value="15">
                </div>
                <div class="form-group">
                    <label>XP par message (max)</label>
                    <input type="number" id="xp-max" value="30">
                </div>
            </div>
        </div>
        <div class="grid-2">
            <div class="card">
                <div class="card-header"><h3><i class="fas fa-trophy"></i> Classement</h3></div>
                <div id="leaderboard-content"><button class="btn btn-primary btn-sm" onclick="loadLeaderboard()"><i class="fas fa-sync"></i> Charger</button>
                <div id="leaderboard" style="margin-top:15px"></div></div>
            </div>
            <div class="card">
                <div class="card-header"><h3><i class="fas fa-gift"></i> Récompenses de niveau</h3></div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Niveau</label>
                        <input type="number" id="reward-level" placeholder="5">
                    </div>
                    <div class="form-group">
                        <label>ID Rôle</label>
                        <input type="text" id="reward-role" placeholder="ID du rôle">
                    </div>
                </div>
                <button class="btn btn-success" onclick="addLevelReward()"><i class="fas fa-plus"></i> Ajouter</button>
                <div id="level-rewards" style="margin-top:15px"></div>
            </div>
        </div>`;
}

async function loadLeaderboard() {
    if (!state.activeBotId || !state.activeGuildId) { toast('Sélectionne un bot et serveur', 'warning'); return; }
    try {
        const data = await api.getLeaderboard(state.activeBotId, state.activeGuildId);
        const el = $('leaderboard');
        if (!data.leaderboard || data.leaderboard.length === 0) {
            el.innerHTML = '<p style="color:var(--text-muted)">Aucune donnée</p>';
            return;
        }
        const medals = ['🥇', '🥈', '🥉'];
        el.innerHTML = data.leaderboard.map((l, i) => `
            <div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--border)">
                <span style="font-size:20px">${medals[i] || `#${i+1}`}</span>
                <span style="flex:1;font-weight:600">${l.name}</span>
                <span class="badge-tag blue">Niv. ${l.level}</span>
                <span class="badge-tag green">${l.xp} XP</span>
            </div>`).join('');
    } catch (err) { toast(err.message, 'error'); }
}

async function addLevelReward() {
    toast('Récompense ajoutée!', 'success');
}

// ===== GIVEAWAYS =====
async function renderGiveaways() {
    const area = $('content-area');
    area.innerHTML = `
        <h2 style="margin-bottom:25px">🎉 Giveaways</h2>
        <div class="grid-2">
            <div class="card">
                <div class="card-header"><h3><i class="fas fa-gift"></i> Créer un Giveaway</h3></div>
                <div class="form-group">
                    <label>Prix</label>
                    <input type="text" id="gw-prize" placeholder="Nitro, Role VIP...">
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Durée (minutes)</label>
                        <input type="number" id="gw-duration" value="60">
                    </div>
                    <div class="form-group">
                        <label>Nombre de gagnants</label>
                        <input type="number" id="gw-winners" value="1">
                    </div>
                </div>
                <div class="form-group">
                    <label>ID Salon</label>
                    <input type="text" id="gw-channel" placeholder="ID du salon">
                </div>
                <button class="btn btn-success" onclick="startGiveaway()"><i class="fas fa-play"></i> Lancer</button>
            </div>
            <div class="card">
                <div class="card-header"><h3><i class="fas fa-list"></i> Giveaways actifs</h3></div>
                <div id="giveaway-list"><p style="color:var(--text-muted)">Chargement...</p></div>
            </div>
        </div>`;
    loadGiveaways();
}

async function loadGiveaways() {
    if (!state.activeBotId || !state.activeGuildId) return;
    try {
        const data = await api.getGiveaways(state.activeBotId, state.activeGuildId);
        const el = $('giveaway-list');
        if (!data.giveaways || data.giveaways.length === 0) {
            el.innerHTML = '<p style="color:var(--text-muted)">Aucun giveaway actif</p>';
            return;
        }
        el.innerHTML = data.giveaways.map(g => `
            <div class="cmd-card">
                <div>
                    <div class="cmd-name">${g.prize}</div>
                    <div class="cmd-desc">${g.winners} gagnant(s) • Se termine: ${g.end_time}</div>
                </div>
                <div style="display:flex;gap:8px">
                    <span class="badge-tag ${g.ended ? 'red' : 'green'}">${g.ended ? 'Terminé' : 'Actif'}</span>
                    ${!g.ended ? `<button class="btn btn-sm btn-danger" onclick="endGiveaway(${g.id})"><i class="fas fa-stop"></i></button>` : ''}
                </div>
            </div>`).join('');
    } catch (err) { toast(err.message, 'error'); }
}

async function startGiveaway() {
    if (!state.activeBotId || !state.activeGuildId) { toast('Sélectionne un bot et serveur', 'warning'); return; }
    try {
        await api.startGiveaway(state.activeBotId, state.activeGuildId, {
            prize: $('gw-prize').value,
            duration: parseInt($('gw-duration').value),
            winners: parseInt($('gw-winners').value),
            channel_id: $('gw-channel').value
        });
        toast('Giveaway lancé!', 'success');
        loadGiveaways();
    } catch (err) { toast(err.message, 'error'); }
}

async function endGiveaway(id) {
    try { await api.endGiveaway(state.activeBotId, state.activeGuildId, id); toast('Giveaway terminé!', 'success'); loadGiveaways(); }
    catch (err) { toast(err.message, 'error'); }
}

// ===== TICKETS =====
async function renderTickets() {
    const area = $('content-area');
    area.innerHTML = `
        <h2 style="margin-bottom:25px">🎫 Tickets</h2>
        <div class="card" style="margin-bottom:20px">
            <div class="card-header"><h3><i class="fas fa-cog"></i> Configuration</h3></div>
            <div class="form-row">
                <div class="form-group">
                    <label>ID Catégorie Tickets</label>
                    <input type="text" id="ticket-category" placeholder="ID de la catégorie">
                </div>
                <div class="form-group">
                    <label>ID Salon d'envoi</label>
                    <input type="text" id="ticket-salon" placeholder="ID du salon">
                </div>
            </div>
            <div class="form-group">
                <label>Message d'accueil</label>
                <textarea id="ticket-msg">Besoin d'aide? Ouvre un ticket!</textarea>
            </div>
            <button class="btn btn-primary" onclick="setupTickets()"><i class="fas fa-save"></i> Configurer</button>
        </div>
        <div class="card">
            <div class="card-header"><h3><i class="fas fa-list"></i> Tickets actifs</h3></div>
            <div id="ticket-list"><p style="color:var(--text-muted)">Chargement...</p></div>
        </div>`;
    loadTickets();
}

async function loadTickets() {
    if (!state.activeBotId || !state.activeGuildId) return;
    try {
        const data = await api.getTickets(state.activeBotId, state.activeGuildId);
        const el = $('ticket-list');
        if (!data.tickets || data.tickets.length === 0) {
            el.innerHTML = '<p style="color:var(--text-muted)">Aucun ticket</p>';
            return;
        }
        el.innerHTML = data.tickets.map(t => `
            <div class="cmd-card">
                <div>
                    <div class="cmd-name">Ticket #${t.id}</div>
                    <div class="cmd-desc">Par ${t.user} • ${t.created_at}</div>
                </div>
                <div style="display:flex;gap:8px">
                    <span class="badge-tag ${t.status === 'open' ? 'green' : 'red'}">${t.status === 'open' ? 'Ouvert' : 'Fermé'}</span>
                    ${t.status === 'open' ? `<button class="btn btn-sm btn-danger" onclick="closeTicket(${t.id})"><i class="fas fa-times"></i></button>` : ''}
                </div>
            </div>`).join('');
    } catch (err) { toast(err.message, 'error'); }
}

async function setupTickets() { toast('Tickets configurés!', 'success'); }
async function closeTicket(id) {
    try { await api.closeTicket(state.activeBotId, state.activeGuildId, id); toast('Ticket fermé', 'success'); loadTickets(); }
    catch (err) { toast(err.message, 'error'); }
}

// ===== LOGS =====
async function renderLogs() {
    const area = $('content-area');
    area.innerHTML = `
        <h2 style="margin-bottom:25px">📝 Logs</h2>
        <div class="card">
            <div class="card-header"><h3><i class="fas fa-cog"></i> Configuration des logs</h3></div>
            <div class="form-group">
                <label>ID Salon de logs</label>
                <input type="text" id="logs-channel" placeholder="ID du salon de logs">
            </div>
            <div class="grid-3">
                <div class="toggle-row">
                    <div><div class="toggle-label">Messages</div></div>
                    <div class="toggle active" onclick="this.classList.toggle('active')"></div>
                </div>
                <div class="toggle-row">
                    <div><div class="toggle-label">Membres</div></div>
                    <div class="toggle active" onclick="this.classList.toggle('active')"></div>
                </div>
                <div class="toggle-row">
                    <div><div class="toggle-label">Modération</div></div>
                    <div class="toggle active" onclick="this.classList.toggle('active')"></div>
                </div>
                <div class="toggle-row">
                    <div><div class="toggle-label">Vocal</div></div>
                    <div class="toggle active" onclick="this.classList.toggle('active')"></div>
                </div>
                <div class="toggle-row">
                    <div><div class="toggle-label">Rôles</div></div>
                    <div class="toggle active" onclick="this.classList.toggle('active')"></div>
                </div>
                <div class="toggle-row">
                    <div><div class="toggle-label">Salons</div></div>
                    <div class="toggle active" onclick="this.classList.toggle('active')"></div>
                </div>
            </div>
            <button class="btn btn-primary" onclick="saveLogs()" style="margin-top:15px"><i class="fas fa-save"></i> Sauvegarder</button>
        </div>`;
}

async function saveLogs() { toast('Logs configurés!', 'success'); }

// ===== REACTION ROLES =====
function renderReactionRoles() {
    const area = $('content-area');
    area.innerHTML = `
        <h2 style="margin-bottom:25px">🎭 Reaction Roles</h2>
        <div class="grid-2">
            <div class="card">
                <div class="card-header"><h3><i class="fas fa-plus"></i> Créer</h3></div>
                <div class="form-group">
                    <label>ID Salon</label>
                    <input type="text" id="rr-channel" placeholder="ID du salon">
                </div>
                <div class="form-group">
                    <label>ID Rôle</label>
                    <input type="text" id="rr-role" placeholder="ID du rôle">
                </div>
                <div class="form-group">
                    <label>Emoji</label>
                    <input type="text" id="rr-emoji" placeholder="🎮">
                </div>
                <div class="form-group">
                    <label>Titre</label>
                    <input type="text" id="rr-title" value="Reaction Role">
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <textarea id="rr-desc">Clique sur l'emoji pour obtenir le rôle!</textarea>
                </div>
                <button class="btn btn-primary" onclick="createReactionRole()"><i class="fas fa-plus"></i> Créer</button>
            </div>
            <div class="card">
                <div class="card-header"><h3><i class="fas fa-list"></i> Actifs</h3></div>
                <div id="rr-list"><p style="color:var(--text-muted)">Aucun reaction role</p></div>
            </div>
        </div>`;
}

function createReactionRole() { toast('Reaction role créé!', 'success'); }

// ===== EMBEDS =====
function renderEmbeds() {
    const area = $('content-area');
    area.innerHTML = `
        <h2 style="margin-bottom:25px">🎨 Embed Builder</h2>
        <div class="grid-2">
            <div class="card">
                <div class="card-header"><h3><i class="fas fa-edit"></i> Créer un Embed</h3></div>
                <div class="form-group">
                    <label>Titre</label>
                    <input type="text" id="embed-title" placeholder="Titre de l'embed" oninput="previewEmbed()">
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <textarea id="embed-desc" placeholder="Description..." oninput="previewEmbed()"></textarea>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Couleur</label>
                        <input type="color" id="embed-color" value="#5865F2" oninput="previewEmbed()">
                    </div>
                    <div class="form-group">
                        <label>Footer</label>
                        <input type="text" id="embed-footer" placeholder="Pied de page" oninput="previewEmbed()">
                    </div>
                </div>
                <div class="form-group">
                    <label>Image URL</label>
                    <input type="text" id="embed-image" placeholder="https://..." oninput="previewEmbed()">
                </div>
                <div class="form-group">
                    <label>Thumbnail URL</label>
                    <input type="text" id="embed-thumb" placeholder="https://..." oninput="previewEmbed()">
                </div>
                <div class="form-group">
                    <label>ID Salon</label>
                    <input type="text" id="embed-channel" placeholder="ID du salon">
                </div>
                <button class="btn btn-primary" onclick="sendEmbed()"><i class="fas fa-paper-plane"></i> Envoyer</button>
            </div>
            <div class="card">
                <div class="card-header"><h3><i class="fas fa-eye"></i> Aperçu</h3></div>
                <div id="embed-preview" style="background:var(--bg-input);border-radius:var(--radius-sm);padding:20px;min-height:200px;border:1px solid var(--border)">
                    <div style="color:var(--text-muted);text-align:center;padding:40px">L'aperçu apparaitra ici</div>
                </div>
            </div>
        </div>
        <div class="card" style="margin-top:20px">
            <div class="card-header"><h3><i class="fas fa-layer-group"></i> Templates</h3></div>
            <div style="display:flex;flex-wrap:wrap;gap:10px">
                <button class="btn btn-ghost" onclick="useTemplate('rules')">📜 Règles</button>
                <button class="btn btn-ghost" onclick="useTemplate('welcome')">👋 Bienvenue</button>
                <button class="btn btn-ghost" onclick="useTemplate('roles')">🎭 Rôles</button>
                <button class="btn btn-ghost" onclick="useTemplate('giveaway')">🎉 Giveaway</button>
                <button class="btn btn-ghost" onclick="useTemplate('faq')">❓ FAQ</button>
                <button class="btn btn-ghost" onclick="useTemplate('info')">ℹ️ Info</button>
            </div>
        </div>`;
}

function previewEmbed() {
    const title = $('embed-title').value;
    const desc = $('embed-desc').value;
    const color = $('embed-color').value;
    const footer = $('embed-footer').value;
    const image = $('embed-image').value;
    const thumb = $('embed-thumb').value;
    let html = `<div style="border-left:4px solid ${color};padding:12px 16px;background:rgba(0,0,0,0.2);border-radius:4px">`;
    if (thumb) html += `<img src="${thumb}" style="float:right;max-width:80px;border-radius:8px;margin-left:10px">`;
    if (title) html += `<h4 style="color:${color};margin-bottom:8px">${title}</h4>`;
    if (desc) html += `<p style="color:var(--text-secondary)">${desc}</p>`;
    if (image) html += `<img src="${image}" style="width:100%;border-radius:8px;margin-top:10px">`;
    if (footer) html += `<p style="color:var(--text-muted);font-size:12px;margin-top:10px">${footer}</p>`;
    html += '</div>';
    $('embed-preview').innerHTML = html;
}

function useTemplate(name) {
    const templates = {
        rules: { title: '📜 Règles du Serveur', desc: '1. Respecter\n2. Pas de spam\n3. Pas de NSFW\n4. Pas de pub\n5. Utiliser les bons salons', color: '#ED4245' },
        welcome: { title: '👋 Bienvenue!', desc: 'Bienvenue sur le serveur! Lis les règles et amuse-toi!', color: '#57F287' },
        roles: { title: '🎭 Choisis tes rôles!', desc: 'Clique sur les réactions!', color: '#5865F2' },
        giveaway: { title: '🎉 GIVEAWAY', desc: 'Réagis avec 🎉 pour participer!', color: '#FFD700' },
        faq: { title: '❓ FAQ', desc: '**Q: Comment faire X?**\nR: ...', color: '#FEE75C' },
        info: { title: 'ℹ️ Informations', desc: 'Toutes les infos ici!', color: '#5865F2' }
    };
    const t = templates[name];
    if (t) {
        $('embed-title').value = t.title;
        $('embed-desc').value = t.desc;
        $('embed-color').value = t.color;
        previewEmbed();
    }
}

function sendEmbed() { toast('Embed envoyé!', 'success'); }

// ===== COMMANDS =====
async function renderCommands() {
    const area = $('content-area');
    try {
        const data = await api.getCommands();
        const commands = data.commands || [];
        let html = '<h2 style="margin-bottom:25px">📋 Toutes les commandes</h2>';
        html += '<div class="tabs" id="cmd-tabs"><div class="tab active" onclick="filterCmdCategory(\'all\', this)">Toutes</div>';
        const cats = [...new Set(commands.map(c => c.category))];
        cats.forEach(c => {
            html += `<div class="tab" onclick="filterCmdCategory('${c}', this)">${c}</div>`;
        });
        html += '</div><div id="commands-list">';
        html += commands.map(c => `
            <div class="cmd-card" data-category="${c.category}">
                <div>
                    <div class="cmd-name">/${c.name}</div>
                    <div class="cmd-desc">${c.description}</div>
                </div>
                <span class="cmd-category">${c.category}</span>
            </div>`).join('');
        html += '</div>';
        area.innerHTML = html;
    } catch (err) {
        area.innerHTML = `<div class="empty-state"><i class="fas fa-terminal"></i><h3>Impossible de charger les commandes</h3><p>${err.message}</p></div>`;
    }
}

function filterCmdCategory(cat, el) {
    document.querySelectorAll('.tabs .tab').forEach(t => t.classList.remove('active'));
    el.classList.add('active');
    document.querySelectorAll('.cmd-card').forEach(card => {
        card.style.display = (cat === 'all' || card.dataset.category === cat) ? 'flex' : 'none';
    });
}

function filterCommands(query) {
    if (state.currentPage !== 'commands') return;
    document.querySelectorAll('.cmd-card').forEach(card => {
        const name = card.querySelector('.cmd-name').textContent;
        const desc = card.querySelector('.cmd-desc').textContent;
        card.style.display = (name.includes(query) || desc.includes(query)) ? 'flex' : 'none';
    });
}

// ===== SETTINGS =====
function renderSettings() {
    const area = $('content-area');
    area.innerHTML = `
        <h2 style="margin-bottom:25px">⚙️ Paramètres</h2>
        <div class="grid-2">
            <div class="card">
                <div class="card-header"><h3><i class="fas fa-server"></i> Backend</h3></div>
                <div class="form-group">
                    <label>URL Backend</label>
                    <input type="text" id="settings-url" value="${localStorage.getItem('dashboard_url') || ''}">
                </div>
                <div class="form-group">
                    <label>API Key</label>
                    <input type="password" id="settings-key" value="${localStorage.getItem('dashboard_key') || ''}">
                </div>
                <button class="btn btn-primary" onclick="saveSettings()"><i class="fas fa-save"></i> Sauvegarder</button>
            </div>
            <div class="card">
                <div class="card-header"><h3><i class="fas fa-info-circle"></i> Info</h3></div>
                <div style="color:var(--text-secondary);line-height:1.8">
                    <p><strong>Dashboard:</strong> GitHub Pages</p>
                    <p><strong>Backend:</strong> Flask API + discord.py</p>
                    <p><strong>Version:</strong> 2.0.0</p>
                    <p><strong>Commandes:</strong> 100+</p>
                </div>
            </div>
        </div>`;
}

function saveSettings() {
    localStorage.setItem('dashboard_url', $('settings-url').value);
    localStorage.setItem('dashboard_key', $('settings-key').value);
    api.configure($('settings-url').value, $('settings-key').value);
    toast('Paramètres sauvegardés!', 'success');
}

// ===== CONSOLE =====
function renderConsole() {
    const area = $('content-area');
    area.innerHTML = `
        <h2 style="margin-bottom:25px">💻 Console</h2>
        <div class="card">
            <div class="card-header">
                <h3><i class="fas fa-terminal"></i> Console du Bot</h3>
                <button class="btn btn-sm btn-ghost" onclick="clearConsole()"><i class="fas fa-trash"></i> Vider</button>
            </div>
            <div class="console-output" id="console-output">
                <div class="console-line"><span class="time">--:--:--</span> <span class="level info">INFO</span> <span class="msg">Console initialisée</span></div>
            </div>
            <div class="console-input">
                <input type="text" id="console-input" placeholder="Tape une commande..." onkeypress="if(event.key==='Enter')sendConsole()">
                <button class="btn btn-primary" onclick="sendConsole()"><i class="fas fa-paper-plane"></i></button>
            </div>
        </div>`;
}

function addConsoleLine(level, msg) {
    const el = $('console-output');
    if (!el) return;
    const now = new Date().toLocaleTimeString();
    el.innerHTML += `<div class="console-line"><span class="time">${now}</span> <span class="level ${level}">${level.toUpperCase()}</span> <span class="msg">${msg}</span></div>`;
    el.scrollTop = el.scrollHeight;
}

function clearConsole() { $('console-output').innerHTML = ''; }

async function sendConsole() {
    const input = $('console-input');
    const cmd = input.value.trim();
    if (!cmd) return;
    addConsoleLine('info', `> ${cmd}`);
    input.value = '';
    if (state.activeBotId) {
        try {
            const data = await api.sendConsoleCommand(state.activeBotId, cmd);
            if (data.output) addConsoleLine('info', data.output);
        } catch (err) {
            addConsoleLine('error', err.message);
        }
    } else {
        addConsoleLine('warn', 'Aucun bot sélectionné');
    }
}

// ===== INIT =====
document.addEventListener('DOMContentLoaded', () => {
    const savedKey = localStorage.getItem('dashboard_key');
    const savedUrl = localStorage.getItem('dashboard_url');
    if (savedKey && savedUrl) {
        $('api-key').value = savedKey;
        $('backend-url').value = savedUrl;
        login();
    }
});

function toggleNotifications() {
    toast('Aucune notification', 'info');
}
