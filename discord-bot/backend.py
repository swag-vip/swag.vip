import os
import json
import secrets
import threading
import discord
from discord.ext import commands
from datetime import datetime
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_KEY = os.environ.get('API_KEY', secrets.token_hex(32))
DISCORD_CLIENT_ID = os.environ.get('DISCORD_CLIENT_ID', '')
DISCORD_CLIENT_SECRET = os.environ.get('DISCORD_CLIENT_SECRET', '')
DISCORD_REDIRECT_URI = os.environ.get('DISCORD_REDIRECT_URI', '')

# In-memory storage (cloud-compatible, no file system needed)
running_bots = {}
bot_configs = {}
bot_stats = {}
bot_logs = {}

# Load configs from environment on startup
# Format: BOT_CONFIGS='{"bot1": {"name": "MyBot", "token": "xxx", "prefix": "!"}}'
env_configs = os.environ.get('BOT_CONFIGS', '{}')
try:
    bot_configs = json.loads(env_configs)
except:
    bot_configs = {}

def save_configs_to_env():
    """On Render, env vars are read-only. We keep configs in memory."""
    pass

def require_auth(f):
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '').replace('Bearer ', '')
        if auth != API_KEY:
            return jsonify({'error': 'Non autorisé'}), 401
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# ===== AUTH =====
@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    key = request.json.get('key')
    if key == API_KEY:
        return jsonify({'success': True, 'message': 'Authentifié', 'api_key': API_KEY})
    return jsonify({'error': 'Clé API invalide'}), 401

@app.route('/auth/discord')
def discord_auth():
    if not DISCORD_CLIENT_ID:
        return jsonify({'error': 'Discord OAuth non configuré - ajoute DISCORD_CLIENT_ID'}), 400
    return redirect(
        f'https://discord.com/api/oauth2/authorize'
        f'?client_id={DISCORD_CLIENT_ID}'
        f'&redirect_uri={DISCORD_REDIRECT_URI}'
        f'&response_type=code'
        f'&scope=identify%20guilds'
    )

@app.route('/auth/discord/callback')
def discord_callback():
    return jsonify({'message': 'Callback Discord reçu'})

# ===== BOT MANAGEMENT =====
@app.route('/api/bots', methods=['GET'])
@require_auth
def get_bots():
    bots = []
    for bot_id, cfg in bot_configs.items():
        bots.append({
            'id': bot_id,
            'name': cfg.get('name', 'Bot'),
            'token_masked': cfg.get('token', '')[:8] + '***' if cfg.get('token') else '***',
            'running': bot_id in running_bots and running_bots[bot_id].is_running(),
            'prefix': cfg.get('prefix', '!')
        })
    return jsonify({'bots': bots})

@app.route('/api/bots', methods=['POST'])
@require_auth
def add_bot():
    data = request.json
    bot_id = secrets.token_hex(8)
    bot_configs[bot_id] = {
        'name': data.get('name', 'Bot'),
        'token': data.get('token', ''),
        'client_id': data.get('clientId', ''),
        'prefix': data.get('prefix', '!'),
        'created_at': datetime.utcnow().isoformat()
    }
    return jsonify({'success': True, 'bot_id': bot_id})

@app.route('/api/bots/<bot_id>', methods=['DELETE'])
@require_auth
def remove_bot(bot_id):
    if bot_id in running_bots:
        try:
            running_bots[bot_id].loop.call_soon_threadsafe(running_bots[bot_id].close)
        except:
            pass
        del running_bots[bot_id]
    if bot_id in bot_configs:
        del bot_configs[bot_id]
    return jsonify({'success': True})

@app.route('/api/bots/<bot_id>/start', methods=['POST'])
@require_auth
def start_bot(bot_id):
    if bot_id not in bot_configs:
        return jsonify({'error': 'Bot introuvable'}), 404
    if bot_id in running_bots and running_bots[bot_id].is_running():
        return jsonify({'error': 'Bot déjà en cours'}), 400

    cfg = bot_configs[bot_id]
    token = cfg.get('token', '')
    if not token:
        return jsonify({'error': 'Token manquant'}), 400

    intents = discord.Intents.all()
    prefix = cfg.get('prefix', '!')
    bot = commands.Bot(command_prefix=prefix, intents=intents)

    @bot.event
    async def on_ready():
        bot_stats[bot_id] = {
            'servers': len(bot.guilds),
            'members': sum(g.member_count for g in bot.guilds),
            'commands_run': 0,
            'uptime': '0h',
            'warnings': 0,
            'servers_list': [
                {'id': str(g.id), 'name': g.name, 'members': g.member_count}
                for g in bot.guilds
            ],
            'recent_activity': []
        }
        log_event(bot_id, 'info', f'Connecté en tant que {bot.user} ({len(bot.guilds)} serveurs)')

    @bot.event
    async def on_message(message):
        if message.author.bot:
            return
        await bot.process_commands(message)

    @bot.event
    async def on_member_join(member):
        log_event(bot_id, 'info', f'Membre rejoint: {member} sur {member.guild.name}')

    @bot.event
    async def on_member_remove(member):
        log_event(bot_id, 'info', f'Membre quitté: {member} sur {member.guild.name}')

    @bot.event
    async def on_message_delete(message):
        if message.guild:
            log_event(bot_id, 'warn', f'Message supprimé dans #{message.channel}')

    def run_bot():
        try:
            bot_stats[bot_id] = {
                'servers': 0, 'members': 0, 'commands_run': 0,
                'uptime': '0h', 'warnings': 0,
                'servers_list': [], 'recent_activity': []
            }
            bot.run(token)
        except Exception as e:
            log_event(bot_id, 'error', f'Erreur de connexion: {e}')
            if bot_id in running_bots:
                del running_bots[bot_id]

    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
    running_bots[bot_id] = bot

    log_event(bot_id, 'info', f'Bot "{cfg.get("name")}" démarré')
    return jsonify({'success': True, 'message': 'Bot démarré'})

@app.route('/api/bots/<bot_id>/stop', methods=['POST'])
@require_auth
def stop_bot(bot_id):
    if bot_id in running_bots:
        try:
            bot = running_bots[bot_id]
            bot.loop.call_soon_threadsafe(bot.close)
        except:
            pass
        del running_bots[bot_id]
        log_event(bot_id, 'info', 'Bot arrêté')
        return jsonify({'success': True})
    return jsonify({'error': 'Bot non trouvé'}), 404

@app.route('/api/bots/<bot_id>/status', methods=['GET'])
@require_auth
def get_bot_status(bot_id):
    running = bot_id in running_bots and running_bots[bot_id].is_running()
    return jsonify({'running': running})

@app.route('/api/bots/<bot_id>/stats', methods=['GET'])
@require_auth
def get_bot_stats(bot_id):
    if bot_id in running_bots and bot_id in bot_stats:
        stats = bot_stats[bot_id]
        # Update live stats
        try:
            bot = running_bots[bot_id]
            stats['servers'] = len(bot.guilds)
            stats['members'] = sum(g.member_count for g in bot.guilds)
            stats['servers_list'] = [
                {'id': str(g.id), 'name': g.name, 'members': g.member_count}
                for g in bot.guilds
            ]
        except:
            pass
        return jsonify(stats)
    return jsonify({
        'servers': 0, 'members': 0, 'commands_run': 0,
        'uptime': '0h', 'warnings': 0,
        'servers_list': [], 'recent_activity': []
    })

# ===== SERVERS =====
@app.route('/api/bots/<bot_id>/servers', methods=['GET'])
@require_auth
def get_servers(bot_id):
    if bot_id not in running_bots:
        return jsonify({'servers': []})
    try:
        bot = running_bots[bot_id]
        servers = [{'id': str(g.id), 'name': g.name, 'members': g.member_count} for g in bot.guilds]
        return jsonify({'servers': servers})
    except:
        return jsonify({'servers': []})

# ===== MODERATION =====
@app.route('/api/bots/<bot_id>/servers/<guild_id>/ban', methods=['POST'])
@require_auth
def ban_user(bot_id, guild_id):
    if bot_id not in running_bots:
        return jsonify({'error': 'Bot non actif'}), 400
    data = request.json
    bot = running_bots[bot_id]
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify({'error': 'Serveur introuvable'}), 404
    try:
        member = guild.get_member(int(data['userId']))
        if not member:
            return jsonify({'error': 'Membre introuvable'}), 404
        async def do_ban():
            try:
                await member.send(f"Banni de {guild.name}: {data.get('reason', '')}")
            except:
                pass
            await member.ban(reason=data.get('reason', ''), delete_message_days=7)
        bot.loop.call_soon_threadsafe(lambda: bot.loop.create_task(do_ban()))
        log_event(bot_id, 'warn', f'Ban: {member} | Raison: {data.get("reason", "")}')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/bots/<bot_id>/servers/<guild_id>/kick', methods=['POST'])
@require_auth
def kick_user(bot_id, guild_id):
    if bot_id not in running_bots:
        return jsonify({'error': 'Bot non actif'}), 400
    data = request.json
    bot = running_bots[bot_id]
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify({'error': 'Serveur introuvable'}), 404
    try:
        member = guild.get_member(int(data['userId']))
        if not member:
            return jsonify({'error': 'Membre introuvable'}), 404
        async def do_kick():
            try:
                await member.send(f"Expulsé de {guild.name}: {data.get('reason', '')}")
            except:
                pass
            await member.kick(reason=data.get('reason', ''))
        bot.loop.call_soon_threadsafe(lambda: bot.loop.create_task(do_kick()))
        log_event(bot_id, 'warn', f'Kick: {member}')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/bots/<bot_id>/servers/<guild_id>/mute', methods=['POST'])
@require_auth
def mute_user(bot_id, guild_id):
    if bot_id not in running_bots:
        return jsonify({'error': 'Bot non actif'}), 400
    data = request.json
    bot = running_bots[bot_id]
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify({'error': 'Serveur introuvable'}), 404
    try:
        member = guild.get_member(int(data['userId']))
        if not member:
            return jsonify({'error': 'Membre introuvable'}), 404
        from datetime import timedelta
        duration = timedelta(seconds=data.get('duration', 600))
        async def do_mute():
            await member.timeout(duration, reason=data.get('reason', ''))
        bot.loop.call_soon_threadsafe(lambda: bot.loop.create_task(do_mute()))
        log_event(bot_id, 'warn', f'Mute: {member} ({data.get("duration", 600)}s)')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/bots/<bot_id>/servers/<guild_id>/unmute', methods=['POST'])
@require_auth
def unmute_user(bot_id, guild_id):
    if bot_id not in running_bots:
        return jsonify({'error': 'Bot non actif'}), 400
    data = request.json
    bot = running_bots[bot_id]
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify({'error': 'Serveur introuvable'}), 404
    try:
        member = guild.get_member(int(data['userId']))
        if not member:
            return jsonify({'error': 'Membre introuvable'}), 404
        async def do_unmute():
            await member.timeout(None)
        bot.loop.call_soon_threadsafe(lambda: bot.loop.create_task(do_unmute()))
        log_event(bot_id, 'info', f'Unmute: {member}')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/bots/<bot_id>/servers/<guild_id>/warn', methods=['POST'])
@require_auth
def warn_user(bot_id, guild_id):
    data = request.json
    log_event(bot_id, 'warn', f'Warn: user {data["userId"]} | {data.get("reason", "")}')
    return jsonify({'success': True})

@app.route('/api/bots/<bot_id>/servers/<guild_id>/purge', methods=['POST'])
@require_auth
def purge_messages(bot_id, guild_id):
    data = request.json
    if bot_id not in running_bots:
        return jsonify({'error': 'Bot non actif'}), 400
    bot = running_bots[bot_id]
    guild = bot.get_guild(int(guild_id))
    channel = guild.get_channel(int(data.get('channelId', 0))) if guild else None
    if channel:
        async def do_purge():
            await channel.purge(limit=data.get('amount', 10))
        bot.loop.call_soon_threadsafe(lambda: bot.loop.create_task(do_purge()))
    log_event(bot_id, 'info', f'Purge: {data.get("amount", 0)} messages')
    return jsonify({'success': True})

@app.route('/api/bots/<bot_id>/servers/<guild_id>/warnings/<user_id>', methods=['GET'])
@require_auth
def get_warnings(bot_id, guild_id, user_id):
    return jsonify({'warnings': []})

@app.route('/api/bots/<bot_id>/servers/<guild_id>/bans', methods=['GET'])
@require_auth
def get_bans(bot_id, guild_id):
    if bot_id not in running_bots:
        return jsonify({'bans': []})
    bot = running_bots[bot_id]
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify({'bans': []})
    try:
        async def get_ban_list():
            bans = [entry async for entry in guild.bans()]
            return [{'user': str(b.user), 'reason': b.reason} for b in bans]
        # Can't easily await from sync, return empty for now
    except:
        pass
    return jsonify({'bans': []})

@app.route('/api/bots/<bot_id>/servers/<guild_id>/unban', methods=['POST'])
@require_auth
def unban_user(bot_id, guild_id):
    if bot_id not in running_bots:
        return jsonify({'error': 'Bot non actif'}), 400
    data = request.json
    bot = running_bots[bot_id]
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify({'error': 'Serveur introuvable'}), 404
    try:
        async def do_unban():
            user = await bot.fetch_user(int(data['userId']))
            await guild.unban(user)
        bot.loop.call_soon_threadsafe(lambda: bot.loop.create_task(do_unban()))
        log_event(bot_id, 'info', f'Unban: user {data["userId"]}')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ===== CONFIG =====
@app.route('/api/bots/<bot_id>/servers/<guild_id>/config', methods=['GET'])
@require_auth
def get_config(bot_id, guild_id):
    key = f'{bot_id}_{guild_id}'
    return jsonify(bot_configs.get(key, {}))

@app.route('/api/bots/<bot_id>/servers/<guild_id>/config', methods=['PUT'])
@require_auth
def update_config(bot_id, guild_id):
    data = request.json
    key = f'{bot_id}_{guild_id}'
    bot_configs[key] = data
    return jsonify({'success': True})

@app.route('/api/bots/<bot_id>/servers/<guild_id>/config/welcome', methods=['PUT'])
@require_auth
def update_welcome(bot_id, guild_id):
    data = request.json
    key = f'{bot_id}_{guild_id}_welcome'
    bot_configs[key] = data
    log_event(bot_id, 'info', f'Welcome configuré pour guild {guild_id}')
    return jsonify({'success': True})

@app.route('/api/bots/<bot_id>/servers/<guild_id>/config/automod', methods=['GET'])
@require_auth
def get_automod_config(bot_id, guild_id):
    key = f'{bot_id}_{guild_id}_automod'
    return jsonify(bot_configs.get(key, {}))

@app.route('/api/bots/<bot_id>/servers/<guild_id>/config/automod', methods=['PUT'])
@require_auth
def update_automod(bot_id, guild_id):
    data = request.json
    key = f'{bot_id}_{guild_id}_automod'
    bot_configs[key] = data
    log_event(bot_id, 'info', f'AutoMod configuré pour guild {guild_id}')
    return jsonify({'success': True})

@app.route('/api/bots/<bot_id>/servers/<guild_id>/config/levels', methods=['PUT'])
@require_auth
def update_levels(bot_id, guild_id):
    data = request.json
    key = f'{bot_id}_{guild_id}_levels'
    bot_configs[key] = data
    return jsonify({'success': True})

@app.route('/api/bots/<bot_id>/servers/<guild_id>/config/logs', methods=['PUT'])
@require_auth
def update_logs(bot_id, guild_id):
    data = request.json
    key = f'{bot_id}_{guild_id}_logs'
    bot_configs[key] = data
    return jsonify({'success': True})

@app.route('/api/bots/<bot_id>/servers/<guild_id>/levels/leaderboard', methods=['GET'])
@require_auth
def get_leaderboard(bot_id, guild_id):
    return jsonify({'leaderboard': []})

@app.route('/api/bots/<bot_id>/servers/<guild_id>/roles', methods=['GET'])
@require_auth
def get_roles(bot_id, guild_id):
    if bot_id not in running_bots:
        return jsonify({'roles': []})
    bot = running_bots[bot_id]
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify({'roles': []})
    roles = [
        {'id': str(r.id), 'name': r.name, 'color': str(r.color), 'members': len(r.members)}
        for r in guild.roles if r != guild.default_role
    ]
    return jsonify({'roles': roles})

@app.route('/api/bots/<bot_id>/servers/<guild_id>/channels', methods=['GET'])
@require_auth
def get_channels(bot_id, guild_id):
    if bot_id not in running_bots:
        return jsonify({'channels': []})
    bot = running_bots[bot_id]
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify({'channels': []})
    channels = [
        {'id': str(c.id), 'name': c.name, 'type': str(c.type)}
        for c in guild.channels
    ]
    return jsonify({'channels': channels})

@app.route('/api/bots/<bot_id>/servers/<guild_id>/giveaways', methods=['GET'])
@require_auth
def get_giveaways(bot_id, guild_id):
    return jsonify({'giveaways': []})

@app.route('/api/bots/<bot_id>/servers/<guild_id>/giveaways', methods=['POST'])
@require_auth
def start_giveaway(bot_id, guild_id):
    data = request.json
    log_event(bot_id, 'info', f'Giveaway lancé: {data.get("prize", "")}')
    return jsonify({'success': True})

@app.route('/api/bots/<bot_id>/servers/<guild_id>/giveaways/<gid>/end', methods=['POST'])
@require_auth
def end_giveaway(bot_id, guild_id, gid):
    log_event(bot_id, 'info', f'Giveaway #{gid} terminé')
    return jsonify({'success': True})

@app.route('/api/bots/<bot_id>/servers/<guild_id>/tickets', methods=['GET'])
@require_auth
def get_tickets(bot_id, guild_id):
    return jsonify({'tickets': []})

@app.route('/api/bots/<bot_id>/servers/<guild_id>/tickets/<tid>/close', methods=['POST'])
@require_auth
def close_ticket(bot_id, guild_id, tid):
    log_event(bot_id, 'info', f'Ticket #{tid} fermé')
    return jsonify({'success': True})

@app.route('/api/bots/<bot_id>/servers/<guild_id>/execute', methods=['POST'])
@require_auth
def execute_command(bot_id, guild_id):
    data = request.json
    log_event(bot_id, 'info', f'Commande: {data.get("command", "")}')
    return jsonify({'success': True, 'output': f'Commande {data.get("command")} exécutée'})

@app.route('/api/bots/<bot_id>/servers/<guild_id>/roles', methods=['POST'])
@require_auth
def create_role(bot_id, guild_id):
    data = request.json
    if bot_id not in running_bots:
        return jsonify({'error': 'Bot non actif'}), 400
    bot = running_bots[bot_id]
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify({'error': 'Serveur introuvable'}), 404
    try:
        async def do_create():
            color = discord.Color(int(data.get('color', '#99AAB5').replace('#', ''), 16))
            await guild.create_role(name=data.get('name', 'Rôle'), color=color, reason=f'Créé via dashboard')
        bot.loop.call_soon_threadsafe(lambda: bot.loop.create_task(do_create()))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/bots/<bot_id>/servers/<guild_id>/roles/<role_id>', methods=['DELETE'])
@require_auth
def delete_role(bot_id, guild_id, role_id):
    if bot_id not in running_bots:
        return jsonify({'error': 'Bot non actif'}), 400
    bot = running_bots[bot_id]
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify({'error': 'Serveur introuvable'}), 404
    role = guild.get_role(int(role_id))
    if role:
        async def do_delete():
            await role.delete(reason='Supprimé via dashboard')
        bot.loop.call_soon_threadsafe(lambda: bot.loop.create_task(do_delete()))
    return jsonify({'success': True})

@app.route('/api/bots/<bot_id>/servers/<guild_id>/channels', methods=['POST'])
@require_auth
def create_channel(bot_id, guild_id):
    data = request.json
    if bot_id not in running_bots:
        return jsonify({'error': 'Bot non actif'}), 400
    bot = running_bots[bot_id]
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify({'error': 'Serveur introuvable'}), 404
    try:
        async def do_create():
            ch_type = data.get('type', 'text')
            if ch_type == 'voice':
                await guild.create_voice_channel(data.get('name', 'Salon'), reason='Créé via dashboard')
            else:
                await guild.create_text_channel(data.get('name', 'salon'), reason='Créé via dashboard')
        bot.loop.call_soon_threadsafe(lambda: bot.loop.create_task(do_create()))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/bots/<bot_id>/servers/<guild_id>/channels/<channel_id>', methods=['DELETE'])
@require_auth
def delete_channel(bot_id, guild_id, channel_id):
    if bot_id not in running_bots:
        return jsonify({'error': 'Bot non actif'}), 400
    bot = running_bots[bot_id]
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify({'error': 'Serveur introuvable'}), 404
    channel = guild.get_channel(int(channel_id))
    if channel:
        async def do_delete():
            await channel.delete(reason='Supprimé via dashboard')
        bot.loop.call_soon_threadsafe(lambda: bot.loop.create_task(do_delete()))
    return jsonify({'success': True})

# ===== COMMANDS LIST =====
@app.route('/api/commands', methods=['GET'])
@require_auth
def get_commands():
    commands_list = [
        {'name': 'ban', 'description': 'Bannir un membre', 'category': 'Modération'},
        {'name': 'unban', 'description': 'Débannir un membre', 'category': 'Modération'},
        {'name': 'kick', 'description': 'Expulser un membre', 'category': 'Modération'},
        {'name': 'mute', 'description': 'Rendre muet un membre', 'category': 'Modération'},
        {'name': 'unmute', 'description': 'Retirer le silence', 'category': 'Modération'},
        {'name': 'warn', 'description': 'Avertir un membre', 'category': 'Modération'},
        {'name': 'unwarn', 'description': 'Retirer un warn', 'category': 'Modération'},
        {'name': 'warnings', 'description': 'Voir les warns', 'category': 'Modération'},
        {'name': 'purge', 'description': 'Supprimer des messages', 'category': 'Modération'},
        {'name': 'slowmode', 'description': 'Slowmode d\'un salon', 'category': 'Modération'},
        {'name': 'lock', 'description': 'Verrouiller un salon', 'category': 'Modération'},
        {'name': 'unlock', 'description': 'Déverrouiller un salon', 'category': 'Modération'},
        {'name': 'nuke', 'description': 'Recréer un salon', 'category': 'Modération'},
        {'name': 'timeout', 'description': 'Timeout un membre', 'category': 'Modération'},
        {'name': 'softban', 'description': 'Softban un membre', 'category': 'Modération'},
        {'name': 'massban', 'description': 'Bannir en masse', 'category': 'Modération'},
        {'name': 'nick', 'description': 'Changer le surnom', 'category': 'Modération'},
        {'name': 'deafen', 'description': 'Rendre sourd', 'category': 'Modération'},
        {'name': 'move', 'description': 'Déplacer en vocal', 'category': 'Modération'},
        {'name': 'disconnect', 'description': 'Déconnecter vocal', 'category': 'Modération'},
        {'name': 'help', 'description': 'Afficher l\'aide', 'category': 'Utilité'},
        {'name': 'serverinfo', 'description': 'Infos du serveur', 'category': 'Utilité'},
        {'name': 'userinfo', 'description': 'Infos d\'un membre', 'category': 'Utilité'},
        {'name': 'avatar', 'description': 'Avatar d\'un membre', 'category': 'Utilité'},
        {'name': 'banner', 'description': 'Bannière d\'un membre', 'category': 'Utilité'},
        {'name': 'ping', 'description': 'Latence du bot', 'category': 'Utilité'},
        {'name': 'uptime', 'description': 'Temps d\'activité', 'category': 'Utilité'},
        {'name': 'botinfo', 'description': 'Infos du bot', 'category': 'Utilité'},
        {'name': 'roleinfo', 'description': 'Infos d\'un rôle', 'category': 'Utilité'},
        {'name': 'channelinfo', 'description': 'Infos d\'un salon', 'category': 'Utilité'},
        {'name': 'poll', 'description': 'Créer un sondage', 'category': 'Utilité'},
        {'name': 'say', 'description': 'Faire dire au bot', 'category': 'Utilité'},
        {'name': 'calculate', 'description': 'Calculer', 'category': 'Utilité'},
        {'name': 'steal', 'description': 'Voler un emoji', 'category': 'Utilité'},
        {'name': 'remindme', 'description': 'Rappel', 'category': 'Utilité'},
        {'name': 'addrole', 'description': 'Ajouter un rôle', 'category': 'Rôles'},
        {'name': 'removerole', 'description': 'Retirer un rôle', 'category': 'Rôles'},
        {'name': 'createrole', 'description': 'Créer un rôle', 'category': 'Rôles'},
        {'name': 'deleterole', 'description': 'Supprimer un rôle', 'category': 'Rôles'},
        {'name': 'editrole', 'description': 'Modifier un rôle', 'category': 'Rôles'},
        {'name': 'roleall', 'description': 'Rôle à tous', 'category': 'Rôles'},
        {'name': 'rolemembers', 'description': 'Membres d\'un rôle', 'category': 'Rôles'},
        {'name': 'color', 'description': 'Changer couleur', 'category': 'Rôles'},
        {'name': 'allroles', 'description': 'Tous les rôles', 'category': 'Rôles'},
        {'name': 'createchannel', 'description': 'Créer un salon', 'category': 'Salons'},
        {'name': 'deletechannel', 'description': 'Supprimer un salon', 'category': 'Salons'},
        {'name': 'renamechannel', 'description': 'Renommer un salon', 'category': 'Salons'},
        {'name': 'clone', 'description': 'Cloner un salon', 'category': 'Salons'},
        {'name': 'rank', 'description': 'Voir son rang', 'category': 'Niveaux'},
        {'name': 'leaderboard', 'description': 'Classement XP', 'category': 'Niveaux'},
        {'name': 'setxp', 'description': 'Définir l\'XP', 'category': 'Niveaux'},
        {'name': 'resetxp', 'description': 'Reset XP', 'category': 'Niveaux'},
        {'name': 'xpreward', 'description': 'Récompense de niveau', 'category': 'Niveaux'},
        {'name': 'giveaway', 'description': 'Lancer un giveaway', 'category': 'Giveaways'},
        {'name': 'giveaway-end', 'description': 'Terminer un giveaway', 'category': 'Giveaways'},
        {'name': 'giveaway-reroll', 'description': 'Relancer un giveaway', 'category': 'Giveaways'},
        {'name': 'ticket-setup', 'description': 'Setup tickets', 'category': 'Tickets'},
        {'name': 'ticket-close', 'description': 'Fermer un ticket', 'category': 'Tickets'},
        {'name': 'ticket-add', 'description': 'Ajouter au ticket', 'category': 'Tickets'},
        {'name': 'setwelcome', 'description': 'Welcome message', 'category': 'Welcome'},
        {'name': 'setgoodbye', 'description': 'Goodbye message', 'category': 'Welcome'},
        {'name': 'autorole', 'description': 'Auto-rôle', 'category': 'Welcome'},
        {'name': 'reactionrole', 'description': 'Reaction role', 'category': 'Reaction Roles'},
        {'name': 'setlogs', 'description': 'Config logs', 'category': 'Logs'},
        {'name': 'embed', 'description': 'Créer un embed', 'category': 'Embeds'},
        {'name': 'announce', 'description': 'Annonce', 'category': 'Embeds'},
        {'name': '8ball', 'description': 'Magic 8-ball', 'category': 'Fun'},
        {'name': 'coinflip', 'description': 'Pile ou face', 'category': 'Fun'},
        {'name': 'dice', 'description': 'Lancer de dés', 'category': 'Fun'},
        {'name': 'ship', 'description': 'Shipper deux membres', 'category': 'Fun'},
        {'name': 'trivia', 'description': 'Quiz', 'category': 'Fun'},
        {'name': 'rps', 'description': 'Pierre Papier Ciseaux', 'category': 'Fun'},
        {'name': 'choose', 'description': 'Choisir parmi des options', 'category': 'Fun'},
        {'name': 'rate', 'description': 'Noter quelque chose', 'category': 'Fun'},
        {'name': 'meme', 'description': 'Mème aléatoire', 'category': 'Fun'},
        {'name': 'joke', 'description': 'Blague', 'category': 'Fun'},
        {'name': 'owo', 'description': 'OwO-ifier', 'category': 'Fun'},
        {'name': 'setup', 'description': 'Setup rapide', 'category': 'Serveur'},
        {'name': 'server-stats', 'description': 'Stats détaillées', 'category': 'Serveur'},
        {'name': 'server-audit', 'description': 'Audit du serveur', 'category': 'Serveur'},
        {'name': 'backup', 'description': 'Backup des rôles', 'category': 'Serveur'},
        {'name': 'massrole', 'description': 'Rôle en masse', 'category': 'Serveur'},
        {'name': 'bans', 'description': 'Liste des bans', 'category': 'Serveur'},
        {'name': 'permissions', 'description': 'Permissions d\'un membre', 'category': 'Serveur'},
        {'name': 'reminder', 'description': 'Rappel', 'category': 'Extras'},
        {'name': 'weather', 'description': 'Météo', 'category': 'Extras'},
        {'name': 'color-info', 'description': 'Info couleur', 'category': 'Extras'},
        {'name': 'timestamp', 'description': 'Timestamp Discord', 'category': 'Extras'},
        {'name': 'encode', 'description': 'Encoder base64', 'category': 'Extras'},
        {'name': 'decode', 'description': 'Décoder base64', 'category': 'Extras'},
        {'name': 'qr', 'description': 'QR Code', 'category': 'Extras'},
        {'name': 'ascii', 'description': 'ASCII Art', 'category': 'Extras'},
    ]
    return jsonify({'commands': commands_list})

# ===== CONSOLE =====
@app.route('/api/bots/<bot_id>/console', methods=['GET'])
@require_auth
def get_console_logs(bot_id):
    logs = bot_logs.get(bot_id, [])[-100:]
    return jsonify({'logs': logs})

@app.route('/api/bots/<bot_id>/console', methods=['POST'])
@require_auth
def send_console_command(bot_id):
    data = request.json
    cmd = data.get('command', '')
    log_event(bot_id, 'info', f'Console: {cmd}')
    return jsonify({'success': True, 'output': f'Commande "{cmd}" reçue'})

def log_event(bot_id, level, message):
    if bot_id not in bot_logs:
        bot_logs[bot_id] = []
    bot_logs[bot_id].append({
        'time': datetime.utcnow().strftime('%H:%M:%S'),
        'level': level,
        'message': message
    })
    if len(bot_logs[bot_id]) > 1000:
        bot_logs[bot_id] = bot_logs[bot_id][-500:]

@app.route('/')
def index():
    return jsonify({
        'name': 'Discord Bot Dashboard API',
        'version': '2.0',
        'status': 'running',
        'dashboard': 'https://ton-username.github.io/discord-bot-dashboard/',
        'endpoints': ['/api/auth/login', '/api/bots', '/api/commands']
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 50)
    print("  DISCORD BOT DASHBOARD - BACKEND API")
    print("=" * 50)
    print(f"  Port: {port}")
    print(f"  API Key: {API_KEY}")
    print(f"  Dashboard: Ouvre dashboard/index.html")
    print("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=False)
