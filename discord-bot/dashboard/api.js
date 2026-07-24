class API {
    constructor() {
        this.baseUrl = '';
        this.apiKey = '';
        this.headers = {};
    }

    configure(baseUrl, apiKey) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.apiKey = apiKey;
        this.headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`
        };
    }

    async request(method, endpoint, body = null) {
        const config = {
            method,
            headers: this.headers
        };
        if (body) config.body = JSON.stringify(body);

        try {
            const res = await fetch(`${this.baseUrl}${endpoint}`, config);
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
            return data;
        } catch (err) {
            if (err.message.includes('Failed to fetch')) {
                throw new Error('Impossible de joindre le backend. Vérifie l\'URL.');
            }
            throw err;
        }
    }

    get(endpoint) { return this.request('GET', endpoint); }
    post(endpoint, body) { return this.request('POST', endpoint, body); }
    put(endpoint, body) { return this.request('PUT', endpoint, body); }
    delete(endpoint) { return this.request('DELETE', endpoint); }

    // Auth
    login(key) { return this.post('/api/auth/login', { key }); }

    // Bots
    getBots() { return this.get('/api/bots'); }
    addBot(data) { return this.post('/api/bots', data); }
    removeBot(id) { return this.delete(`/api/bots/${id}`); }
    startBot(id) { return this.post(`/api/bots/${id}/start`); }
    stopBot(id) { return this.post(`/api/bots/${id}/stop`); }
    getBotStatus(id) { return this.get(`/api/bots/${id}/status`); }
    getBotStats(id) { return this.get(`/api/bots/${id}/stats`); }

    // Servers
    getServers(botId) { return this.get(`/api/bots/${botId}/servers`); }

    // Moderation
    ban(botId, guildId, userId, reason) { return this.post(`/api/bots/${botId}/servers/${guildId}/ban`, { userId, reason }); }
    kick(botId, guildId, userId, reason) { return this.post(`/api/bots/${botId}/servers/${guildId}/kick`, { userId, reason }); }
    mute(botId, guildId, userId, duration, reason) { return this.post(`/api/bots/${botId}/servers/${guildId}/mute`, { userId, duration, reason }); }
    unmute(botId, guildId, userId) { return this.post(`/api/bots/${botId}/servers/${guildId}/unmute`, { userId }); }
    warn(botId, guildId, userId, reason) { return this.post(`/api/bots/${botId}/servers/${guildId}/warn`, { userId, reason }); }
    purge(botId, guildId, channelId, amount) { return this.post(`/api/bots/${botId}/servers/${guildId}/purge`, { channelId, amount }); }
    getWarnings(botId, guildId, userId) { return this.get(`/api/bots/${botId}/servers/${guildId}/warnings/${userId}`); }
    getBans(botId, guildId) { return this.get(`/api/bots/${botId}/servers/${guildId}/bans`); }
    unban(botId, guildId, userId) { return this.post(`/api/bots/${botId}/servers/${guildId}/unban`, { userId }); }

    // Config
    getConfig(botId, guildId) { return this.get(`/api/bots/${botId}/servers/${guildId}/config`); }
    updateConfig(botId, guildId, data) { return this.put(`/api/bots/${botId}/servers/${guildId}/config`, data); }

    // Welcome
    getWelcomeConfig(botId, guildId) { return this.get(`/api/bots/${botId}/servers/${guildId}/config/welcome`); }
    updateWelcome(botId, guildId, data) { return this.put(`/api/bots/${botId}/servers/${guildId}/config/welcome`, data); }

    // AutoMod
    getAutoModConfig(botId, guildId) { return this.get(`/api/bots/${botId}/servers/${guildId}/config/automod`); }
    updateAutoMod(botId, guildId, data) { return this.put(`/api/bots/${botId}/servers/${guildId}/config/automod`, data); }

    // Levels
    getLeaderboard(botId, guildId) { return this.get(`/api/bots/${botId}/servers/${guildId}/levels/leaderboard`); }
    getLevelConfig(botId, guildId) { return this.get(`/api/bots/${botId}/servers/${guildId}/config/levels`); }
    updateLevels(botId, guildId, data) { return this.put(`/api/bots/${botId}/servers/${guildId}/config/levels`, data); }

    // Logs
    getLogsConfig(botId, guildId) { return this.get(`/api/bots/${botId}/servers/${guildId}/config/logs`); }
    updateLogs(botId, guildId, data) { return this.put(`/api/bots/${botId}/servers/${guildId}/config/logs`, data); }

    // Giveaways
    getGiveaways(botId, guildId) { return this.get(`/api/bots/${botId}/servers/${guildId}/giveaways`); }
    startGiveaway(botId, guildId, data) { return this.post(`/api/bots/${botId}/servers/${guildId}/giveaways`, data); }
    endGiveaway(botId, guildId, id) { return this.post(`/api/bots/${botId}/servers/${guildId}/giveaways/${id}/end`); }

    // Tickets
    getTickets(botId, guildId) { return this.get(`/api/bots/${botId}/servers/${guildId}/tickets`); }
    closeTicket(botId, guildId, id) { return this.post(`/api/bots/${botId}/servers/${guildId}/tickets/${id}/close`); }

    // Commands
    getCommands() { return this.get('/api/commands'); }
    executeCommand(botId, guildId, command, args) { return this.post(`/api/bots/${botId}/servers/${guildId}/execute`, { command, args }); }

    // Console
    getConsoleLogs(botId) { return this.get(`/api/bots/${botId}/console`); }
    sendConsoleCommand(botId, command) { return this.post(`/api/bots/${botId}/console`, { command }); }

    // Roles
    getRoles(botId, guildId) { return this.get(`/api/bots/${botId}/servers/${guildId}/roles`); }
    createRole(botId, guildId, data) { return this.post(`/api/bots/${botId}/servers/${guildId}/roles`, data); }
    deleteRole(botId, guildId, roleId) { return this.delete(`/api/bots/${botId}/servers/${guildId}/roles/${roleId}`); }

    // Channels
    getChannels(botId, guildId) { return this.get(`/api/bots/${botId}/servers/${guildId}/channels`); }
    createChannel(botId, guildId, data) { return this.post(`/api/bots/${botId}/servers/${guildId}/channels`, data); }
    deleteChannel(botId, guildId, channelId) { return this.delete(`/api/bots/${botId}/servers/${guildId}/channels/${channelId}`); }
}

const api = new API();
