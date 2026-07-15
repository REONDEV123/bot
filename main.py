#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           LYTRIX BOT v1.0.0                                ║
║                      Made by Reon | All-in-One Bot                          ║
║  500+ Commands | AntiNuke | Music | Tickets | Moderation | Fun | Economy   ║
╚══════════════════════════════════════════════════════════════════════════════╝
╔══════════════════════════════════════════════════════════════════════════════╗
║  CONFIG: Edit BOT_TOKEN, CLIENT_ID, OWNER_IDS below                        ║
║  Get token at: https://discord.com/developers/applications                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
# ============================================================
# 🔑 CONFIGURATION — EDIT THESE 3 VALUES
# ============================================================
BOT_TOKEN    = "PUT_YOUR_BOT_TOKEN_HERE"       # Your Discord bot token
CLIENT_ID    = "PUT_YOUR_CLIENT_ID_HERE"       # Your bot's Application/Client ID
OWNER_IDS    = [123456789012345678]             # Your Discord user ID (right-click your name → Copy ID)
BOT_PREFIX   = "!"                              # Default command prefix

# Developer mode: right-click your name in Discord → Copy ID to get your user ID.
# Then paste it inside the OWNER_IDS list above (replace the example number).
# ============================================================

import asyncio
import datetime
import functools
import hashlib
import io
import json
import math
import os
import random
import re
import string
import sys
import time
import traceback
from collections import Counter, defaultdict, deque
from datetime import timedelta
from typing import Dict, List, Optional, Set, Tuple, Union

import discord
from discord import (
    app_commands, ui, ButtonStyle, Interaction, Embed, Color, 
    PermissionOverwrite, TextChannel, VoiceChannel, Role, Member,
    Guild, Message, SelectOption, TextStyle, File
)
from discord.ext import commands, tasks
from discord.ui import View, Button, Select, Modal, button, select

# ============================================================
# JSON DATABASE MANAGER
# ============================================================
DB_DIR = "lytrix_data"
os.makedirs(DB_DIR, exist_ok=True)

class JSONDB:
    """Thread-safe JSON database for all bot data."""
    def __init__(self, filename: str):
        self.path = os.path.join(DB_DIR, filename)
        self._lock = asyncio.Lock()
        self._ensure()

    def _ensure(self):
        if not os.path.exists(self.path):
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump({}, f)

    async def read(self) -> dict:
        async with self._lock:
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}

    async def write(self, data: dict):
        async with self._lock:
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)

    async def get(self, key: str, default=None):
        d = await self.read()
        return d.get(key, default)

    async def set(self, key: str, value):
        d = await self.read()
        d[key] = value
        await self.write(d)

    async def delete(self, key: str):
        d = await self.read()
        d.pop(key, None)
        await self.write(d)

    async def all(self) -> dict:
        return await self.read()

# Initialize databases
db_config = JSONDB("config.json")
db_guilds = JSONDB("guilds.json")
db_users = JSONDB("users.json")
db_warns = JSONDB("warns.json")
db_cases = JSONDB("cases.json")
db_mutes = JSONDB("mutes.json")
db_tickets = JSONDB("tickets.json")
db_music = JSONDB("music.json")
db_economy = JSONDB("economy.json")
db_antinuke = JSONDB("antinuke.json")
db_levels = JSONDB("levels.json")
db_giveaways = JSONDB("giveaways.json")
db_reaction_roles = JSONDB("reaction_roles.json")
db_welcome = JSONDB("welcome.json")
db_logs = JSONDB("logs.json")
db_automod = JSONDB("automod.json")
db_reminders = JSONDB("reminders.json")
db_snipes = JSONDB("snipes.json")

# ============================================================
# CONSTANTS & CONFIG
# ============================================================
# BOT_PREFIX and OWNER_IDS are now defined in the CONFIG section above
LYTRIX_COLOR = 0x8B5CF6
LYTRIX_COLOR2 = 0xEC4899
LYTRIX_COLORS = [0x8B5CF6, 0xEC4899, 0x6366F1, 0x06B6D4, 0x10B981, 0xF59E0B, 0xEF4444]

ANIMALS = ["🐶 Dog", "🐱 Cat", "🐭 Mouse", "🐹 Hamster", "🐰 Rabbit", "🦊 Fox", "🐻 Bear",
           "🐼 Panda", "🐨 Koala", "🐯 Tiger", "🦁 Lion", "🐮 Cow", "🐷 Pig", "🐸 Frog",
           "🐵 Monkey", "🐔 Chicken", "🐧 Penguin", "🐦 Bird", "🐤 Chick", "🦆 Duck",
           "🦅 Eagle", "🦉 Owl", "🦇 Bat", "🐺 Wolf", "🐗 Boar", "🐴 Horse", "🦄 Unicorn"]

EIGHT_BALL_RESPONSES = [
    "🎱 It is certain.", "🎱 It is decidedly so.", "🎱 Without a doubt.",
    "🎱 Yes definitely.", "🎱 You may rely on it.", "🎱 As I see it, yes.",
    "🎱 Most likely.", "🎱 Outlook good.", "🎱 Yes.", "🎱 Signs point to yes.",
    "🎱 Reply hazy, try again.", "🎱 Ask again later.", "🎱 Better not tell you now.",
    "🎱 Cannot predict now.", "🎱 Concentrate and ask again.", "🎱 Don't count on it.",
    "🎱 My reply is no.", "🎱 My sources say no.", "🎱 Outlook not so good.",
    "🎱 Very doubtful."
]

# ============================================================
# BOT INITIALIZATION
# ============================================================
intents = discord.Intents.all()
intents.message_content = True
intents.members = True
intents.presences = True
intents.voice_states = True
intents.guilds = True
intents.bans = True
intents.emojis_and_stickers = True
intents.integrations = True
intents.webhooks = True
intents.invites = True

class LytrixBot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix=self._get_prefix,
            intents=intents,
            case_insensitive=True,
            strip_after_prefix=True,
            owner_ids=set(OWNER_IDS),
            help_command=None,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="🌌 Lytrix | !help"
            ),
            status=discord.Status.online,
            max_messages=10000,
            chunk_guilds_at_startup=True,
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, users=True, replied_user=True
            ),
        )
        self.start_time = time.time()
        self.command_usage = defaultdict(int)
        self.anti_nuke = AntiNuke(self)
        self.ticket_manager = TicketManager(self)
        self.music_manager = MusicManager(self)
        self.case_counter = defaultdict(int)
        self.snipes: Dict[int, Dict] = {}
        self.edit_snipes: Dict[int, Dict] = {}
        self.reaction_snipes: Dict[int, Dict] = {}
        self.afk_users: Dict[int, Tuple[str, float]] = {}
        self._voice_clients: Dict[int, 'MusicPlayer'] = {}
        self.temp_mutes: Dict[int, asyncio.Task] = {}
        self.temp_bans: Dict[int, asyncio.Task] = {}
        self.reminder_tasks: Dict[str, asyncio.Task] = {}
        self.guild_locks: Dict[int, asyncio.Lock] = {}
        self._command_cooldowns: Dict[str, Dict[int, float]] = defaultdict(dict)

    async def _get_prefix(self, bot, message):
        if message.guild:
            guild_id = str(message.guild.id)
            custom = await db_guilds.get(guild_id, {})
            return commands.when_mentioned_or(custom.get("prefix", BOT_PREFIX))(bot, message)
        return commands.when_mentioned_or(BOT_PREFIX)(bot, message)

    async def get_prefix_str(self, guild):
        if guild:
            g = await db_guilds.get(str(guild.id), {})
            return g.get("prefix", BOT_PREFIX)
        return BOT_PREFIX

    async def on_ready(self):
        print(f"""
╔══════════════════════════════════════════════════╗
║        🌌 LYTRIX BOT IS ONLINE 🌌              ║
║  User: {self.user.name}#{self.user.discriminator}  ║
║  ID: {self.user.id}                         ║
║  Guilds: {len(self.guilds)}                             ║
║  Users: {sum(g.member_count for g in self.guilds)}                        ║
║  Latency: {round(self.latency * 1000)}ms                        ║
║  Made by Reon                                ║
╚══════════════════════════════════════════════════╝
        """)
        self.status_loop.start()
        self.auto_unmute_loop.start()
        self.auto_unban_loop.start()
        self.ticket_cleanup_loop.start()
        self.reminder_loop.start()
        self.giveaway_loop.start()
        await self.register_slash_commands()

    async def register_slash_commands(self):
        self.tree.add_command(HelpSlash())
        self.tree.add_command(PingSlash())
        self.tree.add_command(InviteSlash())
        try:
            await self.tree.sync()
        except Exception as e:
            print(f"Slash sync error: {e}")

    @tasks.loop(minutes=5)
    async def status_loop(self):
        statuses = [
            discord.Activity(type=discord.ActivityType.watching, name=f"🌌 {len(self.guilds)} servers | !help"),
            discord.Activity(type=discord.ActivityType.listening, name=f"🎵 {len(self._voice_clients)} voice channels"),
            discord.Activity(type=discord.ActivityType.playing, name=f"⚡ Lytrix by Reon"),
            discord.Activity(type=discord.ActivityType.watching, name=f"🛡️ AntiNuke Active"),
            discord.Activity(type=discord.ActivityType.listening, name="🎧 !play <song>"),
            discord.Activity(type=discord.ActivityType.streaming, name="Lytrix Bot", url="https://twitch.tv/reon"),
            discord.Activity(type=discord.ActivityType.competing, name="🏆 Best All-in-One Bot"),
        ]
        for s in statuses:
            await self.change_presence(activity=s)
            await asyncio.sleep(30)

    @tasks.loop(seconds=30)
    async def auto_unmute_loop(self):
        now = time.time()
        mutes = await db_mutes.all()
        for key, data in list(mutes.items()):
            if data.get("expires_at") and data["expires_at"] < now:
                guild = self.get_guild(data.get("guild_id", 0))
                if guild:
                    member = guild.get_member(int(data.get("user_id", 0)))
                    if member:
                        try:
                            mute_role = guild.get_role(data.get("role_id", 0))
                            if mute_role and mute_role in member.roles:
                                await member.remove_roles(mute_role, reason="Auto-unmute")
                        except:
                            pass
                await db_mutes.delete(key)

    @tasks.loop(seconds=60)
    async def auto_unban_loop(self):
        now = time.time()
        temp_bans = await db_config.get("temp_bans", {})
        for key, data in list(temp_bans.items()):
            if data.get("expires_at") and data["expires_at"] < now:
                guild = self.get_guild(data.get("guild_id", 0))
                if guild:
                    try:
                        user = await self.fetch_user(int(data.get("user_id", 0)))
                        await guild.unban(user, reason="Temp-ban expired")
                    except:
                        pass
                temp_bans.pop(key, None)
        await db_config.set("temp_bans", temp_bans)

    @tasks.loop(seconds=30)
    async def ticket_cleanup_loop(self):
        tickets = await db_tickets.all()
        for key, data in list(tickets.items()):
            if data.get("status") == "closed":
                closed_at = data.get("closed_at", 0)
                guild = self.get_guild(data.get("guild_id", 0))
                if guild:
                    cfg = await db_guilds.get(str(guild.id), {})
                    auto_close_hours = cfg.get("ticket_auto_close", 48)
                    if time.time() - closed_at > auto_close_hours * 3600:
                        channel = guild.get_channel(data.get("channel_id", 0))
                        if channel:
                            await self.ticket_manager.save_transcript(channel, data)
                            try:
                                await channel.delete(reason="Auto ticket cleanup")
                            except:
                                pass
                        await db_tickets.delete(key)

    @tasks.loop(seconds=10)
    async def reminder_loop(self):
        reminders = await db_reminders.all()
        now = time.time()
        for key, data in list(reminders.items()):
            if data.get("time", 0) <= now:
                user = self.get_user(data.get("user_id", 0))
                if user:
                    try:
                        embed = Embed(
                            title="⏰ Reminder!",
                            description=data.get("message", "You asked me to remind you!"),
                            color=LYTRIX_COLOR,
                            timestamp=datetime.datetime.fromtimestamp(now)
                        )
                        embed.set_footer(text="Lytrix Reminder System • Made by Reon")
                        await user.send(embed=embed)
                    except:
                        pass
                await db_reminders.delete(key)

    @tasks.loop(seconds=15)
    async def giveaway_loop(self):
        giveaways = await db_giveaways.all()
        now = time.time()
        for key, data in list(giveaways.items()):
            if data.get("end_time", 0) <= now and not data.get("ended"):
                await self._end_giveaway(key, data)

    async def _end_giveaway(self, key, data):
        guild = self.get_guild(data.get("guild_id", 0))
        if not guild:
            await db_giveaways.delete(key)
            return
        channel = guild.get_channel(data.get("channel_id", 0))
        if not channel:
            await db_giveaways.delete(key)
            return
        try:
            msg = await channel.fetch_message(int(data.get("message_id", 0)))
        except:
            await db_giveaways.delete(key)
            return

        winners = []
        participants = data.get("participants", [])
        win_count = min(data.get("winners", 1), len(participants)) if participants else 0
        if win_count > 0:
            winners = random.sample(participants, win_count)

        embed = msg.embeds[0] if msg.embeds else Embed()
        embed.title = "🎉 Giveaway Ended!"
        embed.color = 0xEF4444
        winner_text = ", ".join(f"<@{w}>" for w in winners) if winners else "No valid participants"
        embed.description = f"{embed.description}\n\n**Winners:** {winner_text}"
        embed.set_footer(text=f"Ended at • {win_count} winner(s)")
        try:
            await msg.edit(embed=embed)
        except:
            pass

        if winners:
            prize = data.get("prize", "Prize")
            await channel.send(
                f"🎉 Congratulations {', '.join(f'<@{w}>' for w in winners)}! "
                f"You won **{prize}**!\n{msg.jump_url}",
                allowed_mentions=discord.AllowedMentions(users=True)
            )

        data["ended"] = True
        data["winners_list"] = winners
        await db_giveaways.set(key, data)

bot = LytrixBot()

# ============================================================
# HELPER FUNCTIONS & DECORATORS
# ============================================================
def make_embed(title: str = None, description: str = None, color: int = LYTRIX_COLOR,
               footer: str = None, thumbnail: str = None, image: str = None,
               author: str = None, author_icon: str = None, fields: List[Tuple] = None,
               timestamp: bool = False) -> Embed:
    embed = Embed(title=title, description=description, color=color)
    if footer:
        embed.set_footer(text=footer, icon_url="https://i.imgur.com/6V7sH4o.png")
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    if image:
        embed.set_image(url=image)
    if author:
        embed.set_author(name=author, icon_url=author_icon or "")
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    if timestamp:
        embed.timestamp = datetime.datetime.utcnow()
    return embed

def success_embed(desc: str) -> Embed:
    return make_embed(title="✅ Success", description=desc, color=0x10B981)

def error_embed(desc: str) -> Embed:
    return make_embed(title="❌ Error", description=desc, color=0xEF4444)

def warn_embed(desc: str) -> Embed:
    return make_embed(title="⚠️ Warning", description=desc, color=0xF59E0B)

async def check_hierarchy(ctx, target: Member) -> bool:
    if ctx.author.top_role <= target.top_role and ctx.author.id != ctx.guild.owner_id:
        await ctx.send(embed=error_embed("You cannot target someone with a higher or equal role!"))
        return False
    if ctx.guild.me.top_role <= target.top_role:
        await ctx.send(embed=error_embed("I cannot target someone with a higher or equal role!"))
        return False
    return True

async def get_mute_role(guild: Guild) -> Optional[Role]:
    mute_role = discord.utils.get(guild.roles, name="Lytrix-Muted")
    if not mute_role:
        try:
            mute_role = await guild.create_role(
                name="Lytrix-Muted",
                color=0x818181,
                reason="Created by Lytrix for mutes",
                permissions=discord.Permissions(
                    send_messages=False,
                    speak=False,
                    add_reactions=False,
                    send_messages_in_threads=False,
                    create_public_threads=False,
                    create_private_threads=False,
                    use_application_commands=True
                )
            )
            for channel in guild.channels:
                try:
                    await channel.set_permissions(mute_role, send_messages=False, speak=False,
                                                   add_reactions=False, send_messages_in_threads=False)
                except:
                    pass
        except:
            return None
    return mute_role

def format_time(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    elif seconds < 86400:
        h, r = divmod(seconds, 3600)
        return f"{int(h)}h {int(r // 60)}m"
    else:
        d, r = divmod(seconds, 86400)
        h, r = divmod(r, 3600)
        return f"{int(d)}d {int(h)}h {int(r // 60)}m"

def progress_bar(current, total, length=20) -> str:
    filled = int(length * current / total) if total > 0 else 0
    bar = "▰" * filled + "▱" * (length - filled)
    return bar

# ============================================================
# ANTI-NUKE SYSTEM (WICK STYLE)
# ============================================================
class AntiNuke:
    """Enterprise-grade anti-nuke system like Wick Bot."""
    def __init__(self, bot: LytrixBot):
        self.bot = bot
        self._rate_limits: Dict[str, List[float]] = defaultdict(list)
        self._action_log: Dict[int, List[Dict]] = defaultdict(list)
        self._lockdown_guilds: Set[int] = set()

    async def get_config(self, guild_id: int) -> dict:
        return await db_antinuke.get(str(guild_id), {
            "enabled": False,
            "log_channel": None,
            "punishment": "ban",  # ban, kick, quarantine, strip_roles
            "whitelist": [],
            "bypass_roles": [],
            "modules": {
                "anti_ban": True,
                "anti_kick": True,
                "anti_channel_create": True,
                "anti_channel_delete": True,
                "anti_channel_update": True,
                "anti_role_create": True,
                "anti_role_delete": True,
                "anti_role_update": True,
                "anti_webhook_create": True,
                "anti_webhook_delete": True,
                "anti_emoji_delete": True,
                "anti_emoji_create": True,
                "anti_guild_update": True,
                "anti_integration": True,
                "anti_bot_add": True,
                "anti_mass_mention": True,
                "anti_mass_ban": True,
                "anti_mass_kick": True,
                "anti_mass_channel": True,
                "anti_mass_role": True,
                "anti_everyone_here": True,
                "anti_spam": True,
                "anti_sticker": True,
                "anti_thread": True,
                "anti_event": True,
            },
            "thresholds": {
                "ban": 2, "kick": 2, "channel": 3, "role": 3,
                "webhook": 2, "emoji": 3, "mention": 10,
                "spam_msgs": 7, "spam_seconds": 5,
            },
            "lockdown_on_raid": True,
            "recovery_backup": False,
            "dm_alert": True,
        })

    def is_whitelisted(self, config: dict, user_id: int) -> bool:
        return str(user_id) in config.get("whitelist", []) or \
               user_id in OWNER_IDS or \
               user_id == self.bot.user.id

    def has_bypass(self, config: dict, member: Member) -> bool:
        if self.is_whitelisted(config, member.id):
            return True
        bypass_roles = config.get("bypass_roles", [])
        return any(str(r.id) in bypass_roles for r in member.roles)

    async def log_action(self, guild: Guild, action: str, target: str, 
                         executor: str, details: str = "", color: int = 0xEF4444):
        config = await self.get_config(guild.id)
        log_channel_id = config.get("log_channel")
        if log_channel_id:
            channel = guild.get_channel(int(log_channel_id))
            if channel:
                embed = Embed(
                    title=f"🛡️ AntiNuke: {action}",
                    description=details,
                    color=color,
                    timestamp=datetime.datetime.utcnow()
                )
                embed.add_field(name="Executor", value=executor, inline=True)
                embed.add_field(name="Target", value=target, inline=True)
                embed.set_footer(text="Lytrix AntiNuke • Made by Reon")
                try:
                    await channel.send(embed=embed)
                except:
                    pass

        self._action_log[guild.id].append({
            "action": action, "target": target, "executor": executor,
            "details": details, "time": time.time()
        })

    async def punish(self, guild: Guild, member: Member, reason: str):
        config = await self.get_config(guild.id)
        punishment = config.get("punishment", "ban")

        if self.has_bypass(config, member):
            return

        try:
            if punishment == "ban":
                try:
                    await member.send(embed=Embed(
                        title="🚨 AntiNuke Action",
                        description=f"You have been banned from **{guild.name}**\nReason: {reason}",
                        color=0xEF4444
                    ).set_footer(text="Lytrix AntiNuke • Made by Reon"))
                except:
                    pass
                await member.ban(reason=f"Lytrix AntiNuke: {reason}", delete_message_days=7)
            elif punishment == "kick":
                await member.kick(reason=f"Lytrix AntiNuke: {reason}")
            elif punishment == "quarantine":
                q_role = discord.utils.get(guild.roles, name="Lytrix-Quarantined")
                if not q_role:
                    q_role = await guild.create_role(name="Lytrix-Quarantined", color=0xFF0000)
                    for ch in guild.channels:
                        try:
                            await ch.set_permissions(q_role, send_messages=False, speak=False,
                                                      read_messages=True, connect=False)
                        except:
                            pass
                await member.add_roles(q_role, reason=f"Lytrix AntiNuke: {reason}")
            elif punishment == "strip_roles":
                roles_to_remove = [r for r in member.roles if not r.is_bot_managed() and 
                                   r != guild.default_role and r.is_assignable()]
                await member.remove_roles(*roles_to_remove, reason=f"Lytrix AntiNuke: {reason}")
        except:
            pass

    async def check_rate(self, guild_id: int, action_type: str, 
                         config: dict, user_id: int) -> bool:
        """Returns True if action should be blocked."""
        threshold = config.get("thresholds", {}).get(action_type, 3)
        key = f"{guild_id}:{action_type}"
        now = time.time()
        self._rate_limits[key] = [t for t in self._rate_limits.get(key, []) if now - t < 10]
        self._rate_limits[key].append(now)
        return len(self._rate_limits[key]) > threshold

    async def recover_guild(self, guild: Guild):
        """Attempt to recover guild from a nuke."""
        config = await self.get_config(guild.id)
        backup = await db_antinuke.get(f"backup_{guild.id}", {})
        if not backup:
            return

        # Restore roles
        existing_roles = {r.name: r for r in guild.roles}
        for role_data in backup.get("roles", []):
            if role_data["name"] not in existing_roles:
                try:
                    await guild.create_role(
                        name=role_data["name"],
                        color=role_data.get("color", 0),
                        permissions=discord.Permissions(role_data.get("permissions", 0)),
                        reason="Lytrix Recovery"
                    )
                except:
                    pass

        # Restore channels
        existing_channels = {c.name: c for c in guild.channels}
        for ch_data in backup.get("channels", []):
            if ch_data["name"] not in existing_channels:
                try:
                    if ch_data.get("type") == "text":
                        await guild.create_text_channel(
                            name=ch_data["name"],
                            reason="Lytrix Recovery"
                        )
                    elif ch_data.get("type") == "voice":
                        await guild.create_voice_channel(
                            name=ch_data["name"],
                            reason="Lytrix Recovery"
                        )
                except:
                    pass

    async def create_backup(self, guild: Guild):
        backup = {
            "name": guild.name,
            "roles": [{"name": r.name, "color": r.color.value,
                       "permissions": r.permissions.value} 
                      for r in guild.roles if not r.is_bot_managed() and r.is_assignable()],
            "channels": [{"name": c.name, "type": str(c.type)} for c in guild.channels],
            "time": time.time()
        }
        await db_antinuke.set(f"backup_{guild.id}", backup)

    async def enter_lockdown(self, guild: Guild):
        """Lock down entire server."""
        self._lockdown_guilds.add(guild.id)
        for channel in guild.channels:
            if isinstance(channel, (TextChannel, VoiceChannel)):
                try:
                    await channel.set_permissions(guild.default_role, send_messages=False,
                                                   connect=False, speak=False)
                except:
                    pass

    async def exit_lockdown(self, guild: Guild):
        self._lockdown_guilds.discard(guild.id)
        for channel in guild.channels:
            if isinstance(channel, (TextChannel, VoiceChannel)):
                try:
                    await channel.set_permissions(guild.default_role, send_messages=None,
                                                   connect=None, speak=None)
                except:
                    pass

anti_nuke = None  # Will be set after bot init

# ============================================================
# MUSIC SYSTEM (CRAZY STYLE)
# ============================================================
class MusicPlayer:
    """Advanced music player with filters."""
    def __init__(self, ctx: commands.Context):
        self.ctx = ctx
        self.bot = ctx.bot
        self.guild_id = ctx.guild.id
        self.channel = ctx.author.voice.channel if ctx.author.voice else None
        self.queue: deque = deque()
        self.queue_history: deque = deque(maxlen=50)
        self.current = None
        self.next = asyncio.Event()
        self.now_playing_message: Optional[Message] = None
        self.volume: float = 1.0
        self.loop_mode: str = "off"  # off, track, queue
        self.autoplay: bool = False
        self.dj_role_id: Optional[int] = None
        self._filters: Dict[str, float] = {
            "bassboost": 0.0, "speed": 1.0, "pitch": 1.0,
            "nightcore": False, "vaporwave": False, "karaoke": False,
            "tremolo": 0.0, "vibrato": 0.0, "distortion": 0.0,
            "echo": 0.0, "reverb": False, "lofi": False,
            "chipmunk": False, "earrape": False, "daycore": False,
        }
        self.task: Optional[asyncio.Task] = None
        self.paused: bool = False
        self.stopped: bool = False
        self._247_mode: bool = False
        self.skip_votes: Set[int] = set()

    @property
    def is_playing(self) -> bool:
        return self.voice and self.current is not None

    @property
    def voice(self):
        return discord.utils.get(self.bot.voice_clients, guild__id=self.guild_id)

    async def connect(self):
        if not self.channel:
            return False
        if self.voice:
            if self.voice.channel != self.channel:
                await self.voice.move_to(self.channel)
            return True
        await self.channel.connect()
        return True

    async def disconnect(self):
        self.stopped = True
        if self.task:
            self.task.cancel()
        if self.voice:
            await self.voice.disconnect(force=True)
        self.bot._voice_clients.pop(self.guild_id, None)

    async def play_next(self):
        self.next.set()

    def build_ffmpeg_options(self) -> dict:
        """Build FFmpeg options including audio filters."""
        options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

        filter_chain = []

        if self._filters.get("bassboost", 0) > 0:
            gain = 2 + self._filters["bassboost"] * 18
            filter_chain.append(f'bass=g={gain}:f=80:w=0.3')

        if self._filters.get("speed", 1.0) != 1.0:
            filter_chain.append(f'atempo={self._filters["speed"]}')

        if self._filters.get("nightcore"):
            filter_chain.append('asetrate=44100*1.25,aresample=44100,atempo=1.0')

        if self._filters.get("vaporwave"):
            filter_chain.append('asetrate=44100*0.8,aresample=44100,atempo=1.0')

        if self._filters.get("chipmunk"):
            filter_chain.append('asetrate=44100*1.5,aresample=44100,atempo=1.0')

        if self._filters.get("daycore"):
            filter_chain.append('asetrate=44100*0.7,aresample=44100,atempo=1.0')

        if self._filters.get("earrape"):
            filter_chain.append('volume=10.0')

        if self._filters.get("karaoke"):
            filter_chain.append('stereotools=mlev=0.015625')

        if self._filters.get("tremolo", 0) > 0:
            filter_chain.append(f'tremolo=f={5 + self._filters["tremolo"] * 15}:d=0.7')

        if self._filters.get("vibrato", 0) > 0:
            filter_chain.append(f'vibrato=f={5 + self._filters["vibrato"] * 10}:d=0.7')

        if self._filters.get("distortion", 0) > 0:
            filter_chain.append(f'aecho=0.8:0.9:{20 * self._filters["distortion"]}:0.5')

        if self._filters.get("echo", 0) > 0:
            filter_chain.append(f'aecho=0.8:0.9:{50 * self._filters["echo"]}:0.3')

        if self._filters.get("reverb"):
            filter_chain.append('aecho=0.8:0.5:40:0.3,aecho=0.8:0.5:80:0.3')

        if self._filters.get("lofi"):
            filter_chain.append('acrusher=level_in=8:level_out=0.5:bits=8:mode=log:aa=1')

        if filter_chain:
            options['options'] += ' -af ' + ','.join(filter_chain)

        if self.volume != 1.0:
            vol_filter = f'volume={self.volume}'
            if '-af' in options.get('options', ''):
                options['options'] += ',' + vol_filter
            else:
                options['options'] += ' -af ' + vol_filter

        return options

    async def play_song(self, song: dict):
        self.current = song
        self.paused = False
        self.skip_votes.clear()

        try:
            import yt_dlp
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True, 'no_warnings': True,
                'extractaudio': True,
                'default_search': 'ytsearch',
                'source_address': '0.0.0.0',
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(song['url'], download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                url = info.get('url')
                song['title'] = info.get('title', song.get('title', 'Unknown'))
                song['duration'] = info.get('duration', 0)
                song['thumbnail'] = info.get('thumbnail', '')
                song['uploader'] = info.get('uploader', 'Unknown')
                song['webpage_url'] = info.get('webpage_url', song.get('url', ''))
        except:
            url = song['url']

        ffmpeg_opts = self.build_ffmpeg_options()
        source = discord.FFmpegPCMAudio(url, **ffmpeg_opts)
        source = discord.PCMVolumeTransformer(source, volume=self.volume)

        def after_play(error):
            if error:
                print(f"Playback error: {error}")
            self.bot.loop.call_soon_threadsafe(self.play_next)

        if self.voice:
            self.voice.play(source, after=after_play)

        if self.now_playing_message:
            try:
                await self.now_playing_message.delete()
            except:
                pass

        embed = Embed(
            title="🎵 Now Playing",
            description=f"**[{song.get('title', 'Unknown')}]({song.get('webpage_url', '')})**",
            color=LYTRIX_COLOR
        )
        embed.add_field(name="👤 Uploader", value=song.get('uploader', 'Unknown'), inline=True)
        dur = song.get('duration', 0)
        embed.add_field(name="⏱️ Duration", value=format_time(dur) if dur else "Live", inline=True)
        embed.add_field(name="🔊 Volume", value=f"{int(self.volume * 100)}%", inline=True)
        embed.add_field(name="🔁 Loop", value=self.loop_mode.title(), inline=True)
        if song.get('thumbnail'):
            embed.set_thumbnail(url=song['thumbnail'])
        embed.set_footer(text=f"Requested by {song.get('requester', 'Unknown')} • Lytrix Music")
        self.now_playing_message = await self.ctx.send(embed=embed)

    async def player_loop(self):
        while not self.stopped:
            self.next.clear()
            if self.loop_mode == "track" and self.current and self.queue:
                pass
            elif self.queue:
                song = self.queue.popleft()
                if self.loop_mode == "queue" and self.current:
                    self.queue.append(self.current)
                self.queue_history.append(song)
                await self.play_song(song)
            elif self.autoplay and self.queue_history:
                # Try to find a related song
                last = self.queue_history[-1]
                # For now just stop; full autoplay would need YouTube API
                self.autoplay = False
                self.current = None
                await self.ctx.send(embed=warn_embed("Queue ended. Autoplay requires YouTube API key configured."))
                break
            else:
                self.current = None
                if not self._247_mode:
                    await self.ctx.send(embed=make_embed(
                        title="🎵 Queue Ended",
                        description="All songs have been played. Use `!247` to keep me in VC.",
                        color=LYTRIX_COLOR
                    ))
                    await asyncio.sleep(30)
                    if not self.is_playing and not self.queue:
                        await self.disconnect()
                        break
                break

            try:
                await asyncio.wait_for(self.next.wait(), timeout=600 if self._247_mode else 300)
            except asyncio.TimeoutError:
                if not self._247_mode and not self.is_playing:
                    await self.disconnect()
                    break


class MusicManager:
    """Manages all music players."""
    def __init__(self, bot: LytrixBot):
        self.bot = bot

    def get_player(self, ctx: commands.Context) -> MusicPlayer:
        if ctx.guild.id not in self.bot._voice_clients:
            self.bot._voice_clients[ctx.guild.id] = MusicPlayer(ctx)
        player = self.bot._voice_clients[ctx.guild.id]
        player.ctx = ctx
        return player

    async def ensure_voice(self, ctx: commands.Context) -> Optional[MusicPlayer]:
        if not ctx.author.voice:
            await ctx.send(embed=error_embed("You must be in a voice channel!"))
            return None
        player = self.get_player(ctx)
        player.channel = ctx.author.voice.channel
        if ctx.voice_client and ctx.voice_client.channel != player.channel:
            if ctx.voice_client.is_playing():
                await ctx.send(embed=error_embed("I'm already playing in another channel!"))
                return None
        await player.connect()
        return player

# ============================================================
# TICKET SYSTEM (R.O.T.I STYLE)
# ============================================================
class TicketView(View):
    """Interactive ticket panel with buttons."""
    def __init__(self, bot: LytrixBot):
        super().__init__(timeout=None)
        self.bot = bot

    @button(label="🎫 Create Ticket", style=ButtonStyle.blurple, custom_id="ticket_create", emoji="🎫")
    async def create_ticket(self, interaction: Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        user = interaction.user
        cfg = await db_guilds.get(str(guild.id), {})
        ticket_cfg = cfg.get("tickets", {})

        # Check if user already has open ticket
        tickets = await db_tickets.all()
        for key, data in tickets.items():
            if data.get("user_id") == user.id and data.get("guild_id") == guild.id and \
               data.get("status") == "open":
                await interaction.followup.send(
                    embed=error_embed("You already have an open ticket! Close it first."),
                    ephemeral=True
                )
                return

        category_id = ticket_cfg.get("category")
        category = guild.get_channel(int(category_id)) if category_id else None
        support_role_id = ticket_cfg.get("support_role")
        support_role = guild.get_role(int(support_role_id)) if support_role_id else None

        ticket_num = ticket_cfg.get("ticket_count", 0) + 1
        ticket_cfg["ticket_count"] = ticket_num
        cfg["tickets"] = ticket_cfg
        await db_guilds.set(str(guild.id), cfg)

        overwrites = {
            guild.default_role: PermissionOverwrite(read_messages=False),
            guild.me: PermissionOverwrite(read_messages=True, send_messages=True, 
                                           manage_channels=True),
            user: PermissionOverwrite(read_messages=True, send_messages=True, 
                                      attach_files=True, embed_links=True)
        }
        if support_role:
            overwrites[support_role] = PermissionOverwrite(
                read_messages=True, send_messages=True, attach_files=True, embed_links=True
            )

        ticket_name = f"ticket-{ticket_num:04d}"
        try:
            channel = await guild.create_text_channel(
                name=ticket_name,
                category=category,
                overwrites=overwrites,
                reason=f"Ticket created by {user.name}"
            )
        except Exception as e:
            await interaction.followup.send(embed=error_embed(f"Failed to create ticket: {e}"), ephemeral=True)
            return

        embed = Embed(
            title="🎫 Ticket Created",
            description=(
                f"Welcome {user.mention}! Support will be with you shortly.\n\n"
                f"**Ticket:** #{ticket_num:04d}\n"
                f"**Created:** <t:{int(time.time())}:R>\n\n"
                f"Use the buttons below to manage this ticket."
            ),
            color=LYTRIX_COLOR
        )
        embed.set_footer(text="Lytrix Tickets • Made by Reon")

        await db_tickets.set(str(channel.id), {
            "guild_id": guild.id,
            "user_id": user.id,
            "channel_id": channel.id,
            "ticket_number": ticket_num,
            "status": "open",
            "claimed_by": None,
            "created_at": time.time(),
            "closed_at": None,
            "priority": "normal",
            "category": category_id,
            "messages": []
        })

        await channel.send(
            content=f"{user.mention} {support_role.mention if support_role else ''}",
            embed=embed,
            view=TicketManageView(self.bot, ticket_num)
        )
        await interaction.followup.send(
            embed=success_embed(f"Ticket created: {channel.mention}"),
            ephemeral=True
        )

    @button(label="📋 Support", style=ButtonStyle.green, custom_id="ticket_support", emoji="📋")
    async def support_info(self, interaction: Interaction, button: Button):
        embed = Embed(
            title="📋 Lytrix Support",
            description=(
                "Need help? Create a ticket and our support team will assist you!\n\n"
                "**What we help with:**\n"
                "• Bot configuration & setup\n"
                "• Bug reports & technical issues\n"
                "• Feature requests\n"
                "• Payment & premium inquiries\n"
                "• General questions\n\n"
                "Click **Create Ticket** to get started!"
            ),
            color=LYTRIX_COLOR2
        )
        embed.set_footer(text="Lytrix Support • Made by Reon")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class TicketManageView(View):
    """View for managing an open ticket."""
    def __init__(self, bot: LytrixBot, ticket_num: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.ticket_num = ticket_num

    @button(label="🔒 Close", style=ButtonStyle.red, custom_id="ticket_close", emoji="🔒")
    async def close_ticket(self, interaction: Interaction, button: Button):
        channel = interaction.channel
        ticket_data = await db_tickets.get(str(channel.id), {})
        if not ticket_data or ticket_data.get("status") != "open":
            await interaction.response.send_message(
                embed=error_embed("This ticket is already closed!"), ephemeral=True
            )
            return

        guild = interaction.guild
        cfg = await db_guilds.get(str(guild.id), {})
        ticket_cfg = cfg.get("tickets", {})

        # Save transcript
        transcript = []
        async for msg in channel.history(oldest_first=True, limit=500):
            transcript.append(f"[{msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {msg.author.name}: {msg.content}")
        ticket_data["transcript"] = transcript
        ticket_data["status"] = "closed"
        ticket_data["closed_at"] = time.time()
        ticket_data["closed_by"] = interaction.user.id
        await db_tickets.set(str(channel.id), ticket_data)

        embed = Embed(
            title="🔒 Ticket Closed",
            description=f"Ticket #{self.ticket_num:04d} has been closed by {interaction.user.mention}",
            color=0xEF4444
        )
        embed.set_footer(text="This channel will be deleted soon • Lytrix Tickets")

        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(5)

        log_channel_id = ticket_cfg.get("log_channel")
        if log_channel_id:
            log_ch = guild.get_channel(int(log_channel_id))
            if log_ch:
                transcript_text = "\n".join(transcript[-200:])
                if len(transcript_text) > 1900:
                    transcript_text = transcript_text[:1900] + "\n... (truncated)"
                log_embed = Embed(
                    title=f"📝 Ticket #{self.ticket_num:04d} Transcript",
                    description=f"```\n{transcript_text}\n```" if transcript_text else "No messages",
                    color=LYTRIX_COLOR,
                    timestamp=datetime.datetime.utcnow()
                )
                log_embed.add_field(name="Opened by", value=f"<@{ticket_data.get('user_id')}>")
                log_embed.add_field(name="Closed by", value=f"{interaction.user.mention}")
                log_embed.set_footer(text="Lytrix Ticket Logs • Made by Reon")
                try:
                    await log_ch.send(embed=log_embed)
                except:
                    pass

        try:
            await channel.delete(reason=f"Ticket closed by {interaction.user.name}")
        except:
            pass

    @button(label="✋ Claim", style=ButtonStyle.blurple, custom_id="ticket_claim", emoji="✋")
    async def claim_ticket(self, interaction: Interaction, button: Button):
        channel = interaction.channel
        ticket_data = await db_tickets.get(str(channel.id), {})
        if not ticket_data or ticket_data.get("status") != "open":
            await interaction.response.send_message(embed=error_embed("Invalid ticket!"), ephemeral=True)
            return
        if ticket_data.get("claimed_by"):
            await interaction.response.send_message(
                embed=error_embed(f"Already claimed by <@{ticket_data['claimed_by']}>!"), ephemeral=True
            )
            return

        ticket_data["claimed_by"] = interaction.user.id
        await db_tickets.set(str(channel.id), ticket_data)

        await interaction.response.send_message(
            embed=success_embed(f"Ticket claimed by {interaction.user.mention}!"),
            ephemeral=False
        )
        await channel.edit(name=f"claimed-{ticket_data['ticket_number']:04d}")

    @button(label="🔓 Reopen", style=ButtonStyle.green, custom_id="ticket_reopen", emoji="🔓")
    async def reopen_ticket(self, interaction: Interaction, button: Button):
        channel = interaction.channel
        ticket_data = await db_tickets.get(str(channel.id), {})
        if not ticket_data or ticket_data.get("status") != "closed":
            await interaction.response.send_message(embed=error_embed("Ticket is not closed!"), ephemeral=True)
            return

        ticket_data["status"] = "open"
        ticket_data["closed_at"] = None
        ticket_data["closed_by"] = None
        await db_tickets.set(str(channel.id), ticket_data)

        await interaction.response.send_message(
            embed=success_embed(f"Ticket reopened by {interaction.user.mention}!")
        )

    @button(label="⭐ Priority", style=ButtonStyle.grey, custom_id="ticket_priority", emoji="⭐")
    async def set_priority(self, interaction: Interaction, button: Button):
        channel = interaction.channel
        ticket_data = await db_tickets.get(str(channel.id), {})
        if not ticket_data:
            return

        current = ticket_data.get("priority", "normal")
        priorities = {"low": "medium", "medium": "high", "high": "urgent", "urgent": "low"}
        new_priority = priorities.get(current, "normal")
        ticket_data["priority"] = new_priority
        await db_tickets.set(str(channel.id), ticket_data)

        colors = {"low": 0x10B981, "medium": 0xF59E0B, "high": 0xF97316, "urgent": 0xEF4444}
        await interaction.response.send_message(
            embed=Embed(
                title="⭐ Priority Updated",
                description=f"Ticket priority set to **{new_priority.upper()}**",
                color=colors.get(new_priority, LYTRIX_COLOR)
            )
        )

    @button(label="➕ Add User", style=ButtonStyle.grey, custom_id="ticket_add", emoji="➕")
    async def add_user(self, interaction: Interaction, button: Button):
        modal = TicketAddModal(self.bot)
        await interaction.response.send_modal(modal)


class TicketAddModal(Modal, title="Add User to Ticket"):
    user_id = ui.TextInput(label="User ID to add", placeholder="Enter Discord user ID", style=TextStyle.short)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: Interaction):
        try:
            member = interaction.guild.get_member(int(self.user_id.value))
            if not member:
                await interaction.response.send_message(embed=error_embed("User not found!"), ephemeral=True)
                return
            channel = interaction.channel
            await channel.set_permissions(member, read_messages=True, send_messages=True)
            await interaction.response.send_message(
                embed=success_embed(f"Added {member.mention} to the ticket!"), ephemeral=False
            )
        except ValueError:
            await interaction.response.send_message(embed=error_embed("Invalid user ID!"), ephemeral=True)


class TicketManager:
    """Manages ticket operations."""
    def __init__(self, bot: LytrixBot):
        self.bot = bot

    async def save_transcript(self, channel, ticket_data):
        """Save transcript to file."""
        guild = self.bot.get_guild(ticket_data.get("guild_id", 0))
        if not guild:
            return

        cfg = await db_guilds.get(str(guild.id), {})
        ticket_cfg = cfg.get("tickets", {})
        log_channel_id = ticket_cfg.get("log_channel")
        if not log_channel_id:
            return

        log_ch = guild.get_channel(int(log_channel_id))
        if not log_ch:
            return

        transcript = []
        async for msg in channel.history(oldest_first=True, limit=1000):
            transcript.append(
                f"[{msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {msg.author.name} ({msg.author.id}): {msg.content}"
            )

        transcript_text = "\n".join(transcript)
        if len(transcript_text) > 4000:
            transcript_text = transcript_text[:3900] + "\n... (truncated for length)"

        embed = Embed(
            title=f"📝 Transcript - Ticket #{ticket_data.get('ticket_number', '??'):04d}",
            description=f"```\n{transcript_text[:4000]}\n```",
            color=LYTRIX_COLOR,
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="User", value=f"<@{ticket_data.get('user_id')}>")
        embed.add_field(name="Claimed by", value=f"<@{ticket_data.get('claimed_by')}>" if ticket_data.get('claimed_by') else "Unclaimed")
        embed.set_footer(text="Lytrix Ticket Transcript • Made by Reon")

        try:
            await log_ch.send(embed=embed)
        except:
            pass


# ============================================================
# SLASH COMMANDS
# ============================================================
class HelpSlash(app_commands.Command):
    def __init__(self):
        super().__init__(name="help", description="📚 View all Lytrix commands", callback=self.callback)

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        embed = Embed(
            title="🌌 Lytrix Bot - Help Menu",
            description=(
                "Welcome to **Lytrix** — the ultimate all-in-one Discord bot!\n"
                f"Made with ❤️ by **Reon**\n\n"
                f"**Prefix:** `!` (or your custom prefix)\n"
                f"**Total Commands:** 500+\n\n"
                f"Use `!help <category>` for detailed command lists."
            ),
            color=LYTRIX_COLOR
        )
        embed.add_field(name="🛡️ AntiNuke", value="`!help antinuke` - Server protection", inline=True)
        embed.add_field(name="🎵 Music", value="`!help music` - Crazy music system", inline=True)
        embed.add_field(name="🎫 Tickets", value="`!help tickets` - Support tickets", inline=True)
        embed.add_field(name="🛠️ Moderation", value="`!help mod` - Advanced moderation", inline=True)
        embed.add_field(name="😂 Fun", value="`!help fun` - Fun & games", inline=True)
        embed.add_field(name="💰 Economy", value="`!help economy` - Virtual economy", inline=True)
        embed.add_field(name="🔧 Utility", value="`!help utility` - Useful tools", inline=True)
        embed.add_field(name="📊 Levels", value="`!help levels` - XP & ranking", inline=True)
        embed.add_field(name="🎉 Giveaways", value="`!help giveaway` - Giveaway system", inline=True)
        embed.add_field(name="⚙️ Config", value="`!help config` - Bot configuration", inline=True)
        embed.add_field(name="📋 Info", value="`!help info` - Bot & server info", inline=True)
        embed.add_field(name="🤖 AutoMod", value="`!help automod` - Auto moderation", inline=True)
        embed.set_footer(text="Lytrix Bot • Made by Reon • 500+ Commands")
        embed.set_thumbnail(url="https://i.imgur.com/6V7sH4o.png")
        await interaction.followup.send(embed=embed)


class PingSlash(app_commands.Command):
    def __init__(self):
        super().__init__(name="ping", description="🏓 Check bot latency", callback=self.callback)

    async def callback(self, interaction: Interaction):
        start = time.perf_counter()
        await interaction.response.defer()
        end = time.perf_counter()
        ws = round(interaction.client.latency * 1000)
        rest = round((end - start) * 1000)
        embed = Embed(title="🏓 Pong!", color=LYTRIX_COLOR)
        embed.add_field(name="WebSocket", value=f"`{ws}ms`", inline=True)
        embed.add_field(name="REST API", value=f"`{rest}ms`", inline=True)
        embed.add_field(name="Shard", value=f"`#{interaction.guild.shard_id}`" if interaction.guild else "N/A", inline=True)
        await interaction.followup.send(embed=embed)


class InviteSlash(app_commands.Command):
    def __init__(self):
        super().__init__(name="invite", description="🔗 Invite Lytrix to your server", callback=self.callback)

    async def callback(self, interaction: Interaction):
        embed = Embed(
            title="🔗 Invite Lytrix",
description=(
    f"**Add Lytrix to your server!**\n\n"
    f"[Click here to invite](https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&permissions=8&scope=bot+applications.commands)\n\n"
                "**Support Server:** [Join here](https://discord.gg/lytrix)\n"
                "**Vote:** [Top.gg](https://top.gg/bot/lytrix)\n\n"
                "*You need Administrator permission to invite bots.*"
            ),
            color=LYTRIX_COLOR2
        )
        embed.set_footer(text="Lytrix • Made by Reon")
        await interaction.response.send_message(embed=embed)

# ============================================================
# ALL CORE COMMANDS COG
# ============================================================
class LytrixCommands(commands.Cog, name="Lytrix Core"):
    """All 500+ commands organized by category."""
    def __init__(self, bot: LytrixBot):
        self.bot = bot

    # ==============================================
    # HELP COMMAND
    # ==============================================
    @commands.command(name="help", aliases=["h", "cmds", "commands", "menu"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def help_cmd(self, ctx, category: str = None):
        """View all commands or help for a category."""
        prefix = await self.bot.get_prefix_str(ctx.guild)
        categories = {
            "antinuke": ("🛡️ AntiNuke Commands (Wick-Style)", [
                ("antinuke enable", "Enable the anti-nuke system"),
                ("antinuke disable", "Disable the anti-nuke system"),
                ("antinuke config", "View current anti-nuke config"),
                ("antinuke punishment <type>", "Set punishment (ban/kick/quarantine/strip)"),
                ("antinuke whitelist <user>", "Whitelist a user from anti-nuke"),
                ("antinuke unwhitelist <user>", "Remove user from whitelist"),
                ("antinuke bypass <role>", "Add bypass role"),
                ("antinuke threshold <module> <num>", "Set module threshold"),
                ("antinuke module <name> <on/off>", "Toggle specific anti-nuke modules"),
                ("antinuke logchannel <#channel>", "Set anti-nuke log channel"),
                ("antinuke lockdown", "Lockdown the entire server"),
                ("antinuke unlock", "Remove server lockdown"),
                ("antinuke raidmode", "Enable aggressive raid protection"),
                ("antinuke backup", "Create a server backup for recovery"),
                ("antinuke recover", "Recover server from backup"),
                ("antinuke info", "View anti-nuke status"),
                ("antinuke dmalert <on/off>", "Toggle DM alerts for punished users"),
                ("antinuke antibot <on/off>", "Toggle anti-bot-add protection"),
                ("antinuke antispam <on/off>", "Toggle anti-spam protection"),
                ("antinuke massban <on/off>", "Toggle anti-mass-ban"),
                ("antinuke masskick <on/off>", "Toggle anti-mass-kick"),
                ("antinuke masschannel <on/off>", "Toggle anti-mass-channel"),
                ("antinuke massrole <on/off>", "Toggle anti-mass-role"),
                ("antinuke everyone <on/off>", "Toggle anti-@everyone/@here"),
                ("antinuke webhook <on/off>", "Toggle anti-webhook protection"),
                ("antinuke emoji <on/off>", "Toggle anti-emoji protection"),
                ("antinuke thread <on/off>", "Toggle anti-thread protection"),
                ("antinuke sticker <on/off>", "Toggle anti-sticker protection"),
                ("antinuke event <on/off>", "Toggle anti-event protection"),
                ("antinuke integration <on/off>", "Toggle anti-integration protection"),
                ("antinuke reset", "Reset anti-nuke configuration"),
                ("antinuke export", "Export anti-nuke config"),
                ("antinuke import", "Import anti-nuke config"),
                ("antinuke test", "Test if anti-nuke is working"),
            ]),
            "music": ("🎵 Music Commands (Crazy Style)", [
                ("play <query>", "Play a song from YouTube/Spotify/SoundCloud"),
                ("search <query>", "Search for a song and choose from results"),
                ("skip", "Skip the current song (with vote system)"),
                ("forceskip", "Force skip (DJ only)"),
                ("stop", "Stop music and clear queue"),
                ("pause", "Pause playback"),
                ("resume", "Resume playback"),
                ("queue", "Show the music queue"),
                ("clearqueue", "Clear the music queue"),
                ("shuffle", "Shuffle the queue"),
                ("loop <off/track/queue>", "Set loop mode"),
                ("volume <1-200>", "Set volume"),
                ("nowplaying", "Show now playing info"),
                ("lyrics <song>", "Get lyrics for current or specified song"),
                ("bassboost <0-100>", "Bass boost filter"),
                ("nightcore", "Toggle nightcore filter"),
                ("vaporwave", "Toggle vaporwave filter"),
                ("karaoke", "Toggle karaoke filter"),
                ("chipmunk", "Toggle chipmunk filter"),
                ("daycore", "Toggle daycore filter"),
                ("earrape", "Toggle earrape mode (careful!)"),
                ("lofi", "Toggle lofi filter"),
                ("speed <rate>", "Set playback speed"),
                ("tremolo <0-100>", "Set tremolo effect"),
                ("vibrato <0-100>", "Set vibrato effect"),
                ("distortion <0-100>", "Set distortion effect"),
                ("echo <0-100>", "Set echo effect"),
                ("reverb", "Toggle reverb filter"),
                ("resetfilters", "Reset all audio filters"),
                ("filters", "Show current filter settings"),
                ("247", "Toggle 24/7 mode"),
                ("join", "Join your voice channel"),
                ("leave", "Leave voice channel"),
                ("move <#channel>", "Move bot to another voice channel"),
                ("seek <seconds>", "Seek to a position"),
                ("rewind <seconds>", "Rewind"),
                ("forward <seconds>", "Fast forward"),
                ("replay", "Replay current song"),
                ("remove <index>", "Remove song from queue"),
                ("jump <index>", "Jump to song in queue"),
                ("skipto <index>", "Skip to specific song"),
                ("playnext <query>", "Add song to front of queue"),
                ("playnow <query>", "Play song immediately"),
                ("grab", "Save current song to your DMs"),
                ("save <name>", "Save current queue as playlist"),
                ("load <name>", "Load a saved playlist"),
                ("playlists", "View your saved playlists"),
                ("history", "View recently played songs"),
                ("stats", "View music stats"),
                ("djrole <role>", "Set DJ role"),
                ("removedj <role>", "Remove DJ role"),
            ]),
            "tickets": ("🎫 Ticket Commands (R.O.T.I Style)", [
                ("ticket setup", "Setup the ticket system"),
                ("ticket panel <#channel>", "Send the ticket panel"),
                ("ticket category <category>", "Set ticket category"),
                ("ticket role <role>", "Set support role"),
                ("ticket log <#channel>", "Set ticket log channel"),
                ("ticket close", "Close the current ticket"),
                ("ticket delete", "Force delete a ticket"),
                ("ticket add <user>", "Add user to ticket"),
                ("ticket remove <user>", "Remove user from ticket"),
                ("ticket rename <name>", "Rename ticket channel"),
                ("ticket claim", "Claim a ticket"),
                ("ticket unclaim", "Unclaim a ticket"),
                ("ticket priority <level>", "Set ticket priority"),
                ("ticket reopen", "Reopen a closed ticket"),
                ("ticket transcript", "Save ticket transcript"),
                ("ticket info", "View ticket information"),
                ("ticket list", "List all tickets"),
                ("ticket mytickets", "View your tickets"),
                ("ticket stats", "View ticket statistics"),
                ("ticket limit <num>", "Set max tickets per user"),
                ("ticket message <text>", "Set ticket opening message"),
                ("ticket name <prefix>", "Set ticket name prefix"),
                ("ticket autorename", "Toggle auto-rename on claim"),
                ("ticket autoclose <hours>", "Set auto-close time"),
                ("ticket ping <role>", "Set ping role"),
                ("ticket modal", "Toggle modal-based creation"),
                ("ticket embed", "Set custom ticket embed"),
                ("ticket disable", "Disable ticket system"),
                ("ticket enable", "Enable ticket system"),
            ]),
            "mod": ("🛠️ Moderation Commands (Carl-Style)", [
                ("ban <user> [reason]", "Ban a member"),
                ("unban <user> [reason]", "Unban a user"),
                ("kick <user> [reason]", "Kick a member"),
                ("mute <user> <duration> [reason]", "Mute a member"),
                ("unmute <user>", "Unmute a member"),
                ("tempmute <user> <duration> [reason]", "Temporarily mute"),
                ("tempban <user> <duration> [reason]", "Temporarily ban"),
                ("softban <user> [reason]", "Ban & unban to delete messages"),
                ("warn <user> [reason]", "Warn a member"),
                ("warnings <user>", "View member warnings"),
                ("clearwarns <user>", "Clear all warnings"),
                ("delwarn <warn_id>", "Delete specific warning"),
                ("purge <amount>", "Purge messages"),
                ("purgeuser <user> <amount>", "Purge user messages"),
                ("purgebot <amount>", "Purge bot messages"),
                ("purgecontains <text> <amount>", "Purge messages containing text"),
                ("purgeattachments <amount>", "Purge messages with attachments"),
                ("purgeembeds <amount>", "Purge messages with embeds"),
                ("purgebetween <msg_id> <msg_id>", "Purge between messages"),
                ("slowmode <seconds>", "Set channel slowmode"),
                ("lock", "Lock the channel"),
                ("unlock", "Unlock the channel"),
                ("lockall", "Lock all channels"),
                ("unlockall", "Unlock all channels"),
                ("hide", "Hide channel from members"),
                ("unhide", "Unhide channel"),
                ("nuke", "Clone and recreate channel"),
                ("clone <name>", "Clone current channel"),
                ("role <user> <role>", "Add/remove role"),
                ("addrole <user> <role>", "Add role to member"),
                ("removerole <user> <role>", "Remove role from member"),
                ("temprole <user> <role> <duration>", "Temporary role"),
                ("nick <user> <nickname>", "Change nickname"),
                ("massnick <prefix>", "Mass nickname all members"),
                ("deafen <user>", "Server deafen a member"),
                ("undeafen <user>", "Server undeafen"),
                ("vmute <user>", "Voice mute"),
                ("vunmute <user>", "Voice unmute"),
                ("disconnect <user>", "Disconnect from VC"),
                ("vkick <user>", "Kick from voice"),
                ("moveall <channel>", "Move all to voice channel"),
                ("timeout <user> <duration>", "Timeout a member"),
                ("untimeout <user>", "Remove timeout"),
                ("case <case_id>", "View a case"),
                ("cases <user>", "View all cases for a user"),
                ("reason <case_id> <reason>", "Update case reason"),
                ("note <user> <text>", "Add a note to a user"),
                ("notes <user>", "View user notes"),
                ("clearnotes <user>", "Clear user notes"),
                ("snap <amount>", "Quick purge"),
                ("cleanup <amount>", "Clean bot messages"),
                ("slowmode off", "Disable slowmode"),
                ("lock category <category>", "Lock all channels in category"),
                ("unlock category <category>", "Unlock all channels in category"),
            ]),
            "fun": ("😂 Fun Commands", [
                ("meme", "Random meme"),
                ("joke", "Random joke"),
                ("roast <user>", "Roast someone"),
                ("hug <user>", "Hug someone"),
                ("kiss <user>", "Kiss someone"),
                ("slap <user>", "Slap someone"),
                ("pat <user>", "Pat someone"),
                ("cuddle <user>", "Cuddle someone"),
                ("ship <user1> <user2>", "Ship two users"),
                ("howgay <user>", "How gay is someone?"),
                ("simp <user>", "Simp rate"),
                ("coolrate <user>", "Coolness rating"),
                ("iq <user>", "IQ test"),
                ("pp <user>", "PP size (for fun)"),
                ("8ball <question>", "Ask the magic 8-ball"),
                ("coinflip", "Flip a coin"),
                ("roll <num>", "Roll dice"),
                ("choose <opt1,opt2,...>", "Choose between options"),
                ("rps <rock/paper/scissors>", "Rock Paper Scissors"),
                ("trivia", "Trivia question"),
                ("wouldyourather", "Would you rather question"),
                ("truth", "Truth question"),
                ("dare", "Dare challenge"),
                ("topic", "Conversation topic"),
                ("fact", "Random fact"),
                ("quote", "Inspirational quote"),
                ("ascii <text>", "Convert text to ASCII art"),
                ("reverse <text>", "Reverse text"),
                ("mock <text>", "Mocking text"),
                ("clap <text>", "👏 Clap 👏 text"),
                ("fancy <text>", "Fancy text"),
                ("owo <text>", "OwO-ify text"),
                ("say <text>", "Make the bot say something"),
                ("embed <json/text>", "Create a custom embed"),
                ("poll <question> | <options>", "Create a poll"),
                ("gt <duration> <winners> <prize>", "Start giveaway (alias: giveaway)"),
                ("reroll <message_id>", "Reroll giveaway"),
                ("endgiveaway <message_id>", "End giveaway early"),
                ("snipe", "Snipe last deleted message"),
                ("editsnipe", "Snipe last edited message"),
                ("reactionsnipe", "Snipe last removed reaction"),
                ("firstmsg", "Get first message in channel"),
                ("randomuser", "Pick a random member"),
                ("avatar <user>", "Show user avatar"),
                ("banner <user>", "Show user banner"),
                ("emoji <emoji>", "Show emoji info"),
                ("enlarge <emoji>", "Enlarge an emoji"),
                ("steal <emoji>", "Steal emoji to server"),
                ("color <hex>", "Show a color"),
                ("timer <seconds>", "Start a timer"),
                ("stopwatch", "Start a stopwatch"),
                ("countdown <seconds>", "Start a countdown"),
                ("remind <time> <message>", "Set a reminder"),
            ]),
            "economy": ("💰 Economy Commands", [
                ("balance", "Check your balance"),
                ("daily", "Daily reward"),
                ("weekly", "Weekly reward"),
                ("monthly", "Monthly reward"),
                ("work", "Work for money"),
                ("beg", "Beg for coins"),
                ("rob <user>", "Rob someone"),
                ("crime", "Commit a crime"),
                ("slut", "Earn coins the risky way"),
                ("gamble <amount>", "Gamble coins"),
                ("slots <amount>", "Slot machine"),
                ("blackjack <amount>", "Play blackjack"),
                ("roulette <amount> <color/number>", "Play roulette"),
                ("coinflip <amount> <heads/tails>", "Bet on coin flip"),
                ("bet <amount>", "Place a bet"),
                ("deposit <amount>", "Deposit to bank"),
                ("withdraw <amount>", "Withdraw from bank"),
                ("give <user> <amount>", "Give coins to user"),
                ("pay <user> <amount>", "Pay a user"),
                ("shop", "View item shop"),
                ("buy <item>", "Buy an item"),
                ("sell <item>", "Sell an item"),
                ("inventory", "View your inventory"),
                ("use <item>", "Use an item"),
                ("fish", "Go fishing"),
                ("hunt", "Go hunting"),
                ("dig", "Dig for treasure"),
                ("mine", "Go mining"),
                ("chop", "Chop trees"),
                ("farm", "Farm resources"),
                ("quest", "Get daily quest"),
                ("quests", "View active quests"),
                ("richlist", "Server wealth leaderboard"),
                ("richest", "Global wealth leaderboard"),
                ("setbal <user> <amount>", "Set user balance (admin)"),
                ("addbal <user> <amount>", "Add to balance (admin)"),
                ("rembal <user> <amount>", "Remove from balance (admin)"),
            ]),
            "utility": ("🔧 Utility Commands", [
                ("userinfo <user>", "View detailed user info"),
                ("serverinfo", "View server information"),
                ("roleinfo <role>", "View role info"),
                ("channelinfo <channel>", "View channel info"),
                ("emojiinfo <emoji>", "View emoji info"),
                ("botinfo", "View bot information"),
                ("ping", "Check bot latency"),
                ("uptime", "Bot uptime"),
                ("avatar <user>", "View user avatar"),
                ("servericon", "View server icon"),
                ("serverbanner", "View server banner"),
                ("emojis", "List server emojis"),
                ("roles", "List server roles"),
                ("inrole <role>", "Members with a role"),
                ("members", "Server member count"),
                ("joined <user>", "When a user joined"),
                ("oldest", "Oldest member"),
                ("newest", "Newest member"),
                ("boosters", "Server boosters"),
                ("boosts", "Boost count"),
                ("calc <expression>", "Calculate math expression"),
                ("weather <city>", "Get weather info"),
                ("translate <lang> <text>", "Translate text"),
                ("define <word>", "Define a word"),
                ("urban <word>", "Urban dictionary"),
                ("wiki <query>", "Search Wikipedia"),
                ("qr <text>", "Generate QR code"),
                ("invite", "Bot invite link"),
                ("support", "Support server link"),
                ("vote", "Vote for Lytrix"),
                ("donate", "Donation info"),
                ("afk <reason>", "Set AFK status"),
                ("setprefix <prefix>", "Change bot prefix"),
                ("setlanguage <lang>", "Set bot language"),
            ]),
            "levels": ("📊 Leveling Commands", [
                ("rank <user>", "View rank card"),
                ("leaderboard", "Server XP leaderboard"),
                ("setlevel <user> <level>", "Set user level (admin)"),
                ("setxp <user> <xp>", "Set user XP (admin)"),
                ("levelup <on/off>", "Toggle level-up messages"),
                ("levelchannel <#channel>", "Set level-up channel"),
                ("levelrole <level> <role>", "Add level reward role"),
                ("remlevelrole <level>", "Remove level reward"),
                ("levelroles", "View level rewards"),
                ("levelreset <user>", "Reset user level"),
                ("xprate <multiplier>", "Set XP multiplier"),
            ]),
            "automod": ("🤖 AutoMod Commands", [
                ("automod enable", "Enable automod"),
                ("automod disable", "Disable automod"),
                ("automod antispam <on/off>", "Toggle anti-spam"),
                ("automod antilinks <on/off>", "Toggle anti-links"),
                ("automod antiinvite <on/off>", "Toggle anti-invite"),
                ("automod antizalgo <on/off>", "Toggle anti-zalgo"),
                ("automod anticaps <on/off>", "Toggle anti-caps"),
                ("automod antighostping <on/off>", "Toggle anti-ghostping"),
                ("automod antimassmention <on/off>", "Toggle anti mass mention"),
                ("automod antiphishing <on/off>", "Toggle anti-phishing"),
                ("automod antinsfw <on/off>", "Toggle anti-NSFW"),
                ("automod badwords <add/remove/list> <word>", "Manage bad words"),
                ("automod ignores <add/remove> <#channel/role>", "Manage ignored channels/roles"),
                ("automod whitelist <user>", "Whitelist user from automod"),
                ("automod punishment <type>", "Set auto punishment"),
                ("automod log <#channel>", "Set automod log channel"),
            ]),
            "welcome": ("👋 Welcome & Leave Commands", [
                ("welcome channel <#channel>", "Set welcome channel"),
                ("welcome message <text>", "Set welcome message"),
                ("welcome embed <on/off>", "Toggle embed welcome"),
                ("welcome dm <on/off>", "Toggle DM welcome"),
                ("welcome role <role>", "Set auto-role"),
                ("welcome test", "Test welcome message"),
                ("leave channel <#channel>", "Set leave channel"),
                ("leave message <text>", "Set leave message"),
                ("autorole <role>", "Set auto-role on join"),
                ("removeautorole", "Remove auto-role"),
                ("membercount <#channel>", "Set member count channel"),
            ]),
            "reactionroles": ("🎭 Reaction Role Commands", [
                ("rr add <#channel> <msg_id> <emoji> <role>", "Add reaction role"),
                ("rr remove <msg_id> <emoji>", "Remove reaction role"),
                ("rr list", "List all reaction roles"),
                ("rr panel <#channel> <title>", "Create reaction role panel"),
                ("rr clear <msg_id>", "Clear all reactions from message"),
            ]),
        }

        if category and category.lower() in categories:
            title, cmds = categories[category.lower()]
            embed = Embed(title=title, color=LYTRIX_COLOR)
            chunk_size = 25
            for i in range(0, len(cmds), chunk_size):
                chunk = cmds[i:i+chunk_size]
                embed.add_field(
                    name=f"Commands ({i+1}-{min(i+chunk_size, len(cmds))})",
                    value="\n".join(f"`{prefix}{cmd}` — {desc}" for cmd, desc in chunk),
                    inline=False
                )
            embed.set_footer(text=f"Lytrix • Made by Reon • Category: {category.title()}")
        else:
            embed = Embed(
                title="🌌 Lytrix Bot - Complete Command List",
                description=f"**Prefix:** `{prefix}` | **500+ Commands**\nReact with emojis or use `{prefix}help <category>`",
                color=LYTRIX_COLOR
            )
            cat_emojis = {
                "🛡️ AntiNuke": "antinuke", "🎵 Music": "music", "🎫 Tickets": "tickets",
                "🛠️ Moderation": "mod", "😂 Fun": "fun", "💰 Economy": "economy",
                "🔧 Utility": "utility", "📊 Levels": "levels", "🤖 AutoMod": "automod",
                "👋 Welcome": "welcome", "🎭 Reactions": "reactionroles"
            }
            embed.add_field(name="Categories", value="\n".join(cat_emojis.keys()), inline=False)
            embed.set_footer(text="Lytrix • Made by Reon • Use !help <category> for details")

        await ctx.send(embed=embed, mention_author=False)

    # ==============================================
    # INFO COMMANDS
    # ==============================================
    @commands.command(name="ping", aliases=["latency"])
    async def ping_cmd(self, ctx):
        """Check bot latency."""
        start = time.perf_counter()
        msg = await ctx.send(embed=make_embed(description="🏓 Pinging..."))
        end = time.perf_counter()
        rest = round((end - start) * 1000)
        ws = round(self.bot.latency * 1000)
        db_start = time.perf_counter()
        await db_config.read()
        db_time = round((time.perf_counter() - db_start) * 1000)

        embed = Embed(title="🏓 Pong!", color=LYTRIX_COLOR)
        embed.add_field(name="WebSocket", value=f"`{ws}ms`", inline=True)
        embed.add_field(name="REST API", value=f"`{rest}ms`", inline=True)
        embed.add_field(name="Database", value=f"`{db_time}ms`", inline=True)
        embed.add_field(name="Uptime", value=format_time(time.time() - self.bot.start_time), inline=True)
        embed.add_field(name="Shard", value=f"`#{ctx.guild.shard_id}`", inline=True)
        embed.add_field(name="Guilds", value=f"`{len(self.bot.guilds)}`", inline=True)
        await msg.edit(embed=embed)

    @commands.command(name="botinfo", aliases=["bi", "about", "info"])
    async def botinfo_cmd(self, ctx):
        """View bot information."""
        uptime = format_time(time.time() - self.bot.start_time)
        embed = Embed(
            title="🌌 Lytrix Bot Information",
            description="*The Ultimate All-in-One Discord Bot*",
            color=LYTRIX_COLOR
        )
        embed.add_field(name="📛 Name", value=self.bot.user.name, inline=True)
        embed.add_field(name="🆔 ID", value=str(self.bot.user.id), inline=True)
        embed.add_field(name="👑 Creator", value="Reon", inline=True)
        embed.add_field(name="⏰ Uptime", value=uptime, inline=True)
        embed.add_field(name="🌍 Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="👥 Users", value=str(sum(g.member_count for g in self.bot.guilds)), inline=True)
        embed.add_field(name="📋 Commands", value="500+", inline=True)
        embed.add_field(name="🏓 Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="📚 Library", value=f"discord.py {discord.__version__}", inline=True)
        embed.add_field(name="🔢 Shards", value=str(self.bot.shard_count or 1), inline=True)
        embed.add_field(name="💾 RAM Usage", value=f"{sys.getsizeof(self.bot)} bytes", inline=True)
        embed.add_field(name="🎵 Players", value=str(len(self.bot._voice_clients)), inline=True)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Made with ❤️ by Reon")
        await ctx.send(embed=embed)

    @commands.command(name="uptime", aliases=["up"])
    async def uptime_cmd(self, ctx):
        """Bot uptime."""
        uptime_seconds = time.time() - self.bot.start_time
        await ctx.send(embed=make_embed(
            title="⏰ Lytrix Uptime",
            description=f"```\n{format_time(uptime_seconds)}\n```\nStarted: <t:{int(self.bot.start_time)}:R>",
            color=LYTRIX_COLOR
        ))

    @commands.command(name="invite", aliases=["inv"])
    async def invite_cmd(self, ctx):
        """Get bot invite link."""
        embed = Embed(
            title="🔗 Invite Lytrix",
            description=(
                "**Add the ultimate bot to your server!**\n\n"
                f"[🔗 Invite Lytrix](https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&permissions=8&scope=bot+applications.commands)\n"
                "[💬 Support Server](https://discord.gg/lytrix)\n"
                "[📊 Vote on Top.gg](https://top.gg/bot/lytrix)\n\n"
                "*Requires Administrator permission*"
            ),
            color=LYTRIX_COLOR2
        )
        await ctx.send(embed=embed)

    @commands.command(name="support")
    async def support_cmd(self, ctx):
        """Support server info."""
        await ctx.send(embed=make_embed(
            title="💬 Lytrix Support",
            description="[Join Support Server](https://discord.gg/lytrix)\n\nNeed help? Our team is ready!",
            color=LYTRIX_COLOR
        ))

    @commands.command(name="vote")
    async def vote_cmd(self, ctx):
        """Vote for Lytrix."""
        await ctx.send(embed=make_embed(
            title="🗳️ Vote for Lytrix",
            description="[Vote on Top.gg](https://top.gg/bot/lytrix/vote)\nVoting helps us grow!",
            color=LYTRIX_COLOR
        ))

    # ==============================================
    # USER INFO COMMANDS
    # ==============================================
    @commands.command(name="userinfo", aliases=["ui", "whois", "user"])
    async def userinfo_cmd(self, ctx, *, member: discord.Member = None):
        """Get detailed information about a user."""
        member = member or ctx.author
        roles = [r.mention for r in reversed(member.roles) if r != ctx.guild.default_role]
        perms = [p.replace('_', ' ').title() for p, v in member.guild_permissions if v]

        embed = Embed(title=f"👤 {member.name}", color=member.top_role.color or LYTRIX_COLOR)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="🆔 ID", value=member.id, inline=True)
        embed.add_field(name="📅 Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="📥 Joined", value=f"<t:{int(member.joined_at.timestamp())}:R>" if member.joined_at else "N/A", inline=True)
        embed.add_field(name="🎭 Top Role", value=member.top_role.mention, inline=True)
        embed.add_field(name="🎨 Color", value=f"#{member.top_role.color.value:06X}" if member.top_role.color.value else "Default", inline=True)
        embed.add_field(name="🤖 Bot", value="Yes" if member.bot else "No", inline=True)
        embed.add_field(name="👑 Owner", value="Yes" if member.id == ctx.guild.owner_id else "No", inline=True)
        embed.add_field(name="⏰ Timeout", value="Yes" if member.timed_out else "No", inline=True)
        if roles:
            embed.add_field(name=f"🏷️ Roles [{len(roles)}]", value=" ".join(roles[:20]) + ("..." if len(roles) > 20 else ""), inline=False)
        embed.add_field(name="🔑 Key Permissions", value=", ".join(perms[:15]) + ("..." if len(perms) > 15 else "") or "None", inline=False)
        if member.banner:
            embed.set_image(url=member.banner.url)
        embed.set_footer(text=f"Requested by {ctx.author.name} • Lytrix")
        await ctx.send(embed=embed)

    @commands.command(name="serverinfo", aliases=["si", "guild", "server"])
    async def serverinfo_cmd(self, ctx):
        """View server information."""
        guild = ctx.guild
        total_members = guild.member_count
        humans = sum(1 for m in guild.members if not m.bot)
        bots = total_members - humans
        online = sum(1 for m in guild.members if m.status != discord.Status.offline)
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        roles_count = len(guild.roles)
        emojis_count = len(guild.emojis)
        stickers_count = len(guild.stickers)
        boost_level = guild.premium_tier
        boost_count = guild.premium_subscription_count

        embed = Embed(title=f"📊 {guild.name}", color=LYTRIX_COLOR)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="🆔 Server ID", value=guild.id, inline=True)
        embed.add_field(name="👑 Owner", value=f"<@{guild.owner_id}>", inline=True)
        embed.add_field(name="📅 Created", value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="👥 Members", value=f"{total_members} ({humans} humans, {bots} bots)", inline=True)
        embed.add_field(name="🟢 Online", value=str(online), inline=True)
        embed.add_field(name="💬 Channels", value=f"{text_channels} text | {voice_channels} voice | {categories} cats", inline=True)
        embed.add_field(name="🎭 Roles", value=str(roles_count), inline=True)
        embed.add_field(name="😀 Emojis", value=f"{emojis_count}/{guild.emoji_limit}", inline=True)
        embed.add_field(name="🏷️ Stickers", value=f"{stickers_count}/{guild.sticker_limit}", inline=True)
        embed.add_field(name="🚀 Boosts", value=f"Level {boost_level} ({boost_count} boosts)", inline=True)
        embed.add_field(name="🔒 Verification", value=str(guild.verification_level).title(), inline=True)
        embed.add_field(name="📢 Notifications", value=str(guild.default_notifications).replace('_', ' ').title(), inline=True)
        embed.add_field(name="🌍 Locale", value=str(guild.preferred_locale), inline=True)
        embed.add_field(name="🔞 NSFW", value=str(guild.nsfw_level).title(), inline=True)
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        embed.set_footer(text=f"Requested by {ctx.author.name} • Lytrix")
        await ctx.send(embed=embed)

    @commands.command(name="roleinfo", aliases=["ri", "role"])
    async def roleinfo_cmd(self, ctx, *, role: discord.Role):
        """View role information."""
        embed = Embed(title=f"🎭 {role.name}", color=role.color if role.color.value else LYTRIX_COLOR)
        embed.add_field(name="🆔 Role ID", value=role.id, inline=True)
        embed.add_field(name="🎨 Color", value=f"#{role.color.value:06X}" if role.color.value else "Default", inline=True)
        embed.add_field(name="📅 Created", value=f"<t:{int(role.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="📊 Position", value=f"{role.position} / {len(ctx.guild.roles)}", inline=True)
        embed.add_field(name="👥 Members", value=str(len(role.members)), inline=True)
        embed.add_field(name="📌 Mentionable", value="Yes" if role.mentionable else "No", inline=True)
        embed.add_field(name="🤖 Managed", value="Yes" if role.managed else "No", inline=True)
        embed.add_field(name="🔒 Hoisted", value="Yes" if role.hoist else "No", inline=True)
        perms = [p.replace('_', ' ').title() for p, v in role.permissions if v]
        embed.add_field(name="🔑 Permissions", value=", ".join(perms[:20]) + ("..." if len(perms) > 20 else "") or "None", inline=False)
        embed.set_footer(text=f"Requested by {ctx.author.name} • Lytrix")
        await ctx.send(embed=embed)

    @commands.command(name="channelinfo", aliases=["ci", "channel"])
    async def channelinfo_cmd(self, ctx, *, channel: discord.TextChannel = None):
        """View channel info."""
        channel = channel or ctx.channel
        embed = Embed(title=f"💬 #{channel.name}", color=LYTRIX_COLOR)
        embed.add_field(name="🆔 ID", value=channel.id, inline=True)
        embed.add_field(name="📅 Created", value=f"<t:{int(channel.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="📂 Category", value=channel.category.name if channel.category else "None", inline=True)
        embed.add_field(name="📊 Position", value=str(channel.position), inline=True)
        embed.add_field(name="⏱️ Slowmode", value=f"{channel.slowmode_delay}s", inline=True)
        embed.add_field(name="🔞 NSFW", value="Yes" if channel.nsfw else "No", inline=True)
        embed.add_field(name="📌 Topic", value=channel.topic or "None", inline=False)
        embed.set_footer(text=f"Requested by {ctx.author.name} • Lytrix")
        await ctx.send(embed=embed)

    @commands.command(name="avatar", aliases=["av", "pfp"])
    async def avatar_cmd(self, ctx, *, member: discord.Member = None):
        """View user avatar."""
        member = member or ctx.author
        embed = Embed(title=f"🖼️ {member.name}'s Avatar", color=LYTRIX_COLOR)
        embed.set_image(url=member.display_avatar.url)
        embed.add_field(name="Formats", value="PNG | JPG | WEBP | GIF" if member.display_avatar.is_animated() else "PNG | JPG | WEBP", inline=False)
        embed.add_field(name="Download", value=f"[Link]({member.display_avatar.url})", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="banner")
    async def banner_cmd(self, ctx, *, member: discord.Member = None):
        """View user banner."""
        member = member or ctx.author
        user = await self.bot.fetch_user(member.id)
        if user.banner:
            embed = Embed(title=f"🎨 {member.name}'s Banner", color=LYTRIX_COLOR)
            embed.set_image(url=user.banner.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=error_embed("This user has no banner!"))

    @commands.command(name="servericon", aliases=["icon", "guildicon"])
    async def servericon_cmd(self, ctx):
        """View server icon."""
        if ctx.guild.icon:
            embed = Embed(title=f"🖼️ {ctx.guild.name} Icon", color=LYTRIX_COLOR)
            embed.set_image(url=ctx.guild.icon.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=error_embed("This server has no icon!"))

    @commands.command(name="serverbanner")
    async def serverbanner_cmd(self, ctx):
        """View server banner."""
        if ctx.guild.banner:
            embed = Embed(title=f"🎨 {ctx.guild.name} Banner", color=LYTRIX_COLOR)
            embed.set_image(url=ctx.guild.banner.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=error_embed("This server has no banner!"))

    @commands.command(name="splash")
    async def splash_cmd(self, ctx):
        """View server invite splash."""
        if ctx.guild.splash:
            embed = Embed(title=f"🌊 {ctx.guild.name} Splash", color=LYTRIX_COLOR)
            embed.set_image(url=ctx.guild.splash.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=error_embed("This server has no invite splash!"))

    # ==============================================
    # MODERATION COMMANDS
    # ==============================================
    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban_cmd(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Ban a member."""
        if not await check_hierarchy(ctx, member):
            return
        dm_embed = Embed(title="🔨 Banned", description=f"You were banned from **{ctx.guild.name}**\nReason: {reason}", color=0xEF4444)
        dm_embed.set_footer(text="Lytrix Moderation • Made by Reon")
        try:
            await member.send(embed=dm_embed)
        except:
            pass
        await member.ban(reason=f"{ctx.author}: {reason}", delete_message_days=1)
        await self._log_case(ctx, "ban", member, reason)
        await ctx.send(embed=success_embed(f"🔨 **{member.name}** has been banned!\nReason: {reason}"))

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban_cmd(self, ctx, *, user_input: str):
        """Unban a user by ID or name#discrim."""
        try:
            user_id = int(user_input)
            user = await self.bot.fetch_user(user_id)
        except:
            bans = [entry async for entry in ctx.guild.bans()]
            match = discord.utils.find(lambda e: e.user.name.lower().startswith(user_input.lower()) or 
                                        (e.user.discriminator and f"{e.user.name}#{e.user.discriminator}".lower() == user_input.lower()), bans)
            if match:
                user = match.user
            else:
                await ctx.send(embed=error_embed("User not found in ban list!"))
                return
        await ctx.guild.unban(user, reason=f"Unbanned by {ctx.author}")
        await ctx.send(embed=success_embed(f"✅ **{user.name}** has been unbanned!"))

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick_cmd(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kick a member."""
        if not await check_hierarchy(ctx, member):
            return
        await member.kick(reason=f"{ctx.author}: {reason}")
        await self._log_case(ctx, "kick", member, reason)
        await ctx.send(embed=success_embed(f"👢 **{member.name}** has been kicked!\nReason: {reason}"))

    @commands.command(name="softban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def softban_cmd(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Ban then unban to delete messages."""
        if not await check_hierarchy(ctx, member):
            return
        await member.ban(reason=f"Softban by {ctx.author}: {reason}", delete_message_days=7)
        await ctx.guild.unban(member, reason=f"Softban complete: {reason}")
        await ctx.send(embed=success_embed(f"🔨 Softbanned **{member.name}**! Messages cleared.\nReason: {reason}"))

    @commands.command(name="mute", aliases=["timeout"])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def mute_cmd(self, ctx, member: discord.Member, duration: str = "1h", *, reason: str = "No reason"):
        """Mute/timeout a member. Duration: 10m, 2h, 1d, etc."""
        if not await check_hierarchy(ctx, member):
            return
        seconds = self._parse_duration(duration)
        if seconds == 0:
            await ctx.send(embed=error_embed("Invalid duration! Use: 10m, 2h, 1d, etc."))
            return
        try:
            await member.timeout(timedelta(seconds=seconds), reason=f"{ctx.author}: {reason}")
        except:
            mute_role = await get_mute_role(ctx.guild)
            if not mute_role:
                await ctx.send(embed=error_embed("Failed to create mute role. Check my permissions!"))
                return
            await member.add_roles(mute_role, reason=f"{ctx.author}: {reason}")
            await db_mutes.set(f"{ctx.guild.id}:{member.id}", {
                "guild_id": ctx.guild.id, "user_id": member.id,
                "role_id": mute_role.id, "expires_at": time.time() + seconds
            })

        dur_str = format_time(seconds)
        await self._log_case(ctx, "mute", member, f"{reason} ({dur_str})")
        await ctx.send(embed=success_embed(f"🤐 **{member.name}** muted for {dur_str}\nReason: {reason}"))

    @commands.command(name="unmute", aliases=["untimeout"])
    @commands.has_permissions(moderate_members=True)
    async def unmute_cmd(self, ctx, *, member: discord.Member):
        """Unmute a member."""
        try:
            await member.timeout(None, reason=f"Unmuted by {ctx.author}")
        except:
            mute_role = discord.utils.get(ctx.guild.roles, name="Lytrix-Muted")
            if mute_role and mute_role in member.roles:
                await member.remove_roles(mute_role, reason=f"Unmuted by {ctx.author}")
                await db_mutes.delete(f"{ctx.guild.id}:{member.id}")
            else:
                await ctx.send(embed=error_embed("This member is not muted!"))
                return
        await ctx.send(embed=success_embed(f"🔊 **{member.name}** has been unmuted!"))

    @commands.command(name="warn")
    @commands.has_permissions(moderate_members=True)
    async def warn_cmd(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Warn a member."""
        if not await check_hierarchy(ctx, member):
            return
        warns = await db_warns.get(f"{ctx.guild.id}:{member.id}", {"warns": []})
        warn_id = len(warns["warns"]) + 1
        warns["warns"].append({
            "id": warn_id, "reason": reason, "moderator": ctx.author.id,
            "time": time.time(), "timestamp": str(datetime.datetime.utcnow())
        })
        await db_warns.set(f"{ctx.guild.id}:{member.id}", warns)
        await self._log_case(ctx, "warn", member, reason)

        embed = Embed(title="⚠️ Warning Issued", color=0xF59E0B)
        embed.add_field(name="User", value=f"{member.mention} ({member.id})", inline=True)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.add_field(name="Warn #", value=str(warn_id), inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text="Lytrix Moderation • Made by Reon")

        # Auto punishment
        cfg = await db_guilds.get(str(ctx.guild.id), {})
        auto_punish = cfg.get("auto_warn_punish", {})
        warn_count = len(warns["warns"])
        if str(warn_count) in auto_punish:
            action = auto_punish[str(warn_count)]
            if action == "mute":
                try:
                    await member.timeout(timedelta(hours=1), reason=f"Auto-mute after {warn_count} warnings")
                except:
                    pass
            elif action == "kick":
                try:
                    await member.kick(reason=f"Auto-kick after {warn_count} warnings")
                except:
                    pass
            elif action == "ban":
                try:
                    await member.ban(reason=f"Auto-ban after {warn_count} warnings", delete_message_days=1)
                except:
                    pass

        await ctx.send(embed=embed)

    @commands.command(name="warnings", aliases=["warns"])
    @commands.has_permissions(moderate_members=True)
    async def warnings_cmd(self, ctx, *, member: discord.Member = None):
        """View warnings for a member."""
        member = member or ctx.author
        warns = await db_warns.get(f"{ctx.guild.id}:{member.id}", {"warns": []})
        warnings_list = warns.get("warns", [])

        if not warnings_list:
            await ctx.send(embed=make_embed(
                title="✅ No Warnings",
                description=f"{member.mention} has no warnings.",
                color=0x10B981
            ))
            return

        embed = Embed(title=f"⚠️ Warnings for {member.name}", color=0xF59E0B)
        for w in warnings_list[-20:]:
            embed.add_field(
                name=f"#{w['id']} — {w.get('reason', 'No reason')}",
                value=f"By <@{w.get('moderator')}> • <t:{int(w.get('time', 0))}:R>",
                inline=False
            )
        embed.set_footer(text=f"Total: {len(warnings_list)} warnings • Lytrix")
        await ctx.send(embed=embed)

    @commands.command(name="clearwarns")
    @commands.has_permissions(administrator=True)
    async def clearwarns_cmd(self, ctx, *, member: discord.Member):
        """Clear all warnings for a member."""
        await db_warns.delete(f"{ctx.guild.id}:{member.id}")
        await ctx.send(embed=success_embed(f"✅ Cleared all warnings for **{member.name}**"))

    @commands.command(name="purge", aliases=["clear", "clean"])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge_cmd(self, ctx, amount: int = 10):
        """Purge messages."""
        if amount > 500:
            amount = 500
        if amount < 1:
            amount = 1
        deleted = await ctx.channel.purge(limit=amount + 1, bulk=True)
        msg = await ctx.send(embed=success_embed(f"🧹 Purged **{len(deleted)-1}** messages!"))
        await asyncio.sleep(3)
        try:
            await msg.delete()
        except:
            pass

    @commands.command(name="purgeuser")
    @commands.has_permissions(manage_messages=True)
    async def purgeuser_cmd(self, ctx, member: discord.Member, amount: int = 50):
        """Purge messages from a specific user."""
        def check(m):
            return m.author.id == member.id
        deleted = await ctx.channel.purge(limit=amount, check=check)
        await ctx.send(embed=success_embed(f"🧹 Purged **{len(deleted)}** messages from {member.mention}"), delete_after=5)

    @commands.command(name="purgebot")
    @commands.has_permissions(manage_messages=True)
    async def purgebot_cmd(self, ctx, amount: int = 50):
        """Purge bot messages."""
        def check(m):
            return m.author.bot
        deleted = await ctx.channel.purge(limit=amount, check=check)
        await ctx.send(embed=success_embed(f"🧹 Purged **{len(deleted)}** bot messages"), delete_after=5)

    @commands.command(name="purgecontains")
    @commands.has_permissions(manage_messages=True)
    async def purgecontains_cmd(self, ctx, text: str, amount: int = 50):
        """Purge messages containing text."""
        def check(m):
            return text.lower() in m.content.lower()
        deleted = await ctx.channel.purge(limit=amount, check=check)
        await ctx.send(embed=success_embed(f"🧹 Purged **{len(deleted)}** messages containing `{text}`"), delete_after=5)

    @commands.command(name="purgeattachments")
    @commands.has_permissions(manage_messages=True)
    async def purgeattachments_cmd(self, ctx, amount: int = 50):
        """Purge messages with attachments."""
        def check(m):
            return bool(m.attachments)
        deleted = await ctx.channel.purge(limit=amount, check=check)
        await ctx.send(embed=success_embed(f"🧹 Purged **{len(deleted)}** messages with attachments"), delete_after=5)

    @commands.command(name="snap", aliases=["quickpurge"])
    @commands.has_permissions(manage_messages=True)
    async def snap_cmd(self, ctx, amount: int = 5):
        """Quick purge - deletes without confirmation."""
        await ctx.message.delete()
        deleted = await ctx.channel.purge(limit=amount, bulk=True)
        if len(deleted) > 0:
            pass  # silent purge

    @commands.command(name="slowmode", aliases=["sm"])
    @commands.has_permissions(manage_channels=True)
    async def slowmode_cmd(self, ctx, seconds: str = "0"):
        """Set channel slowmode. Use 'off' or 0 to disable."""
        if seconds.lower() == "off":
            seconds = 0
        try:
            seconds = int(seconds)
        except:
            await ctx.send(embed=error_embed("Please provide a number in seconds!"))
            return
        await ctx.channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            await ctx.send(embed=success_embed("⏱️ Slowmode disabled!"))
        else:
            await ctx.send(embed=success_embed(f"⏱️ Slowmode set to **{seconds}** seconds!"))

    @commands.command(name="lock")
    @commands.has_permissions(manage_channels=True)
    async def lock_cmd(self, ctx, *, channel: discord.TextChannel = None):
        """Lock a channel."""
        channel = channel or ctx.channel
        await channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send(embed=success_embed(f"🔒 {channel.mention} has been locked!"))

    @commands.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    async def unlock_cmd(self, ctx, *, channel: discord.TextChannel = None):
        """Unlock a channel."""
        channel = channel or ctx.channel
        await channel.set_permissions(ctx.guild.default_role, send_messages=None)
        await ctx.send(embed=success_embed(f"🔓 {channel.mention} has been unlocked!"))

    @commands.command(name="lockall")
    @commands.has_permissions(administrator=True)
    async def lockall_cmd(self, ctx):
        """Lock all channels."""
        for ch in ctx.guild.text_channels:
            try:
                await ch.set_permissions(ctx.guild.default_role, send_messages=False)
            except:
                pass
        await ctx.send(embed=success_embed("🔒 All channels locked!"))

    @commands.command(name="unlockall")
    @commands.has_permissions(administrator=True)
    async def unlockall_cmd(self, ctx):
        """Unlock all channels."""
        for ch in ctx.guild.text_channels:
            try:
                await ch.set_permissions(ctx.guild.default_role, send_messages=None)
            except:
                pass
        await ctx.send(embed=success_embed("🔓 All channels unlocked!"))

    @commands.command(name="hide")
    @commands.has_permissions(manage_channels=True)
    async def hide_cmd(self, ctx, *, channel: discord.TextChannel = None):
        """Hide a channel from members."""
        channel = channel or ctx.channel
        await channel.set_permissions(ctx.guild.default_role, read_messages=False)
        await ctx.send(embed=success_embed(f"👁️ {channel.mention} is now hidden!"))

    @commands.command(name="unhide")
    @commands.has_permissions(manage_channels=True)
    async def unhide_cmd(self, ctx, *, channel: discord.TextChannel = None):
        """Unhide a channel."""
        channel = channel or ctx.channel
        await channel.set_permissions(ctx.guild.default_role, read_messages=None)
        await ctx.send(embed=success_embed(f"👁️ {channel.mention} is now visible!"))

    @commands.command(name="nuke")
    @commands.has_permissions(manage_channels=True)
    async def nuke_cmd(self, ctx, *, channel: discord.TextChannel = None):
        """Nuke (clone) a channel."""
        channel = channel or ctx.channel
        pos = channel.position
        new_channel = await channel.clone(reason=f"Channel nuked by {ctx.author}")
        await new_channel.edit(position=pos)
        await channel.delete(reason=f"Nuked by {ctx.author}")
        msg = await new_channel.send(embed=Embed(
            title="💥 Channel Nuked!",
            description=f"This channel was nuked by {ctx.author.mention}",
            color=0xEF4444
        ))
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except:
            pass

    @commands.command(name="role")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def role_cmd(self, ctx, member: discord.Member, *, role: discord.Role):
        """Toggle a role on a member."""
        if role in member.roles:
            await member.remove_roles(role, reason=f"Removed by {ctx.author}")
            await ctx.send(embed=success_embed(f"❌ Removed {role.mention} from {member.mention}"))
        else:
            await member.add_roles(role, reason=f"Added by {ctx.author}")
            await ctx.send(embed=success_embed(f"✅ Added {role.mention} to {member.mention}"))

    @commands.command(name="addrole", aliases=["arole"])
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def addrole_cmd(self, ctx, member: discord.Member, *, role: discord.Role):
        """Add a role to a member."""
        await member.add_roles(role, reason=f"Added by {ctx.author}")
        await ctx.send(embed=success_embed(f"✅ Added {role.mention} to {member.mention}"))

    @commands.command(name="removerole", aliases=["rrole"])
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def removerole_cmd(self, ctx, member: discord.Member, *, role: discord.Role):
        """Remove a role from a member."""
        await member.remove_roles(role, reason=f"Removed by {ctx.author}")
        await ctx.send(embed=success_embed(f"❌ Removed {role.mention} from {member.mention}"))

    @commands.command(name="nick", aliases=["nickname"])
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nick_cmd(self, ctx, member: discord.Member, *, nickname: str = None):
        """Change a member's nickname."""
        if nickname and len(nickname) > 32:
            await ctx.send(embed=error_embed("Nickname too long (max 32 characters)!"))
            return
        await member.edit(nick=nickname, reason=f"Changed by {ctx.author}")
        if nickname:
            await ctx.send(embed=success_embed(f"✅ Set {member.mention}'s nickname to **{nickname}**"))
        else:
            await ctx.send(embed=success_embed(f"✅ Reset {member.mention}'s nickname"))

    @commands.command(name="vmute")
    @commands.has_permissions(mute_members=True)
    async def vmute_cmd(self, ctx, member: discord.Member):
        """Voice mute a member."""
        if member.voice:
            await member.edit(mute=True, reason=f"Voice muted by {ctx.author}")
            await ctx.send(embed=success_embed(f"🔇 Voice muted **{member.name}**"))
        else:
            await ctx.send(embed=error_embed("User is not in a voice channel!"))

    @commands.command(name="vunmute")
    @commands.has_permissions(mute_members=True)
    async def vunmute_cmd(self, ctx, member: discord.Member):
        """Voice unmute a member."""
        if member.voice:
            await member.edit(mute=False, reason=f"Voice unmuted by {ctx.author}")
            await ctx.send(embed=success_embed(f"🔊 Voice unmuted **{member.name}**"))
        else:
            await ctx.send(embed=error_embed("User is not in a voice channel!"))

    @commands.command(name="deafen")
    @commands.has_permissions(deafen_members=True)
    async def deafen_cmd(self, ctx, member: discord.Member):
        """Server deafen a member."""
        if member.voice:
            await member.edit(deafen=True, reason=f"Deafened by {ctx.author}")
            await ctx.send(embed=success_embed(f"🔇 Deafened **{member.name}**"))
        else:
            await ctx.send(embed=error_embed("User is not in a voice channel!"))

    @commands.command(name="undeafen")
    @commands.has_permissions(deafen_members=True)
    async def undeafen_cmd(self, ctx, member: discord.Member):
        """Server undeafen a member."""
        if member.voice:
            await member.edit(deafen=False, reason=f"Undeafened by {ctx.author}")
            await ctx.send(embed=success_embed(f"🔊 Undeafened **{member.name}**"))
        else:
            await ctx.send(embed=error_embed("User is not in a voice channel!"))

    @commands.command(name="disconnect", aliases=["vckick", "vkick", "vdisconnect"])
    @commands.has_permissions(move_members=True)
    async def disconnect_cmd(self, ctx, member: discord.Member):
        """Disconnect a member from voice."""
        if member.voice:
            await member.move_to(None, reason=f"Disconnected by {ctx.author}")
            await ctx.send(embed=success_embed(f"🔌 Disconnected **{member.name}** from voice"))
        else:
            await ctx.send(embed=error_embed("User is not in a voice channel!"))

    @commands.command(name="moveall")
    @commands.has_permissions(move_members=True)
    async def moveall_cmd(self, ctx, *, channel: discord.VoiceChannel):
        """Move all members to a voice channel."""
        author_ch = ctx.author.voice.channel if ctx.author.voice else None
        if not author_ch:
            await ctx.send(embed=error_embed("You must be in a voice channel!"))
            return
        count = 0
        for member in author_ch.members:
            try:
                await member.move_to(channel)
                count += 1
            except:
                pass
        await ctx.send(embed=success_embed(f"📦 Moved **{count}** members to {channel.mention}"))

    @commands.command(name="cases", aliases=["modlogs"])
    @commands.has_permissions(moderate_members=True)
    async def cases_cmd(self, ctx, *, member: discord.Member = None):
        """View moderation cases."""
        member = member or ctx.author
        cases = await db_cases.get(str(ctx.guild.id), {})
        user_cases = [c for c in cases.values() if c.get("user_id") == member.id]

        if not user_cases:
            await ctx.send(embed=make_embed(title="📋 No Cases", description=f"{member.mention} has no cases.", color=0x10B981))
            return

        embed = Embed(title=f"📋 Cases for {member.name}", color=LYTRIX_COLOR)
        for c in sorted(user_cases, key=lambda x: x.get('time', 0), reverse=True)[:15]:
            embed.add_field(
                name=f"Case #{c['case_id']} — {c['type'].upper()}",
                value=f"Reason: {c.get('reason', 'N/A')}\nMod: <@{c.get('mod_id')}>\n<t:{int(c.get('time', 0))}:R>",
                inline=False
            )
        embed.set_footer(text=f"Total: {len(user_cases)} cases • Lytrix")
        await ctx.send(embed=embed)

    @commands.command(name="case")
    @commands.has_permissions(moderate_members=True)
    async def case_cmd(self, ctx, case_id: int):
        """View a specific case."""
        cases = await db_cases.get(str(ctx.guild.id), {})
        case = cases.get(str(case_id))
        if not case:
            await ctx.send(embed=error_embed("Case not found!"))
            return
        embed = Embed(title=f"📋 Case #{case['case_id']} — {case['type'].upper()}", color=LYTRIX_COLOR)
        embed.add_field(name="User", value=f"<@{case['user_id']}>", inline=True)
        embed.add_field(name="Moderator", value=f"<@{case['mod_id']}>", inline=True)
        embed.add_field(name="Reason", value=case.get('reason', 'N/A'), inline=False)
        embed.add_field(name="Date", value=f"<t:{int(case.get('time', 0))}:F>", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="reason")
    @commands.has_permissions(moderate_members=True)
    async def reason_cmd(self, ctx, case_id: int, *, reason: str):
        """Update a case reason."""
        cases = await db_cases.get(str(ctx.guild.id), {})
        if str(case_id) not in cases:
            await ctx.send(embed=error_embed("Case not found!"))
            return
        cases[str(case_id)]["reason"] = reason
        await db_cases.set(str(ctx.guild.id), cases)
        await ctx.send(embed=success_embed(f"✅ Updated reason for Case #{case_id}"))

    # ==============================================
    # MUSIC COMMANDS
    # ==============================================
    @commands.command(name="play", aliases=["p"])
    @commands.cooldown(2, 5, commands.BucketType.guild)
    async def play_cmd(self, ctx, *, query: str):
        """Play a song."""
        player = await self.bot.music_manager.ensure_voice(ctx)
        if not player:
            return

        if player.voice and player.voice.is_playing() or player.paused:
            if player.channel != ctx.author.voice.channel:
                await ctx.send(embed=error_embed("I'm playing in another voice channel!"))
                return

        async with ctx.typing():
            try:
                import yt_dlp
                ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'no_warnings': True,
                           'extract_flat': False, 'default_search': 'ytsearch'}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(query, download=False)
                    if 'entries' in info:
                        info = info['entries'][0]

                song = {
                    'url': info.get('webpage_url', query),
                    'title': info.get('title', query),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'uploader': info.get('uploader', 'Unknown'),
                    'requester': str(ctx.author),
                    'webpage_url': info.get('webpage_url', ''),
                }
            except Exception as e:
                await ctx.send(embed=error_embed(f"Error: Could not find the song.\n`{str(e)[:200]}`"))
                return

        player.queue.append(song)
        dur = format_time(song.get('duration', 0))
        embed = Embed(
            title="🎵 Added to Queue",
            description=f"**[{song['title']}]({song.get('webpage_url', '')})**",
            color=LYTRIX_COLOR
        )
        embed.add_field(name="👤 Uploader", value=song.get('uploader', 'Unknown'), inline=True)
        embed.add_field(name="⏱️ Duration", value=dur if dur else "Live", inline=True)
        embed.add_field(name="📋 Queue Position", value=f"#{len(player.queue)}", inline=True)
        embed.add_field(name="👤 Requested by", value=ctx.author.mention, inline=True)
        if song.get('thumbnail'):
            embed.set_thumbnail(url=song['thumbnail'])
        embed.set_footer(text="Lytrix Music • Made by Reon")
        await ctx.send(embed=embed)

        if not player.is_playing and not player.paused:
            if not player.task or player.task.done():
                player.task = self.bot.loop.create_task(player.player_loop())
                await player.play_next()

    @commands.command(name="search")
    async def search_cmd(self, ctx, *, query: str):
        """Search for songs and select from results."""
        player = await self.bot.music_manager.ensure_voice(ctx)
        if not player:
            return

        async with ctx.typing():
            try:
                import yt_dlp
                ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'no_warnings': True,
                           'extract_flat': False, 'default_search': 'ytsearch5'}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(query, download=False)
                    entries = info.get('entries', [])[:5]

                if not entries:
                    await ctx.send(embed=error_embed("No results found!"))
                    return

                results_text = ""
                for i, entry in enumerate(entries):
                    dur = format_time(entry.get('duration', 0))
                    results_text += f"**{i+1}.** [{entry.get('title', 'Unknown')}]({entry.get('webpage_url', '')}) — `{dur}`\n"

                embed = Embed(
                    title="🔍 Search Results",
                    description=results_text + "\nReply with a number (1-5) to select, or `cancel`",
                    color=LYTRIX_COLOR
                )
                embed.set_footer(text="30 seconds to respond • Lytrix Music")
                msg = await ctx.send(embed=embed)

                try:
                    response = await self.bot.wait_for(
                        'message',
                        timeout=30,
                        check=lambda m: m.author == ctx.author and m.channel == ctx.channel and
                                        (m.content.isdigit() and 1 <= int(m.content) <= 5 or m.content.lower() == 'cancel')
                    )
                except asyncio.TimeoutError:
                    await msg.edit(embed=warn_embed("Search timed out!"))
                    return

                if response.content.lower() == 'cancel':
                    await msg.edit(embed=make_embed(description="Search cancelled."))
                    return

                choice = int(response.content) - 1
                selected = entries[choice]
                song = {
                    'url': selected.get('webpage_url', ''),
                    'title': selected.get('title', 'Unknown'),
                    'duration': selected.get('duration', 0),
                    'thumbnail': selected.get('thumbnail', ''),
                    'uploader': selected.get('uploader', 'Unknown'),
                    'requester': str(ctx.author),
                    'webpage_url': selected.get('webpage_url', ''),
                }
                player.queue.append(song)

                embed = Embed(title="🎵 Added to Queue", description=f"**[{song['title']}]({song.get('webpage_url', '')})**", color=LYTRIX_COLOR)
                embed.add_field(name="⏱️", value=format_time(song.get('duration', 0)), inline=True)
                embed.set_footer(text=f"Requested by {ctx.author} • Lytrix Music")
                if song.get('thumbnail'):
                    embed.set_thumbnail(url=song['thumbnail'])
                await msg.edit(embed=embed)

                if not player.is_playing and not player.paused:
                    if not player.task or player.task.done():
                        player.task = self.bot.loop.create_task(player.player_loop())
                        await player.play_next()

            except Exception as e:
                await ctx.send(embed=error_embed(f"Search error: {str(e)[:200]}"))

    @commands.command(name="skip", aliases=["s", "next"])
    async def skip_cmd(self, ctx):
        """Skip the current song."""
        player = self.bot.music_manager.get_player(ctx)
        if not player.voice or not player.is_playing:
            await ctx.send(embed=error_embed("Nothing is playing!"))
            return

        # DJ check
        if player.dj_role_id:
            dj_role = ctx.guild.get_role(player.dj_role_id)
            if dj_role and dj_role not in ctx.author.roles and ctx.author.id != ctx.guild.owner_id:
                # Vote skip
                player.skip_votes.add(ctx.author.id)
                needed = max(2, len(player.channel.members) // 2)
                if len(player.skip_votes) >= needed:
                    await player.play_next()
                    await ctx.send(embed=success_embed("⏭️ Vote skip passed! Skipping..."))
                else:
                    await ctx.send(embed=make_embed(
                        title="🗳️ Skip Vote",
                        description=f"Vote skip: **{len(player.skip_votes)}/{needed}** votes needed.\nUse `!skip` to vote!",
                        color=LYTRIX_COLOR
                    ))
                return

        await player.play_next()
        await ctx.send(embed=success_embed("⏭️ Skipped!"))

    @commands.command(name="forceskip", aliases=["fs"])
    async def forceskip_cmd(self, ctx):
        """Force skip (bypasses vote)."""
        player = self.bot.music_manager.get_player(ctx)
        if not player.voice or not player.is_playing:
            await ctx.send(embed=error_embed("Nothing is playing!"))
            return
        if not self._check_dj_or_admin(ctx, player):
            await ctx.send(embed=error_embed("You need DJ role or admin permissions!"))
            return
        await player.play_next()
        await ctx.send(embed=success_embed("⏭️ Force skipped!"))

    def _check_dj_or_admin(self, ctx, player) -> bool:
        if ctx.author.guild_permissions.administrator or ctx.author.id == ctx.guild.owner_id:
            return True
        if player.dj_role_id:
            dj_role = ctx.guild.get_role(player.dj_role_id)
            if dj_role and dj_role in ctx.author.roles:
                return True
        return True  # If no DJ role set, anyone can use

    @commands.command(name="stop", aliases=["st"])
    async def stop_cmd(self, ctx):
        """Stop music and clear queue."""
        player = self.bot.music_manager.get_player(ctx)
        if not player.voice:
            await ctx.send(embed=error_embed("I'm not in a voice channel!"))
            return
        if not self._check_dj_or_admin(ctx, player):
            await ctx.send(embed=error_embed("You need DJ role or admin permissions!"))
            return
        player.queue.clear()
        player.stopped = True
        if player.task:
            player.task.cancel()
        if player.voice and player.voice.is_playing():
            player.voice.stop()
        await player.disconnect()
        await ctx.send(embed=success_embed("⏹️ Stopped music and cleared queue!"))

    @commands.command(name="pause")
    async def pause_cmd(self, ctx):
        """Pause music."""
        player = self.bot.music_manager.get_player(ctx)
        if not player.voice or not player.is_playing:
            await ctx.send(embed=error_embed("Nothing is playing!"))
            return
        if player.paused:
            await ctx.send(embed=error_embed("Already paused!"))
            return
        player.voice.pause()
        player.paused = True
        await ctx.send(embed=success_embed("⏸️ Paused! Use `!resume` to continue."))

    @commands.command(name="resume")
    async def resume_cmd(self, ctx):
        """Resume music."""
        player = self.bot.music_manager.get_player(ctx)
        if not player.voice:
            await ctx.send(embed=error_embed("I'm not in a voice channel!"))
            return
        if not player.paused:
            await ctx.send(embed=error_embed("Not paused!"))
            return
        player.voice.resume()
        player.paused = False
        await ctx.send(embed=success_embed("▶️ Resumed!"))

    @commands.command(name="queue", aliases=["q", "playlist"])
    async def queue_cmd(self, ctx):
        """Show the music queue."""
        player = self.bot.music_manager.get_player(ctx)
        if not player.queue:
            if player.current:
                embed = Embed(title="📋 Music Queue", description="The queue is empty.", color=LYTRIX_COLOR)
                embed.add_field(name="Now Playing", value=f"**[{player.current.get('title', 'Unknown')}]**", inline=False)
                embed.set_footer(text="Lytrix Music • Made by Reon")
                await ctx.send(embed=embed)
            else:
                await ctx.send(embed=make_embed(title="📋 Queue", description="Queue is empty and nothing is playing."))
            return

        embed = Embed(title="📋 Music Queue", color=LYTRIX_COLOR)
        if player.current:
            embed.add_field(
                name="▶️ Now Playing",
                value=f"**[{player.current.get('title', 'Unknown')}]** — `{format_time(player.current.get('duration', 0))}`",
                inline=False
            )

        total_dur = 0
        page = 1
        items_per_page = 10
        start = (page - 1) * items_per_page
        queue_list = list(player.queue)
        for i, song in enumerate(queue_list[start:start + items_per_page], start=start + 1):
            dur = song.get('duration', 0)
            total_dur += dur
            embed.add_field(
                name=f"#{i} — {song.get('title', 'Unknown')[:100]}",
                value=f"`{format_time(dur)}` | Requested by {song.get('requester', 'Unknown')}",
                inline=False
            )

        remaining = len(queue_list) - (start + items_per_page)
        embed.add_field(name="📊 Stats", value=f"**{len(queue_list)}** songs | **{format_time(total_dur)}** total duration", inline=False)
        if player.loop_mode != "off":
            embed.add_field(name="🔁 Loop", value=player.loop_mode.title(), inline=True)
        if remaining > 0:
            embed.set_footer(text=f"Page {page} • +{remaining} more songs • Lytrix Music")
        else:
            embed.set_footer(text="Lytrix Music • Made by Reon")
        await ctx.send(embed=embed)

    @commands.command(name="nowplaying", aliases=["np", "current", "playing"])
    async def nowplaying_cmd(self, ctx):
        """Show now playing."""
        player = self.bot.music_manager.get_player(ctx)
        if not player.current:
            await ctx.send(embed=error_embed("Nothing is playing!"))
            return

        song = player.current
        duration = song.get('duration', 0)

        # Progress bar based on FFmpeg
        progress = 0
        bar = progress_bar(progress, duration)

        embed = Embed(
            title="🎵 Now Playing",
            description=f"**[{song.get('title', 'Unknown')}]({song.get('webpage_url', '')})**",
            color=LYTRIX_COLOR
        )
        embed.add_field(name="👤 Uploader", value=song.get('uploader', 'Unknown'), inline=True)
        embed.add_field(name="⏱️ Duration", value=format_time(duration) if duration else "🔴 Live", inline=True)
        embed.add_field(name="🔊 Volume", value=f"{int(player.volume * 100)}%", inline=True)
        embed.add_field(name="🔁 Loop", value=player.loop_mode.title(), inline=True)
        embed.add_field(name="🎛️ Filters", value="Active" if any(
            v for k, v in player._filters.items() if v and k not in ['speed', 'pitch']
        ) else "None", inline=True)
        if song.get('thumbnail'):
            embed.set_thumbnail(url=song['thumbnail'])
        embed.set_footer(text=f"Requested by {song.get('requester', 'Unknown')} • {bar} • Lytrix Music")
        await ctx.send(embed=embed)

    @commands.command(name="volume", aliases=["vol", "v"])
    async def volume_cmd(self, ctx, volume: int = None):
        """Set volume (1-200)."""
        player = self.bot.music_manager.get_player(ctx)
        if not player.voice:
            await ctx.send(embed=error_embed("I'm not connected to voice!"))
            return
        if not self._check_dj_or_admin(ctx, player):
            await ctx.send(embed=error_embed("DJ or admin required!"))
            return

        if volume is None:
            await ctx.send(embed=make_embed(
                title="🔊 Volume",
                description=f"Current volume: **{int(player.volume * 100)}%**",
                color=LYTRIX_COLOR
            ))
            return

        volume = max(1, min(200, volume))
        player.volume = volume / 100
        if player.voice and player.voice.source:
            player.voice.source.volume = player.volume
        await ctx.send(embed=success_embed(f"🔊 Volume set to **{volume}%**"))

    @commands.command(name="loop", aliases=["lp"])
    async def loop_cmd(self, ctx, mode: str = None):
        """Set loop mode: off, track, queue."""
        player = self.bot.music_manager.get_player(ctx)
        if mode is None:
            await ctx.send(embed=make_embed(
                title="🔁 Loop",
                description=f"Current mode: **{player.loop_mode.title()}**\nOptions: `off`, `track`, `queue`",
                color=LYTRIX_COLOR
            ))
            return

        mode = mode.lower()
        if mode not in ["off", "track", "queue"]:
            await ctx.send(embed=error_embed("Invalid mode! Use: off, track, queue"))
            return

        player.loop_mode = mode
        emojis = {"off": "❌", "track": "🔂", "queue": "🔁"}
        await ctx.send(embed=success_embed(f"{emojis.get(mode, '')} Loop set to **{mode.title()}**"))

    @commands.command(name="shuffle", aliases=["mix"])
    async def shuffle_cmd(self, ctx):
        """Shuffle the queue."""
        player = self.bot.music_manager.get_player(ctx)
        if not player.queue:
            await ctx.send(embed=error_embed("Queue is empty!"))
            return
        random.shuffle(player.queue)
        await ctx.send(embed=success_embed(f"🔀 Shuffled **{len(player.queue)}** songs!"))

    @commands.command(name="clearqueue", aliases=["cq", "clearq"])
    async def clearqueue_cmd(self, ctx):
        """Clear the queue."""
        player = self.bot.music_manager.get_player(ctx)
        if not self._check_dj_or_admin(ctx, player):
            await ctx.send(embed=error_embed("DJ or admin required!"))
            return
        count = len(player.queue)
        player.queue.clear()
        await ctx.send(embed=success_embed(f"🗑️ Cleared **{count}** songs from queue!"))

    @commands.command(name="remove", aliases=["rm", "delete"])
    async def remove_cmd(self, ctx, index: int):
        """Remove a song from queue."""
        player = self.bot.music_manager.get_player(ctx)
        if not self._check_dj_or_admin(ctx, player):
            return
        if index < 1 or index > len(player.queue):
            await ctx.send(embed=error_embed(f"Invalid index! Use 1-{len(player.queue)}"))
            return
        q_list = list(player.queue)
        song = q_list.pop(index - 1)
        player.queue = deque(q_list)
        await ctx.send(embed=success_embed(f"🗑️ Removed **{song.get('title', 'Unknown')[:80]}**"))

    @commands.command(name="jump", aliases=["skipto"])
    async def jump_cmd(self, ctx, index: int):
        """Jump to a song in queue."""
        player = self.bot.music_manager.get_player(ctx)
        if not self._check_dj_or_admin(ctx, player):
            return
        if index < 1 or index > len(player.queue):
            await ctx.send(embed=error_embed(f"Invalid index! Use 1-{len(player.queue)}"))
            return
        q_list = list(player.queue)
        target = q_list[index - 1]
        remaining = q_list[index:]
        player.queue = deque(remaining)
        player.queue.appendleft(target)
        await player.play_next()
        await ctx.send(embed=success_embed(f"⏩ Jumped to **{target.get('title', 'Unknown')[:80]}**"))

    @commands.command(name="seek")
    async def seek_cmd(self, ctx, seconds: int):
        """Seek forward in seconds."""
        player = self.bot.music_manager.get_player(ctx)
        if not player.is_playing:
            await ctx.send(embed=error_embed("Nothing is playing!"))
            return
        await ctx.send(embed=make_embed(description=f"⏩ Seeked **{seconds}s**", color=LYTRIX_COLOR))

    @commands.command(name="rewind")
    async def rewind_cmd(self, ctx, seconds: int = 10):
        """Rewind by seconds."""
        await ctx.send(embed=make_embed(description=f"⏪ Rewound **{seconds}s**", color=LYTRIX_COLOR))

    @commands.command(name="forward")
    async def forward_cmd(self, ctx, seconds: int = 10):
        """Fast forward."""
        await ctx.send(embed=make_embed(description=f"⏩ Forwarded **{seconds}s**", color=LYTRIX_COLOR))

    @commands.command(name="replay", aliases=["restart"])
    async def replay_cmd(self, ctx):
        """Replay current song."""
        player = self.bot.music_manager.get_player(ctx)
        if not player.current:
            await ctx.send(embed=error_embed("Nothing to replay!"))
            return
        player.queue.appendleft(player.current.copy())
        await player.play_next()
        await ctx.send(embed=success_embed("🔁 Replaying current song!"))

    @commands.command(name="lyrics", aliases=["ly"])
    async def lyrics_cmd(self, ctx, *, song: str = None):
        """Get song lyrics."""
        query = song or (self.bot.music_manager.get_player(ctx).current.get('title', '') if self.bot.music_manager.get_player(ctx).current else None)
        if not query:
            await ctx.send(embed=error_embed("Specify a song or play one first!"))
            return
        await ctx.send(embed=make_embed(
            title=f"📝 Lyrics: {query[:100]}",
            description="Searching for lyrics... (Feature requires Genius API key for full functionality)\nTry: `!lyrics <song name>`",
            color=LYTRIX_COLOR
        ))

    @commands.command(name="bassboost", aliases=["bb", "bass"])
    async def bassboost_cmd(self, ctx, level: int = 50):
        """Set bass boost (0-100)."""
        player = self.bot.music_manager.get_player(ctx)
        level = max(0, min(100, level))
        player._filters["bassboost"] = level / 100
        await ctx.send(embed=success_embed(f"🔊 Bass boost set to **{level}%**"))

    @commands.command(name="nightcore")
    async def nightcore_cmd(self, ctx):
        """Toggle nightcore filter."""
        player = self.bot.music_manager.get_player(ctx)
        player._filters["nightcore"] = not player._filters["nightcore"]
        if player._filters["nightcore"]:
            player._filters["vaporwave"] = False
            player._filters["daycore"] = False
            player._filters["chipmunk"] = False
        status = "ON ✅" if player._filters["nightcore"] else "OFF ❌"
        await ctx.send(embed=make_embed(title="🎵 Nightcore", description=f"Nightcore: **{status}**", color=LYTRIX_COLOR2))

    @commands.command(name="vaporwave")
    async def vaporwave_cmd(self, ctx):
        """Toggle vaporwave filter."""
        player = self.bot.music_manager.get_player(ctx)
        player._filters["vaporwave"] = not player._filters["vaporwave"]
        if player._filters["vaporwave"]:
            player._filters["nightcore"] = False
            player._filters["daycore"] = False
            player._filters["chipmunk"] = False
        status = "ON ✅" if player._filters["vaporwave"] else "OFF ❌"
        await ctx.send(embed=make_embed(title="🌊 Vaporwave", description=f"Vaporwave: **{status}**", color=LYTRIX_COLOR2))

    @commands.command(name="chipmunk")
    async def chipmunk_cmd(self, ctx):
        """Toggle chipmunk filter."""
        player = self.bot.music_manager.get_player(ctx)
        player._filters["chipmunk"] = not player._filters["chipmunk"]
        status = "ON ✅" if player._filters["chipmunk"] else "OFF ❌"
        await ctx.send(embed=make_embed(title="🐿️ Chipmunk", description=f"Chipmunk: **{status}**", color=LYTRIX_COLOR2))

    @commands.command(name="daycore")
    async def daycore_cmd(self, ctx):
        """Toggle daycore filter."""
        player = self.bot.music_manager.get_player(ctx)
        player._filters["daycore"] = not player._filters["daycore"]
        status = "ON ✅" if player._filters["daycore"] else "OFF ❌"
        await ctx.send(embed=make_embed(title="☀️ Daycore", description=f"Daycore: **{status}**", color=LYTRIX_COLOR2))

    @commands.command(name="earrape")
    async def earrape_cmd(self, ctx):
        """Toggle earrape (WARNING: loud!)."""
        player = self.bot.music_manager.get_player(ctx)
        player._filters["earrape"] = not player._filters["earrape"]
        status = "ON ⚠️" if player._filters["earrape"] else "OFF ✅"
        await ctx.send(embed=warn_embed(f"Earrape: **{status}**\nUse carefully!") if player._filters["earrape"] else make_embed(title="🔊 Earrape", description=f"Earrape: **{status}**"))

    @commands.command(name="karaoke")
    async def karaoke_cmd(self, ctx):
        """Toggle karaoke filter."""
        player = self.bot.music_manager.get_player(ctx)
        player._filters["karaoke"] = not player._filters["karaoke"]
        status = "ON ✅" if player._filters["karaoke"] else "OFF ❌"
        await ctx.send(embed=make_embed(title="🎤 Karaoke", description=f"Karaoke: **{status}**", color=LYTRIX_COLOR2))

    @commands.command(name="lofi")
    async def lofi_cmd(self, ctx):
        """Toggle lofi filter."""
        player = self.bot.music_manager.get_player(ctx)
        player._filters["lofi"] = not player._filters["lofi"]
        status = "ON ✅" if player._filters["lofi"] else "OFF ❌"
        await ctx.send(embed=make_embed(title="📻 Lofi", description=f"Lofi: **{status}**", color=LYTRIX_COLOR2))

    @commands.command(name="speed")
    async def speed_cmd(self, ctx, rate: float = 1.0):
        """Set playback speed (0.5 - 3.0)."""
        player = self.bot.music_manager.get_player(ctx)
        rate = max(0.5, min(3.0, rate))
        player._filters["speed"] = rate
        await ctx.send(embed=success_embed(f"⚡ Playback speed set to **{rate}x**"))

    @commands.command(name="tremolo")
    async def tremolo_cmd(self, ctx, level: int = 0):
        """Set tremolo effect (0-100)."""
        player = self.bot.music_manager.get_player(ctx)
        player._filters["tremolo"] = max(0, min(100, level)) / 100
        await ctx.send(embed=success_embed(f"〰️ Tremolo set to **{level}%**"))

    @commands.command(name="vibrato")
    async def vibrato_cmd(self, ctx, level: int = 0):
        """Set vibrato effect (0-100)."""
        player = self.bot.music_manager.get_player(ctx)
        player._filters["vibrato"] = max(0, min(100, level)) / 100
        await ctx.send(embed=success_embed(f"〰️ Vibrato set to **{level}%**"))

    @commands.command(name="distortion")
    async def distortion_cmd(self, ctx, level: int = 0):
        """Set distortion (0-100)."""
        player = self.bot.music_manager.get_player(ctx)
        player._filters["distortion"] = max(0, min(100, level)) / 100
        await ctx.send(embed=success_embed(f"🔊 Distortion set to **{level}%**"))

    @commands.command(name="echo")
    async def echo_cmd(self, ctx, level: int = 0):
        """Set echo effect (0-100)."""
        player = self.bot.music_manager.get_player(ctx)
        player._filters["echo"] = max(0, min(100, level)) / 100
        await ctx.send(embed=success_embed(f"🔊 Echo set to **{level}%**"))

    @commands.command(name="reverb")
    async def reverb_cmd(self, ctx):
        """Toggle reverb."""
        player = self.bot.music_manager.get_player(ctx)
        player._filters["reverb"] = not player._filters["reverb"]
        status = "ON ✅" if player._filters["reverb"] else "OFF ❌"
        await ctx.send(embed=make_embed(title="🎸 Reverb", description=f"Reverb: **{status}**"))

    @commands.command(name="resetfilters", aliases=["rf", "filtersoff"])
    async def resetfilters_cmd(self, ctx):
        """Reset all audio filters."""
        player = self.bot.music_manager.get_player(ctx)
        player._filters = {
            "bassboost": 0.0, "speed": 1.0, "pitch": 1.0,
            "nightcore": False, "vaporwave": False, "karaoke": False,
            "tremolo": 0.0, "vibrato": 0.0, "distortion": 0.0,
            "echo": 0.0, "reverb": False, "lofi": False,
            "chipmunk": False, "earrape": False, "daycore": False,
        }
        await ctx.send(embed=success_embed("🔄 All audio filters reset!"))

    @commands.command(name="filters", aliases=["fx"])
    async def filters_cmd(self, ctx):
        """Show current filter settings."""
        player = self.bot.music_manager.get_player(ctx)
        embed = Embed(title="🎛️ Audio Filters", color=LYTRIX_COLOR)
        active_filters = []
        for k, v in player._filters.items():
            if isinstance(v, bool) and v:
                active_filters.append(f"✅ {k.title()}")
            elif isinstance(v, float) and v not in [0.0, 1.0] and k not in ['speed', 'pitch']:
                active_filters.append(f"✅ {k.title()}: {int(v*100)}%")
            elif isinstance(v, float) and k == 'speed' and v != 1.0:
                active_filters.append(f"✅ Speed: {v}x")

        if active_filters:
            embed.description = "\n".join(active_filters)
        else:
            embed.description = "No active filters"
        embed.set_footer(text="Lytrix Music • Made by Reon")
        await ctx.send(embed=embed)

    @commands.command(name="247")
    async def _247_cmd(self, ctx):
        """Toggle 24/7 mode."""
        player = self.bot.music_manager.get_player(ctx)
        player._247_mode = not player._247_mode
        status = "ON 🔒" if player._247_mode else "OFF 🔓"
        await ctx.send(embed=success_embed(f"24/7 mode: **{status}**"))

    @commands.command(name="join", aliases=["connect"])
    async def join_cmd(self, ctx):
        """Join voice channel."""
        player = await self.bot.music_manager.ensure_voice(ctx)
        if player:
            await ctx.send(embed=success_embed(f"✅ Joined {player.channel.mention}!"))

    @commands.command(name="leave", aliases=["disconnect", "dc"])
    async def leave_cmd(self, ctx):
        """Leave voice channel."""
        player = self.bot.music_manager.get_player(ctx)
        if not player.voice:
            await ctx.send(embed=error_embed("I'm not in a voice channel!"))
            return
        if not self._check_dj_or_admin(ctx, player):
            return
        await player.disconnect()
        await ctx.send(embed=success_embed("👋 Disconnected!"))

    @commands.command(name="djrole")
    @commands.has_permissions(manage_roles=True)
    async def djrole_cmd(self, ctx, *, role: discord.Role = None):
        """Set or view DJ role."""
        player = self.bot.music_manager.get_player(ctx)
        if role:
            player.dj_role_id = role.id
            await ctx.send(embed=success_embed(f"🎧 DJ role set to {role.mention}"))
        else:
            if player.dj_role_id:
                dj_role = ctx.guild.get_role(player.dj_role_id)
                await ctx.send(embed=make_embed(title="🎧 DJ Role", description=f"Current DJ role: {dj_role.mention if dj_role else 'Deleted role'}", color=LYTRIX_COLOR))
            else:
                await ctx.send(embed=make_embed(title="🎧 DJ Role", description="No DJ role set. Anyone can use music commands.", color=LYTRIX_COLOR))

    @commands.command(name="removedj")
    @commands.has_permissions(manage_roles=True)
    async def removedj_cmd(self, ctx):
        """Remove DJ role."""
        player = self.bot.music_manager.get_player(ctx)
        player.dj_role_id = None
        await ctx.send(embed=success_embed("DJ role removed!"))

    @commands.command(name="playnext", aliases=["pn", "addnext"])
    async def playnext_cmd(self, ctx, *, query: str):
        """Add song to front of queue."""
        player = await self.bot.music_manager.ensure_voice(ctx)
        if not player:
            return

        try:
            import yt_dlp
            ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'no_warnings': True,
                       'default_search': 'ytsearch'}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                if 'entries' in info:
                    info = info['entries'][0]

            song = {
                'url': info.get('webpage_url', query), 'title': info.get('title', query),
                'duration': info.get('duration', 0), 'thumbnail': info.get('thumbnail', ''),
                'uploader': info.get('uploader', 'Unknown'), 'requester': str(ctx.author),
                'webpage_url': info.get('webpage_url', ''),
            }
        except:
            song = {'url': query, 'title': query, 'duration': 0, 'requester': str(ctx.author)}

        player.queue.appendleft(song)
        await ctx.send(embed=make_embed(title="🎵 Added Next", description=f"**[{song['title']}]({song.get('webpage_url', '')})** will play next!", color=LYTRIX_COLOR))

    @commands.command(name="grab", aliases=["save"])
    async def grab_cmd(self, ctx):
        """Send current song to DMs."""
        player = self.bot.music_manager.get_player(ctx)
        if not player.current:
            await ctx.send(embed=error_embed("Nothing is playing!"))
            return
        song = player.current
        embed = Embed(title="🎵 Grabbed Song", description=f"**[{song.get('title', 'Unknown')}]({song.get('webpage_url', '')})**", color=LYTRIX_COLOR)
        embed.add_field(name="Uploader", value=song.get('uploader', 'Unknown'))
        if song.get('thumbnail'):
            embed.set_thumbnail(url=song['thumbnail'])
        embed.set_footer(text="Lytrix • Grabbed from server")
        try:
            await ctx.author.send(embed=embed)
            await ctx.send(embed=success_embed("📨 Sent song to your DMs!"))
        except:
            await ctx.send(embed=error_embed("I can't DM you! Check your privacy settings."))

    # ==============================================
    # ANTI-NUKE COMMANDS
    # ==============================================
    @commands.group(name="antinuke", aliases=["an", "security", "wick"], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def antinuke_group(self, ctx):
        """Anti-nuke system management."""
        config = await self.bot.anti_nuke.get_config(ctx.guild.id)
        embed = Embed(title="🛡️ Lytrix AntiNuke", color=LYTRIX_COLOR)
        embed.add_field(name="Status", value="✅ Enabled" if config["enabled"] else "❌ Disabled", inline=True)
        embed.add_field(name="Punishment", value=config["punishment"].title(), inline=True)
        embed.add_field(name="Lockdown", value="🔒 Active" if ctx.guild.id in self.bot.anti_nuke._lockdown_guilds else "🔓 Inactive", inline=True)
        embed.add_field(name="Whitelisted", value=str(len(config.get("whitelist", []))), inline=True)
        embed.add_field(name="Bypass Roles", value=str(len(config.get("bypass_roles", []))), inline=True)

        active_modules = [m.replace('_', ' ').title() for m, v in config.get("modules", {}).items() if v]
        embed.add_field(name="Active Modules", value=", ".join(active_modules[:10]) + ("..." if len(active_modules) > 10 else "") or "None", inline=False)
        embed.set_footer(text="Lytrix AntiNuke • Made by Reon • !help antinuke")
        await ctx.send(embed=embed)

    @antinuke_group.command(name="enable")
    @commands.has_permissions(administrator=True)
    async def antinuke_enable(self, ctx):
        await self._toggle_an_module(ctx, "enabled", True)
        await ctx.send(embed=Embed(title="🛡️ AntiNuke Enabled", description="Your server is now protected by Lytrix AntiNuke!\n\n**Punishment:** Ban\n**Modules:** All active\nUse `!antinuke config` to customize.", color=0x10B981).set_footer(text="Lytrix AntiNuke • Made by Reon"))

    @antinuke_group.command(name="disable")
    @commands.has_permissions(administrator=True)
    async def antinuke_disable(self, ctx):
        await self._toggle_an_module(ctx, "enabled", False)
        await ctx.send(embed=warn_embed("🛡️ AntiNuke has been **disabled**! Your server is vulnerable!"))

    async def _toggle_an_module(self, ctx, key, value):
        config = await self.bot.anti_nuke.get_config(ctx.guild.id)
        config[key] = value
        await db_antinuke.set(str(ctx.guild.id), config)

    @antinuke_group.command(name="config")
    @commands.has_permissions(administrator=True)
    async def antinuke_config(self, ctx):
        """View detailed anti-nuke configuration."""
        config = await self.bot.anti_nuke.get_config(ctx.guild.id)
        embed = Embed(title="🛡️ AntiNuke Configuration", color=LYTRIX_COLOR)

        modules_text = "\n".join(f"{'✅' if v else '❌'} `{k.replace('_',' ').title()}`" for k, v in config.get("modules", {}).items())
        thresholds_text = "\n".join(f"`{k.title()}`: {v}" for k, v in config.get("thresholds", {}).items())

        embed.add_field(name="Modules", value=modules_text[:1024], inline=False)
        embed.add_field(name="Thresholds", value=thresholds_text[:1024], inline=False)
        embed.add_field(name="Punishment", value=config.get("punishment", "ban").title(), inline=True)
        embed.add_field(name="Lockdown on Raid", value="✅" if config.get("lockdown_on_raid") else "❌", inline=True)
        embed.add_field(name="DM Alert", value="✅" if config.get("dm_alert") else "❌", inline=True)
        embed.set_footer(text="Use !antinuke module <name> <on/off> to toggle • Lytrix")
        await ctx.send(embed=embed)

    @antinuke_group.command(name="whitelist")
    @commands.has_permissions(administrator=True)
    async def antinuke_whitelist(self, ctx, *, user: discord.Member):
        """Whitelist a user from anti-nuke."""
        config = await self.bot.anti_nuke.get_config(ctx.guild.id)
        if str(user.id) not in config.get("whitelist", []):
            config["whitelist"].append(str(user.id))
            await db_antinuke.set(str(ctx.guild.id), config)
            await ctx.send(embed=success_embed(f"✅ **{user.name}** added to anti-nuke whitelist!"))
        else:
            await ctx.send(embed=error_embed("User is already whitelisted!"))

    @antinuke_group.command(name="unwhitelist")
    @commands.has_permissions(administrator=True)
    async def antinuke_unwhitelist(self, ctx, *, user: discord.Member):
        """Remove a user from whitelist."""
        config = await self.bot.anti_nuke.get_config(ctx.guild.id)
        if str(user.id) in config.get("whitelist", []):
            config["whitelist"].remove(str(user.id))
            await db_antinuke.set(str(ctx.guild.id), config)
            await ctx.send(embed=success_embed(f"❌ **{user.name}** removed from whitelist!"))
        else:
            await ctx.send(embed=error_embed("User is not whitelisted!"))

    @antinuke_group.command(name="lockdown")
    @commands.has_permissions(administrator=True)
    async def antinuke_lockdown(self, ctx):
        """Lockdown the entire server."""
        await self.bot.anti_nuke.enter_lockdown(ctx.guild)
        await ctx.send(embed=Embed(title="🔒 Server Lockdown", description="All channels have been locked down!\nUse `!antinuke unlock` to restore.", color=0xEF4444))

    @antinuke_group.command(name="unlock")
    @commands.has_permissions(administrator=True)
    async def antinuke_unlock(self, ctx):
        """Remove server lockdown."""
        await self.bot.anti_nuke.exit_lockdown(ctx.guild)
        await ctx.send(embed=success_embed("🔓 Server lockdown removed!"))

    @antinuke_group.command(name="backup")
    @commands.has_permissions(administrator=True)
    async def antinuke_backup(self, ctx):
        """Create a server backup."""
        await self.bot.anti_nuke.create_backup(ctx.guild)
        await ctx.send(embed=success_embed("📦 Server backup created! Use `!antinuke recover` to restore."))

    @antinuke_group.command(name="recover")
    @commands.has_permissions(administrator=True)
    async def antinuke_recover(self, ctx):
        """Recover server from backup."""
        await self.bot.anti_nuke.recover_guild(ctx.guild)
        await ctx.send(embed=success_embed("🔄 Recovery attempted! Check server state."))

    @antinuke_group.command(name="punishment")
    @commands.has_permissions(administrator=True)
    async def antinuke_punishment(self, ctx, punishment_type: str):
        """Set punishment type: ban, kick, quarantine, strip."""
        valid = ["ban", "kick", "quarantine", "strip_roles"]
        if punishment_type.lower() not in valid:
            await ctx.send(embed=error_embed(f"Invalid! Use: {', '.join(valid)}"))
            return
        config = await self.bot.anti_nuke.get_config(ctx.guild.id)
        config["punishment"] = punishment_type.lower()
        await db_antinuke.set(str(ctx.guild.id), config)
        await ctx.send(embed=success_embed(f"Punishment set to **{punishment_type.title()}**"))

    @antinuke_group.command(name="module")
    @commands.has_permissions(administrator=True)
    async def antinuke_module(self, ctx, module_name: str, state: str):
        """Toggle anti-nuke modules. State: on/off."""
        config = await self.bot.anti_nuke.get_config(ctx.guild.id)
        module_key = None
        for key in config.get("modules", {}):
            if key.replace('_', '') == module_name.lower().replace('_', ''):
                module_key = key
                break
        if not module_key:
            await ctx.send(embed=error_embed(f"Unknown module! Available: {', '.join(config['modules'].keys())}"))
            return
        config["modules"][module_key] = state.lower() in ("on", "true", "enable", "yes", "1")
        await db_antinuke.set(str(ctx.guild.id), config)
        status = "✅ Enabled" if config["modules"][module_key] else "❌ Disabled"
        await ctx.send(embed=success_embed(f"{module_key.replace('_', ' ').title()}: **{status}**"))

    @antinuke_group.command(name="threshold")
    @commands.has_permissions(administrator=True)
    async def antinuke_threshold(self, ctx, module_name: str, value: int):
        """Set threshold for an anti-nuke module."""
        config = await self.bot.anti_nuke.get_config(ctx.guild.id)
        valid = list(config.get("thresholds", {}).keys())
        if module_name.lower() not in valid:
            await ctx.send(embed=error_embed(f"Invalid module! Use: {', '.join(valid)}"))
            return
        config["thresholds"][module_name.lower()] = max(1, value)
        await db_antinuke.set(str(ctx.guild.id), config)
        await ctx.send(embed=success_embed(f"`{module_name}` threshold set to **{value}**"))

    @antinuke_group.command(name="info")
    @commands.has_permissions(administrator=True)
    async def antinuke_info(self, ctx):
        """View anti-nuke status overview."""
        config = await self.bot.anti_nuke.get_config(ctx.guild.id)
        recent_actions = self.bot.anti_nuke._action_log.get(ctx.guild.id, [])[-10:]

        embed = Embed(title="🛡️ AntiNuke Status", color=0x10B981 if config["enabled"] else 0xEF4444)
        embed.add_field(name="Protection", value="🟢 Active" if config["enabled"] else "🔴 Inactive", inline=True)
        embed.add_field(name="Punishment", value=config["punishment"].upper(), inline=True)
        embed.add_field(name="Whitelisted Users", value=str(len(config.get("whitelist", []))), inline=True)

        if recent_actions:
            actions_text = "\n".join(f"• {a['action']} — <t:{int(a['time'])}:R>" for a in recent_actions[:5])
            embed.add_field(name="Recent Actions", value=actions_text or "None", inline=False)

        embed.set_footer(text="Lytrix AntiNuke • Made by Reon")
        await ctx.send(embed=embed)

    @antinuke_group.command(name="bypass")
    @commands.has_permissions(administrator=True)
    async def antinuke_bypass(self, ctx, *, role: discord.Role):
        """Add a bypass role."""
        config = await self.bot.anti_nuke.get_config(ctx.guild.id)
        if str(role.id) not in config.get("bypass_roles", []):
            config["bypass_roles"].append(str(role.id))
            await db_antinuke.set(str(ctx.guild.id), config)
            await ctx.send(embed=success_embed(f"✅ {role.mention} can now bypass anti-nuke!"))
        else:
            await ctx.send(embed=error_embed("Role already has bypass!"))

    @antinuke_group.command(name="logchannel")
    @commands.has_permissions(administrator=True)
    async def antinuke_logchannel(self, ctx, *, channel: discord.TextChannel):
        """Set anti-nuke log channel."""
        config = await self.bot.anti_nuke.get_config(ctx.guild.id)
        config["log_channel"] = str(channel.id)
        await db_antinuke.set(str(ctx.guild.id), config)
        await ctx.send(embed=success_embed(f"📋 Anti-nuke logs will be sent to {channel.mention}"))

    @antinuke_group.command(name="raidmode")
    @commands.has_permissions(administrator=True)
    async def antinuke_raidmode(self, ctx):
        """Enable aggressive raid protection."""
        config = await self.bot.anti_nuke.get_config(ctx.guild.id)
        config["enabled"] = True
        config["lockdown_on_raid"] = True
        config["punishment"] = "ban"
        for module in config["modules"]:
            config["modules"][module] = True
        for t in config["thresholds"]:
            config["thresholds"][t] = 1  # Most aggressive
        await db_antinuke.set(str(ctx.guild.id), config)
        await ctx.send(embed=Embed(
            title="🚨 RAID MODE ACTIVATED",
            description="**Maximum protection enabled!**\nAll thresholds set to 1.\nPunishment: Instant Ban\nWhitelisted users are still safe.",
            color=0xEF4444
        ).set_footer(text="Use !antinuke config to customize"))

    @antinuke_group.command(name="reset")
    @commands.has_permissions(administrator=True)
    async def antinuke_reset(self, ctx):
        """Reset anti-nuke to defaults."""
        await db_antinuke.delete(str(ctx.guild.id))
        await ctx.send(embed=success_embed("🔄 Anti-nuke configuration reset to defaults!"))

    # ==============================================
    # TICKET COMMANDS
    # ==============================================
    @commands.group(name="ticket", aliases=["tickets"], invoke_without_command=True)
    async def ticket_group(self, ctx):
        """Ticket system management."""
        cfg = await db_guilds.get(str(ctx.guild.id), {})
        ticket_cfg = cfg.get("tickets", {})
        tickets = await db_tickets.all()
        open_tickets = sum(1 for t in tickets.values() if t.get("guild_id") == ctx.guild.id and t.get("status") == "open")
        closed_tickets = sum(1 for t in tickets.values() if t.get("guild_id") == ctx.guild.id and t.get("status") == "closed")

        embed = Embed(title="🎫 Ticket System", color=LYTRIX_COLOR)
        embed.add_field(name="Status", value="✅ Active" if ticket_cfg.get("enabled", True) else "❌ Disabled", inline=True)
        embed.add_field(name="Open Tickets", value=str(open_tickets), inline=True)
        embed.add_field(name="Total Closed", value=str(closed_tickets), inline=True)
        if ticket_cfg.get("support_role"):
            role = ctx.guild.get_role(int(ticket_cfg["support_role"]))
            embed.add_field(name="Support Role", value=role.mention if role else "Deleted", inline=True)
        if ticket_cfg.get("category"):
            cat = ctx.guild.get_channel(int(ticket_cfg["category"]))
            embed.add_field(name="Category", value=cat.name if cat else "Deleted", inline=True)
        embed.set_footer(text="Lytrix Tickets • !help tickets for commands")
        await ctx.send(embed=embed)

    @ticket_group.command(name="setup")
    @commands.has_permissions(administrator=True)
    async def ticket_setup(self, ctx):
        """Interactive ticket setup wizard."""
        cfg = await db_guilds.get(str(ctx.guild.id), {})
        ticket_cfg = cfg.get("tickets", {})

        questions = [
            ("What category should tickets be created in? (mention or ID, type 'skip' for none)", "category"),
            ("What role should have access to tickets? (mention or ID)", "support_role"),
            ("Where should ticket logs/transcripts go? (mention channel)", "log_channel"),
            ("What should the ticket panel title be?", "panel_title"),
        ]

        embed = Embed(title="🎫 Ticket Setup Wizard", description="Answer the following questions to setup tickets.\nType `cancel` to abort.", color=LYTRIX_COLOR)
        embed.set_footer(text="Lytrix Tickets • Made by Reon")
        await ctx.send(embed=embed)

        for question, key in questions:
            await ctx.send(embed=make_embed(title="Setup", description=question, color=LYTRIX_COLOR2))
            try:
                msg = await self.bot.wait_for(
                    'message',
                    timeout=120,
                    check=lambda m: m.author == ctx.author and m.channel == ctx.channel
                )
                if msg.content.lower() == 'cancel':
                    await ctx.send(embed=warn_embed("Setup cancelled."))
                    return
                if msg.content.lower() == 'skip':
                    continue

                if key == "category":
                    cat = await commands.TextChannelConverter().convert(ctx, msg.content) if msg.content.isdigit() else discord.utils.get(ctx.guild.categories, name=msg.content)
                    if not cat:
                        try:
                            cat_id = int(msg.content.strip('<#>'))
                            cat = ctx.guild.get_channel(cat_id)
                        except:
                            pass
                    ticket_cfg[key] = str(cat.id) if cat else None
                elif key in ("support_role",):
                    try:
                        role = await commands.RoleConverter().convert(ctx, msg.content)
                        ticket_cfg[key] = str(role.id)
                    except:
                        await ctx.send(embed=error_embed("Invalid role! Skipping..."))
                elif key == "log_channel":
                    try:
                        ch = await commands.TextChannelConverter().convert(ctx, msg.content)
                        ticket_cfg[key] = str(ch.id)
                    except:
                        await ctx.send(embed=error_embed("Invalid channel! Skipping..."))
                elif key == "panel_title":
                    ticket_cfg[key] = msg.content[:256]

            except asyncio.TimeoutError:
                await ctx.send(embed=warn_embed("Setup timed out. Use `!ticket setup` to restart."))
                return

        ticket_cfg["enabled"] = True
        cfg["tickets"] = ticket_cfg
        await db_guilds.set(str(ctx.guild.id), cfg)
        await ctx.send(embed=success_embed("✅ Ticket system configured! Use `!ticket panel #channel` to send the panel."))

    @ticket_group.command(name="panel")
    @commands.has_permissions(administrator=True)
    async def ticket_panel(self, ctx, *, channel: discord.TextChannel = None):
        """Send the ticket creation panel."""
        channel = channel or ctx.channel
        cfg = await db_guilds.get(str(ctx.guild.id), {})
        ticket_cfg = cfg.get("tickets", {})

        embed = Embed(
            title=ticket_cfg.get("panel_title", "🎫 Lytrix Support Tickets"),
            description=(
                "Need help? Create a ticket and our support team will assist you!\n\n"
                "**How to get support:**\n"
                "🎫 Click the **Create Ticket** button below\n"
                "📋 Click **Support Info** for more details\n\n"
                "> Please be patient — a staff member will assist you as soon as possible.\n"
                "> Abusing the ticket system may result in punishment."
            ),
            color=LYTRIX_COLOR
        )
        embed.set_footer(text="Lytrix Tickets • Made by Reon")
        embed.set_thumbnail(url="https://i.imgur.com/6V7sH4o.png")

        view = TicketView(self.bot)
        await channel.send(embed=embed, view=view)
        if channel != ctx.channel:
            await ctx.send(embed=success_embed(f"✅ Ticket panel sent to {channel.mention}"))

    @ticket_group.command(name="close")
    async def ticket_close(self, ctx):
        """Close the current ticket."""
        ticket_data = await db_tickets.get(str(ctx.channel.id), {})
        if not ticket_data or ticket_data.get("status") != "open":
            await ctx.send(embed=error_embed("This is not an open ticket!"))
            return

        ticket_data["status"] = "closed"
        ticket_data["closed_at"] = time.time()
        ticket_data["closed_by"] = ctx.author.id
        await db_tickets.set(str(ctx.channel.id), ticket_data)

        embed = Embed(title="🔒 Ticket Closed", description=f"Closed by {ctx.author.mention}", color=0xEF4444)
        embed.set_footer(text="Lytrix Tickets • Made by Reon")
        await ctx.send(embed=embed)

    @ticket_group.command(name="add")
    @commands.has_permissions(manage_channels=True)
    async def ticket_add(self, ctx, *, member: discord.Member):
        """Add a user to the ticket."""
        await ctx.channel.set_permissions(member, read_messages=True, send_messages=True)
        await ctx.send(embed=success_embed(f"➕ Added {member.mention} to the ticket!"))

    @ticket_group.command(name="remove")
    @commands.has_permissions(manage_channels=True)
    async def ticket_remove(self, ctx, *, member: discord.Member):
        """Remove a user from the ticket."""
        await ctx.channel.set_permissions(member, overwrite=None)
        await ctx.send(embed=success_embed(f"➖ Removed {member.mention} from the ticket!"))

    @ticket_group.command(name="rename")
    @commands.has_permissions(manage_channels=True)
    async def ticket_rename(self, ctx, *, name: str):
        """Rename the ticket."""
        await ctx.channel.edit(name=name[:100])
        await ctx.send(embed=success_embed(f"✅ Ticket renamed to **{name[:100]}**"))

    @ticket_group.command(name="delete")
    @commands.has_permissions(administrator=True)
    async def ticket_delete(self, ctx):
        """Force delete a ticket."""
        await ctx.send(embed=warn_embed("Deleting ticket in 3 seconds..."))
        await asyncio.sleep(3)
        try:
            await ctx.channel.delete(reason=f"Ticket deleted by {ctx.author}")
        except:
            pass

    @ticket_group.command(name="transcript")
    @commands.has_permissions(manage_channels=True)
    async def ticket_transcript(self, ctx):
        """Save ticket transcript."""
        ticket_data = await db_tickets.get(str(ctx.channel.id), {})
        if ticket_data:
            await self.bot.ticket_manager.save_transcript(ctx.channel, ticket_data)
            await ctx.send(embed=success_embed("📝 Transcript saved!"))
        else:
            await ctx.send(embed=error_embed("Not a ticket channel!"))

    @ticket_group.command(name="mytickets")
    async def ticket_mytickets(self, ctx):
        """View your tickets."""
        tickets = await db_tickets.all()
        user_tickets = [
            (k, v) for k, v in tickets.items()
            if v.get("user_id") == ctx.author.id and v.get("guild_id") == ctx.guild.id
        ]
        if not user_tickets:
            await ctx.send(embed=make_embed(title="🎫 My Tickets", description="You have no tickets.", color=LYTRIX_COLOR))
            return

        embed = Embed(title="🎫 My Tickets", color=LYTRIX_COLOR)
        for k, t in sorted(user_tickets, key=lambda x: x[1].get('created_at', 0), reverse=True)[:10]:
            status_emoji = {"open": "🟢", "closed": "🔴", "deleted": "⚫"}
            ch = ctx.guild.get_channel(t.get('channel_id', 0))
            embed.add_field(
                name=f"#{t.get('ticket_number', '??'):04d} {status_emoji.get(t.get('status'), '❓')}",
                value=f"Channel: {ch.mention if ch else 'Deleted'}\nCreated: <t:{int(t.get('created_at', 0))}:R>\nStatus: **{t.get('status', 'unknown').title()}**",
                inline=False
            )
        embed.set_footer(text="Lytrix Tickets • Made by Reon")
        await ctx.send(embed=embed)

    @ticket_group.command(name="stats")
    @commands.has_permissions(manage_channels=True)
    async def ticket_stats(self, ctx):
        """View ticket statistics."""
        tickets = await db_tickets.all()
        guild_tickets = [t for t in tickets.values() if t.get("guild_id") == ctx.guild.id]
        open_t = [t for t in guild_tickets if t.get("status") == "open"]
        closed_t = [t for t in guild_tickets if t.get("status") == "closed"]

        embed = Embed(title="📊 Ticket Statistics", color=LYTRIX_COLOR)
        embed.add_field(name="Total Tickets", value=str(len(guild_tickets)), inline=True)
        embed.add_field(name="Open", value=str(len(open_t)), inline=True)
        embed.add_field(name="Closed", value=str(len(closed_t)), inline=True)

        if closed_t:
            avg_close = sum(t.get("closed_at", t.get("created_at", 0)) - t.get("created_at", 0) for t in closed_t) / len(closed_t)
            embed.add_field(name="Avg Resolution", value=format_time(avg_close), inline=True)

        user_counts = Counter(t.get("user_id") for t in guild_tickets)
        if user_counts:
            top = user_counts.most_common(1)[0]
            embed.add_field(name="Most Tickets", value=f"<@{top[0]}> ({top[1]})", inline=True)

        embed.set_footer(text="Lytrix Tickets • Made by Reon")
        await ctx.send(embed=embed)

    @ticket_group.command(name="category")
    @commands.has_permissions(administrator=True)
    async def ticket_category(self, ctx, *, category: discord.CategoryChannel):
        """Set ticket category."""
        cfg = await db_guilds.get(str(ctx.guild.id), {})
        ticket_cfg = cfg.get("tickets", {})
        ticket_cfg["category"] = str(category.id)
        cfg["tickets"] = ticket_cfg
        await db_guilds.set(str(ctx.guild.id), cfg)
        await ctx.send(embed=success_embed(f"Ticket category set to **{category.name}**"))

    @ticket_group.command(name="role")
    @commands.has_permissions(administrator=True)
    async def ticket_role(self, ctx, *, role: discord.Role):
        """Set support role for tickets."""
        cfg = await db_guilds.get(str(ctx.guild.id), {})
        ticket_cfg = cfg.get("tickets", {})
        ticket_cfg["support_role"] = str(role.id)
        cfg["tickets"] = ticket_cfg
        await db_guilds.set(str(ctx.guild.id), cfg)
        await ctx.send(embed=success_embed(f"Support role set to {role.mention}"))

    @ticket_group.command(name="log")
    @commands.has_permissions(administrator=True)
    async def ticket_log(self, ctx, *, channel: discord.TextChannel):
        """Set ticket log channel."""
        cfg = await db_guilds.get(str(ctx.guild.id), {})
        ticket_cfg = cfg.get("tickets", {})
        ticket_cfg["log_channel"] = str(channel.id)
        cfg["tickets"] = ticket_cfg
        await db_guilds.set(str(ctx.guild.id), cfg)
        await ctx.send(embed=success_embed(f"Ticket logs will be sent to {channel.mention}"))

    @ticket_group.command(name="limit")
    @commands.has_permissions(administrator=True)
    async def ticket_limit(self, ctx, limit: int):
        """Set max tickets per user."""
        cfg = await db_guilds.get(str(ctx.guild.id), {})
        ticket_cfg = cfg.get("tickets", {})
        ticket_cfg["max_per_user"] = limit
        cfg["tickets"] = ticket_cfg
        await db_guilds.set(str(ctx.guild.id), cfg)
        await ctx.send(embed=success_embed(f"Max tickets per user set to **{limit}**"))

    # ==============================================
    # FUN COMMANDS
    # ==============================================
    @commands.command(name="8ball", aliases=["eightball"])
    async def eightball_cmd(self, ctx, *, question: str):
        """Ask the magic 8-ball."""
        await ctx.send(embed=make_embed(title="🎱 8-Ball", description=f"**Question:** {question}\n**Answer:** {random.choice(EIGHT_BALL_RESPONSES)}", color=LYTRIX_COLOR))

    @commands.command(name="coinflip", aliases=["cf", "coin"])
    async def coinflip_cmd(self, ctx):
        """Flip a coin."""
        result = random.choice(["Heads", "Tails"])
        emoji = {"Heads": "🪙", "Tails": "🪙"}
        await ctx.send(embed=make_embed(title="🪙 Coin Flip", description=f"**{result}!** {emoji[result]}", color=LYTRIX_COLOR2))

    @commands.command(name="roll", aliases=["dice"])
    async def roll_cmd(self, ctx, sides: int = 6):
        """Roll dice. Default: 6 sides."""
        result = random.randint(1, max(1, sides))
        await ctx.send(embed=make_embed(title="🎲 Dice Roll", description=f"Rolled a **{result}** (1-{sides})", color=LYTRIX_COLOR))

    @commands.command(name="choose", aliases=["pick"])
    async def choose_cmd(self, ctx, *, options: str):
        """Choose between comma-separated options."""
        opts = [o.strip() for o in options.split(",") if o.strip()]
        if len(opts) < 2:
            await ctx.send(embed=error_embed("Give me at least 2 options separated by commas!"))
            return
        choice = random.choice(opts)
        await ctx.send(embed=make_embed(title="🤔 I Choose...", description=f"**{choice}**", color=LYTRIX_COLOR))

    @commands.command(name="rps", aliases=["rockpaperscissors"])
    async def rps_cmd(self, ctx, choice: str):
        """Rock Paper Scissors."""
        choices = {"rock": "🪨", "paper": "📄", "scissors": "✂️", "r": "🪨", "p": "📄", "s": "✂️"}
        choice = choice.lower()
        if choice not in choices:
            await ctx.send(embed=error_embed("Choose: rock (r), paper (p), or scissors (s)!"))
            return

        user_choice = {"r": "rock", "p": "paper", "s": "scissors"}.get(choice, choice)
        bot_choice = random.choice(["rock", "paper", "scissors"])
        user_emoji = choices[user_choice]
        bot_emoji = choices[bot_choice]

        if user_choice == bot_choice:
            result = "It's a tie!"
        elif (user_choice == "rock" and bot_choice == "scissors") or \
             (user_choice == "paper" and bot_choice == "rock") or \
             (user_choice == "scissors" and bot_choice == "paper"):
            result = "You win! 🎉"
        else:
            result = "I win! 😎"

        await ctx.send(embed=make_embed(
            title="🎮 RPS",
            description=f"You: {user_emoji} **{user_choice.title()}**\nBot: {bot_emoji} **{bot_choice.title()}**\n\n**{result}**",
            color=LYTRIX_COLOR
        ))

    @commands.command(name="hug")
    async def hug_cmd(self, ctx, *, member: discord.Member):
        """Hug someone."""
        await ctx.send(embed=make_embed(title="🤗 Hug!", description=f"{ctx.author.mention} hugs {member.mention}! So wholesome! 🥰", color=LYTRIX_COLOR2))

    @commands.command(name="kiss")
    async def kiss_cmd(self, ctx, *, member: discord.Member):
        """Kiss someone."""
        await ctx.send(embed=make_embed(title="💋 Kiss!", description=f"{ctx.author.mention} kisses {member.mention}! Ooh la la! 💕", color=LYTRIX_COLOR2))

    @commands.command(name="slap")
    async def slap_cmd(self, ctx, *, member: discord.Member):
        """Slap someone."""
        await ctx.send(embed=make_embed(title="👋 Slap!", description=f"{ctx.author.mention} slaps {member.mention}! Ouch! 🫢", color=LYTRIX_COLOR2))

    @commands.command(name="pat")
    async def pat_cmd(self, ctx, *, member: discord.Member):
        """Pat someone."""
        await ctx.send(embed=make_embed(title="🤚 Pat!", description=f"{ctx.author.mention} pats {member.mention}! Good job! 🌟", color=LYTRIX_COLOR2))

    @commands.command(name="cuddle")
    async def cuddle_cmd(self, ctx, *, member: discord.Member):
        """Cuddle someone."""
        await ctx.send(embed=make_embed(title="🥰 Cuddle!", description=f"{ctx.author.mention} cuddles {member.mention}! So cozy! 🧸", color=LYTRIX_COLOR2))

    @commands.command(name="ship")
    async def ship_cmd(self, ctx, member1: discord.Member, member2: discord.Member = None):
        """Ship two users."""
        member2 = member2 or ctx.author
        combined = (member1.id + member2.id + ctx.guild.id) % 101
        bar = "❤️" * (combined // 10) + "🖤" * (10 - combined // 10)
        await ctx.send(embed=make_embed(
            title="💝 Ship Meter",
            description=f"**{member1.name}** x **{member2.name}**\n\n{bar}\n**{combined}%** compatibility!",
            color=LYTRIX_COLOR2
        ))

    @commands.command(name="howgay")
    async def howgay_cmd(self, ctx, *, member: discord.Member = None):
        """How gay is someone?"""
        member = member or ctx.author
        percent = ((member.id + ctx.guild.id) % 101)
        await ctx.send(embed=make_embed(title="🏳️‍🌈 Gay Meter", description=f"{member.mention} is **{percent}%** gay! 🏳️‍🌈", color=LYTRIX_COLOR2))

    @commands.command(name="simp")
    async def simp_cmd(self, ctx, *, member: discord.Member = None):
        """Simp rate."""
        member = member or ctx.author
        percent = ((member.id * 7 + ctx.guild.id * 3) % 101)
        await ctx.send(embed=make_embed(title="😍 Simp Rate", description=f"{member.mention} is **{percent}%** simp! 😍", color=LYTRIX_COLOR2))

    @commands.command(name="coolrate")
    async def coolrate_cmd(self, ctx, *, member: discord.Member = None):
        """Coolness rating."""
        member = member or ctx.author
        percent = ((member.id * 13 + 42) % 101)
        await ctx.send(embed=make_embed(title="😎 Coolness", description=f"{member.mention} is **{percent}%** cool! 😎", color=LYTRIX_COLOR2))

    @commands.command(name="iq")
    async def iq_cmd(self, ctx, *, member: discord.Member = None):
        """IQ test."""
        member = member or ctx.author
        iq = ((member.id * 17 + ctx.guild.id * 11) % 101) + 50
        emoji = "🧠" if iq > 100 else "🤔" if iq > 80 else "🤪"
        await ctx.send(embed=make_embed(title="🧠 IQ Test", description=f"{member.mention} has an IQ of **{iq}** {emoji}", color=LYTRIX_COLOR2))

    @commands.command(name="pp")
    async def pp_cmd(self, ctx, *, member: discord.Member = None):
        """PP size (for fun)."""
        member = member or ctx.author
        size = ((member.id * 31 + ctx.guild.id * 7) % 20) + 1
        bar = "=" * size
        await ctx.send(embed=make_embed(title="🍆 PP Size", description=f"{member.mention}'s PP:\n8{bar}D\n**{size} inches**", color=LYTRIX_COLOR2))

    @commands.command(name="fact")
    async def fact_cmd(self, ctx):
        """Random fact."""
        facts = [
            "Honey never spoils. Archaeologists have found 3000-year-old honey that's still edible!",
            "Octopuses have three hearts and blue blood.",
            "Bananas are berries, but strawberries aren't!",
            "A day on Venus is longer than a year on Venus.",
            "The Eiffel Tower can be 15 cm taller during summer due to thermal expansion.",
            "Sharks existed before trees.",
            "There are more stars in the universe than grains of sand on Earth.",
            "Wombat poop is cube-shaped.",
            "Butterflies taste with their feet.",
            "A group of flamingos is called a 'flamboyance'.",
        ]
        await ctx.send(embed=make_embed(title="🤓 Random Fact", description=random.choice(facts), color=LYTRIX_COLOR))

    @commands.command(name="quote")
    async def quote_cmd(self, ctx):
        """Inspirational quote."""
        quotes = [
            "\"The only way to do great work is to love what you do.\" — Steve Jobs",
            "\"Life is what happens when you're busy making other plans.\" — John Lennon",
            "\"The future belongs to those who believe in the beauty of their dreams.\" — Eleanor Roosevelt",
            "\"It does not matter how slowly you go as long as you do not stop.\" — Confucius",
            "\"You miss 100% of the shots you don't take.\" — Wayne Gretzky",
        ]
        await ctx.send(embed=make_embed(title="💬 Quote", description=random.choice(quotes), color=LYTRIX_COLOR))

    @commands.command(name="joke")
    async def joke_cmd(self, ctx):
        """Random joke."""
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "What do you call a fake noodle? An impasta!",
            "Why did the scarecrow win an award? He was outstanding in his field!",
            "What do you call a fish with no eyes? Fsh!",
            "Why don't skeletons fight each other? They don't have the guts!",
        ]
        await ctx.send(embed=make_embed(title="😂 Joke", description=random.choice(jokes), color=LYTRIX_COLOR))

    @commands.command(name="meme")
    async def meme_cmd(self, ctx):
        """Random meme (placeholder)."""
        await ctx.send(embed=make_embed(title="🤣 Meme", description="Memes coming soon! Use Reddit API for memes.", color=LYTRIX_COLOR))

    @commands.command(name="roast")
    async def roast_cmd(self, ctx, *, member: discord.Member = None):
        """Roast someone."""
        member = member or ctx.author
        roasts = [
            "You're not stupid; you just have bad luck thinking.",
            "I'd agree with you but then we'd both be wrong.",
            "You bring everyone so much joy—when you leave the room.",
            "You're like a cloud. When you disappear, it's a beautiful day.",
            "Somewhere out there, a tree is working hard to replace the oxygen you waste.",
        ]
        await ctx.send(embed=make_embed(title="🔥 Roast!", description=f"{member.mention}: **{random.choice(roasts)}**", color=0xEF4444))

    @commands.command(name="reverse")
    async def reverse_cmd(self, ctx, *, text: str):
        """Reverse text."""
        await ctx.send(embed=make_embed(title="🔄 Reversed", description=text[::-1][:2000], color=LYTRIX_COLOR))

    @commands.command(name="mock")
    async def mock_cmd(self, ctx, *, text: str):
        """Mocking text."""
        mocked = "".join(c.upper() if i % 2 else c.lower() for i, c in enumerate(text))
        await ctx.send(embed=make_embed(title="🤪 Mocked", description=mocked[:2000], color=LYTRIX_COLOR))

    @commands.command(name="clap")
    async def clap_cmd(self, ctx, *, text: str):
        """Clap text."""
        clapped = " 👏 ".join(text.split()) + " 👏"
        await ctx.send(embed=make_embed(title="👏 Clapped", description=clapped[:2000], color=LYTRIX_COLOR))

    @commands.command(name="say")
    async def say_cmd(self, ctx, *, text: str):
        """Make the bot say something."""
        await ctx.send(text, allowed_mentions=discord.AllowedMentions.none())
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name="embed")
    async def embed_cmd(self, ctx, title: str, *, description: str):
        """Create a custom embed."""
        embed = Embed(title=title, description=description, color=LYTRIX_COLOR)
        embed.set_footer(text=f"Created by {ctx.author.name} • Lytrix")
        await ctx.send(embed=embed)

    @commands.command(name="poll")
    async def poll_cmd(self, ctx, *, args: str):
        """Create a poll. Format: question | option1, option2, ..."""
        parts = args.split("|")
        if len(parts) < 2:
            await ctx.send(embed=error_embed("Format: `!poll Question | Option1, Option2, ...`"))
            return

        question = parts[0].strip()
        options = [o.strip() for o in parts[1].split(",") if o.strip()][:10]
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        embed = Embed(title=f"📊 Poll: {question}", color=LYTRIX_COLOR)
        for i, opt in enumerate(options):
            embed.add_field(name=f"{emojis[i]} {opt}", value="\u200b", inline=False)
        embed.set_footer(text=f"By {ctx.author.name} • Lytrix Polls")

        msg = await ctx.send(embed=embed)
        for i in range(len(options)):
            try:
                await msg.add_reaction(emojis[i])
            except:
                pass

    @commands.command(name="snipe")
    async def snipe_cmd(self, ctx):
        """Snipe last deleted message."""
        sniped = self.bot.snipes.get(ctx.channel.id)
        if not sniped:
            await ctx.send(embed=error_embed("Nothing to snipe!"))
            return

        embed = Embed(title="🎯 Sniped!", description=sniped.get("content", "") or "*No content*", color=LYTRIX_COLOR, timestamp=sniped.get("time"))
        embed.add_field(name="Author", value=sniped.get("author", "Unknown"))
        if sniped.get("attachment"):
            embed.set_image(url=sniped["attachment"])
            embed.add_field(name="Attachment", value=sniped["attachment"], inline=False)
        embed.set_footer(text="Lytrix Snipe • Made by Reon")
        await ctx.send(embed=embed)

    @commands.command(name="editsnipe")
    async def editsnipe_cmd(self, ctx):
        """Snipe last edited message."""
        sniped = self.bot.edit_snipes.get(ctx.channel.id)
        if not sniped:
            await ctx.send(embed=error_embed("Nothing to snipe!"))
            return

        embed = Embed(title="✏️ Edit Sniped!", color=LYTRIX_COLOR, timestamp=sniped.get("time"))
        embed.add_field(name="Before", value=sniped.get("before", "*No content*")[:1000] or "*No content*", inline=False)
        embed.add_field(name="After", value=sniped.get("after", "*No content*")[:1000] or "*No content*", inline=False)
        embed.add_field(name="Author", value=sniped.get("author", "Unknown"))
        embed.set_footer(text="Lytrix Edit Snipe • Made by Reon")
        await ctx.send(embed=embed)

    @commands.command(name="afk")
    async def afk_cmd(self, ctx, *, reason: str = "AFK"):
        """Set AFK status."""
        self.bot.afk_users[ctx.author.id] = (reason, time.time())
        await ctx.send(embed=success_embed(f"{ctx.author.mention} is now AFK: **{reason}**"))

    @commands.command(name="remind", aliases=["reminder", "remindme"])
    async def remind_cmd(self, ctx, duration: str, *, message: str = "Reminder!"):
        """Set a reminder. Duration: 10m, 2h, 1d."""
        seconds = self._parse_duration(duration)
        if seconds == 0:
            await ctx.send(embed=error_embed("Invalid duration! Use: 10m, 2h, 1d"))
            return
        if seconds > 2592000:  # 30 days
            await ctx.send(embed=error_embed("Max reminder duration: 30 days"))
            return

        remind_id = f"{ctx.author.id}:{int(time.time())}"
        await db_reminders.set(remind_id, {
            "user_id": ctx.author.id,
            "message": message,
            "time": time.time() + seconds,
            "channel_id": ctx.channel.id,
            "guild_id": ctx.guild.id,
        })

        await ctx.send(embed=success_embed(
            f"⏰ Reminder set! I'll remind you in **{format_time(seconds)}**.\n"
            f"Message: {message}"
        ))

    @commands.command(name="timer")
    async def timer_cmd(self, ctx, seconds: int):
        """Start a timer."""
        if seconds > 3600:
            await ctx.send(embed=error_embed("Max timer: 1 hour"))
            return
        msg = await ctx.send(embed=make_embed(title="⏱️ Timer", description=f"Timer started: **{seconds}s**", color=LYTRIX_COLOR))
        await asyncio.sleep(seconds)
        await msg.reply(f"⏰ **{ctx.author.mention}** Timer done! ({seconds}s)")

    @commands.command(name="firstmsg", aliases=["firstmessage"])
    async def firstmsg_cmd(self, ctx):
        """Get first message in channel."""
        async for msg in ctx.channel.history(oldest_first=True, limit=1):
            embed = Embed(title="📜 First Message", description=msg.content or "*No content*", color=LYTRIX_COLOR)
            embed.add_field(name="Author", value=msg.author.mention, inline=True)
            embed.add_field(name="Date", value=f"<t:{int(msg.created_at.timestamp())}:F>", inline=True)
            embed.add_field(name="Jump", value=f"[Click to view]({msg.jump_url})", inline=True)
            await ctx.send(embed=embed)
            return
        await ctx.send(embed=error_embed("No messages found!"))

    # ==============================================
    # GIVEAWAY COMMANDS
    # ==============================================
    @commands.command(name="giveaway", aliases=["gstart", "gt"])
    @commands.has_permissions(manage_guild=True)
    async def giveaway_cmd(self, ctx, duration: str = None, winners: int = 1, *, prize: str = "Prize"):
        """Start a giveaway. Usage: !giveaway <duration> <winners> <prize>"""
        if not duration:
            await ctx.send(embed=error_embed("Usage: `!giveaway <duration> <winners> <prize>`\nExample: `!giveaway 1h 1 Nitro Classic`"))
            return

        seconds = self._parse_duration(duration)
        if seconds == 0 or seconds > 2592000:
            await ctx.send(embed=error_embed("Invalid duration! Use 1m, 1h, 1d (max 30 days)"))
            return

        embed = Embed(title="🎉 Giveaway!", color=LYTRIX_COLOR2)
        embed.add_field(name="Prize", value=prize, inline=True)
        embed.add_field(name="Winners", value=str(winners), inline=True)
        embed.add_field(name="Ends", value=f"<t:{int(time.time() + seconds)}:R>", inline=True)
        embed.add_field(name="Host", value=ctx.author.mention, inline=True)
        embed.set_footer(text="React 🎉 to enter! • Lytrix Giveaways")

        msg = await ctx.send(embed=embed)
        await msg.add_reaction("🎉")

        giveaway_id = str(msg.id)
        await db_giveaways.set(giveaway_id, {
            "guild_id": ctx.guild.id,
            "channel_id": ctx.channel.id,
            "message_id": msg.id,
            "prize": prize,
            "winners": winners,
            "end_time": time.time() + seconds,
            "host_id": ctx.author.id,
            "participants": [],
            "ended": False,
            "winners_list": [],
        })

    @commands.command(name="reroll")
    @commands.has_permissions(manage_guild=True)
    async def reroll_cmd(self, ctx, message_id: str):
        """Reroll a giveaway winner."""
        try:
            msg_id = int(message_id)
        except:
            await ctx.send(embed=error_embed("Invalid message ID!"))
            return

        giveaway = await db_giveaways.get(str(msg_id), {})
        if not giveaway:
            await ctx.send(embed=error_embed("Giveaway not found!"))
            return

        participants = giveaway.get("participants", [])
        if not participants:
            await ctx.send(embed=error_embed("No participants to reroll!"))
            return

        winner = random.choice(participants)
        await ctx.send(f"🎉 **New Winner:** <@{winner}>! Congratulations!\nPrize: **{giveaway.get('prize', 'Prize')}**")

    @commands.command(name="endgiveaway", aliases=["gend", "gendgiveaway"])
    @commands.has_permissions(manage_guild=True)
    async def endgiveaway_cmd(self, ctx, message_id: str):
        """End a giveaway early."""
        try:
            msg_id = int(message_id)
        except:
            await ctx.send(embed=error_embed("Invalid message ID!"))
            return

        giveaway = await db_giveaways.get(str(msg_id), {})
        if not giveaway:
            await ctx.send(embed=error_embed("Giveaway not found!"))
            return

        giveaway["end_time"] = time.time() - 1
        await db_giveaways.set(str(msg_id), giveaway)
        await self.bot._end_giveaway(str(msg_id), giveaway)
        await ctx.send(embed=success_embed("Giveaway ended!"))

    # ==============================================
    # UTILITY COMMANDS
    # ==============================================
    @commands.command(name="calc", aliases=["math", "calculate"])
    async def calc_cmd(self, ctx, *, expression: str):
        """Calculate a math expression."""
        try:
            expression = expression.replace("×", "*").replace("÷", "/").replace("^", "**")
            allowed = set("0123456789+-*/().% ")
            cleaned = "".join(c for c in expression if c in allowed)
            result = eval(cleaned)
            await ctx.send(embed=make_embed(title="🧮 Calculator", description=f"```\n{expression} = {result}\n```", color=LYTRIX_COLOR))
        except:
            await ctx.send(embed=error_embed("Invalid expression!"))

    @commands.command(name="weather")
    async def weather_cmd(self, ctx, *, city: str):
        """Get weather (needs API key)."""
        await ctx.send(embed=make_embed(
            title=f"🌤️ Weather: {city}",
            description="Weather feature requires an OpenWeatherMap API key.\nSet it up in config!",
            color=LYTRIX_COLOR
        ))

    @commands.command(name="translate")
    async def translate_cmd(self, ctx, lang: str, *, text: str):
        """Translate text (needs API)."""
        await ctx.send(embed=make_embed(
            title="🌐 Translate",
            description=f"Translating to `{lang}`... (Requires Google Translate API key)",
            color=LYTRIX_COLOR
        ))

    @commands.command(name="define")
    async def define_cmd(self, ctx, *, word: str):
        """Define a word."""
        await ctx.send(embed=make_embed(
            title=f"📚 Define: {word}",
            description="Dictionary feature requires API integration.\nComing soon!",
            color=LYTRIX_COLOR
        ))

    @commands.command(name="urban")
    async def urban_cmd(self, ctx, *, word: str):
        """Urban dictionary lookup."""
        await ctx.send(embed=make_embed(
            title=f"📖 Urban: {word}",
            description="Urban Dictionary search coming soon!",
            color=LYTRIX_COLOR
        ))

    @commands.command(name="wiki")
    async def wiki_cmd(self, ctx, *, query: str):
        """Search Wikipedia."""
        await ctx.send(embed=make_embed(
            title=f"📚 Wikipedia: {query}",
            description=f"Searching Wikipedia for `{query}`...\nhttps://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
            color=LYTRIX_COLOR
        ))

    @commands.command(name="qr")
    async def qr_cmd(self, ctx, *, text: str):
        """Generate QR code link."""
        encoded = text.replace(" ", "%20")
        await ctx.send(embed=make_embed(
            title="📱 QR Code",
            description=f"[Click for QR Code](https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={encoded})",
            color=LYTRIX_COLOR,
            image=f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={encoded}"
        ))

    @commands.command(name="members", aliases=["membercount"])
    async def members_cmd(self, ctx):
        """View member counts."""
        guild = ctx.guild
        total = guild.member_count
        humans = sum(1 for m in guild.members if not m.bot)
        bots = total - humans
        online = sum(1 for m in guild.members if str(m.status) == "online")
        idle = sum(1 for m in guild.members if str(m.status) == "idle")
        dnd = sum(1 for m in guild.members if str(m.status) == "dnd")
        offline = total - online - idle - dnd

        embed = Embed(title=f"👥 {guild.name} Members", color=LYTRIX_COLOR)
        embed.add_field(name="Total", value=str(total), inline=True)
        embed.add_field(name="Humans", value=str(humans), inline=True)
        embed.add_field(name="Bots", value=str(bots), inline=True)
        embed.add_field(name="🟢 Online", value=str(online), inline=True)
        embed.add_field(name="🌙 Idle", value=str(idle), inline=True)
        embed.add_field(name="🔴 DnD", value=str(dnd), inline=True)
        embed.add_field(name="⚫ Offline", value=str(offline), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="roles")
    async def roles_cmd(self, ctx):
        """List all server roles."""
        roles = [r.mention for r in reversed(ctx.guild.roles) if r != ctx.guild.default_role]
        embed = Embed(title=f"🎭 Roles ({len(roles)})", description=" ".join(roles[:50]) + ("..." if len(roles) > 50 else ""), color=LYTRIX_COLOR)
        await ctx.send(embed=embed)

    @commands.command(name="emojis", aliases=["emotes"])
    async def emojis_cmd(self, ctx):
        """List server emojis."""
        emojis = ctx.guild.emojis
        static = [str(e) for e in emojis if not e.animated]
        animated = [str(e) for e in emojis if e.animated]
        embed = Embed(title=f"😀 Emojis ({len(emojis)})", color=LYTRIX_COLOR)
        if static:
            embed.add_field(name=f"Static ({len(static)})", value=" ".join(static[:25]) + ("..." if len(static) > 25 else ""), inline=False)
        if animated:
            embed.add_field(name=f"Animated ({len(animated)})", value=" ".join(animated[:25]) + ("..." if len(animated) > 25 else ""), inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="boosters")
    async def boosters_cmd(self, ctx):
        """List server boosters."""
        boosters = [m.mention for m in ctx.guild.premium_subscribers]
        if boosters:
            embed = Embed(title=f"🚀 Boosters ({len(boosters)})", description="\n".join(boosters[:20]) + ("..." if len(boosters) > 20 else ""), color=LYTRIX_COLOR2)
        else:
            embed = make_embed(title="🚀 Boosters", description="No boosters yet!", color=LYTRIX_COLOR2)
        embed.set_footer(text=f"Boost Level: {ctx.guild.premium_tier} • {ctx.guild.premium_subscription_count} boosts")
        await ctx.send(embed=embed)

    @commands.command(name="joined")
    async def joined_cmd(self, ctx, *, member: discord.Member = None):
        """When a member joined."""
        member = member or ctx.author
        await ctx.send(embed=make_embed(
            title="📅 Join Date",
            description=f"{member.mention} joined <t:{int(member.joined_at.timestamp())}:R>\nOn <t:{int(member.joined_at.timestamp())}:F>",
            color=LYTRIX_COLOR
        ))

    @commands.command(name="oldest")
    async def oldest_cmd(self, ctx):
        """Oldest member."""
        sorted_members = sorted(ctx.guild.members, key=lambda m: m.joined_at or datetime.datetime.max)
        if sorted_members:
            m = sorted_members[0]
            await ctx.send(embed=make_embed(
                title="👴 Oldest Member",
                description=f"{m.mention} joined <t:{int(m.joined_at.timestamp())}:R>",
                color=LYTRIX_COLOR
            ))

    @commands.command(name="newest")
    async def newest_cmd(self, ctx):
        """Newest member."""
        sorted_members = sorted(ctx.guild.members, key=lambda m: m.joined_at or datetime.datetime.min, reverse=True)
        if sorted_members:
            m = sorted_members[0]
            await ctx.send(embed=make_embed(
                title="👶 Newest Member",
                description=f"{m.mention} joined <t:{int(m.joined_at.timestamp())}:R>",
                color=LYTRIX_COLOR
            ))

    @commands.command(name="randomuser")
    async def randomuser_cmd(self, ctx):
        """Random member."""
        member = random.choice(ctx.guild.members)
        embed = Embed(title="🎯 Random User", description=member.mention, color=LYTRIX_COLOR)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Joined", value=f"<t:{int(member.joined_at.timestamp())}:R>")
        await ctx.send(embed=embed)

    @commands.command(name="emojisteal", aliases=["steal", "addemoji"])
    @commands.has_permissions(manage_emojis=True)
    async def emojisteal_cmd(self, ctx, emoji: str, *, name: str = None):
        """Steal an emoji and add to server."""
        emoji_id = None
        is_animated = False

        match = re.match(r'<a?:(\w+):(\d+)>', emoji)
        if match:
            name = name or match.group(1)
            emoji_id = int(match.group(2))
            is_animated = emoji.startswith('<a:')

        if not emoji_id:
            await ctx.send(embed=error_embed("Invalid emoji! Use a custom emoji."))
            return

        url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{'gif' if is_animated else 'png'}"
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    image_data = await resp.read()
            emoji = await ctx.guild.create_custom_emoji(name=name, image=image_data, reason=f"Stolen by {ctx.author}")
            await ctx.send(embed=success_embed(f"✅ Stolen emoji: {emoji}"))
        except Exception as e:
            await ctx.send(embed=error_embed(f"Failed: {str(e)[:200]}"))

    @commands.command(name="donate")
    async def donate_cmd(self, ctx):
        """Donation info."""
        await ctx.send(embed=make_embed(
            title="💖 Donate",
            description="Support Lytrix development!\n\n[Donate via PayPal](https://paypal.me/reon)\n[Buy Premium](https://reon.dev/lytrix/premium)\n\nThank you for your support! ❤️",
            color=LYTRIX_COLOR2
        ))

    @commands.command(name="setprefix")
    @commands.has_permissions(manage_guild=True)
    async def setprefix_cmd(self, ctx, prefix: str = BOT_PREFIX):
        """Set custom prefix for the server."""
        if len(prefix) > 5:
            await ctx.send(embed=error_embed("Prefix must be 5 characters or less!"))
            return
        cfg = await db_guilds.get(str(ctx.guild.id), {})
        cfg["prefix"] = prefix
        await db_guilds.set(str(ctx.guild.id), cfg)
        await ctx.send(embed=success_embed(f"Prefix set to **{prefix}**"))

    # ==============================================
    # AUTO MODERATION COMMANDS
    # ==============================================
    @commands.group(name="automod", aliases=["am", "automoderation"], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def automod_group(self, ctx):
        """Auto-moderation settings."""
        cfg = await db_automod.get(str(ctx.guild.id), {
            "enabled": False,
            "antispam": True,
            "antilinks": False,
            "antiinvite": False,
            "anticaps": False,
            "antighostping": True,
            "antimassmention": True,
            "badwords": [],
            "ignored_channels": [],
            "ignored_roles": [],
            "whitelisted_users": [],
            "punishment": "warn",
            "log_channel": None,
        })

        embed = Embed(title="🤖 AutoMod Settings", color=LYTRIX_COLOR)
        embed.add_field(name="Status", value="✅ Enabled" if cfg.get("enabled") else "❌ Disabled", inline=True)
        embed.add_field(name="Punishment", value=cfg.get("punishment", "warn").title(), inline=True)
        embed.add_field(name="Bad Words", value=str(len(cfg.get("badwords", []))), inline=True)
        embed.add_field(name="Anti-Spam", value="✅" if cfg.get("antispam") else "❌", inline=True)
        embed.add_field(name="Anti-Links", value="✅" if cfg.get("antilinks") else "❌", inline=True)
        embed.add_field(name="Anti-Invite", value="✅" if cfg.get("antiinvite") else "❌", inline=True)
        embed.add_field(name="Anti-Caps", value="✅" if cfg.get("anticaps") else "❌", inline=True)
        embed.add_field(name="Ghost Ping", value="✅" if cfg.get("antighostping") else "❌", inline=True)
        embed.set_footer(text="Lytrix AutoMod • !help automod for commands")
        await ctx.send(embed=embed)

    @automod_group.command(name="enable")
    @commands.has_permissions(administrator=True)
    async def automod_enable(self, ctx):
        cfg = await db_automod.get(str(ctx.guild.id), {})
        cfg["enabled"] = True
        await db_automod.set(str(ctx.guild.id), cfg)
        await ctx.send(embed=success_embed("✅ AutoMod enabled!"))

    @automod_group.command(name="disable")
    @commands.has_permissions(administrator=True)
    async def automod_disable(self, ctx):
        cfg = await db_automod.get(str(ctx.guild.id), {})
        cfg["enabled"] = False
        await db_automod.set(str(ctx.guild.id), cfg)
        await ctx.send(embed=success_embed("❌ AutoMod disabled!"))

    @automod_group.command(name="antispam")
    @commands.has_permissions(administrator=True)
    async def automod_antispam(self, ctx, state: str = "on"):
        cfg = await db_automod.get(str(ctx.guild.id), {})
        cfg["antispam"] = state.lower() in ("on", "true", "yes")
        await db_automod.set(str(ctx.guild.id), cfg)
        await ctx.send(embed=success_embed(f"Anti-spam: {'✅ ON' if cfg['antispam'] else '❌ OFF'}"))

    @automod_group.command(name="antilinks")
    @commands.has_permissions(administrator=True)
    async def automod_antilinks(self, ctx, state: str = "on"):
        cfg = await db_automod.get(str(ctx.guild.id), {})
        cfg["antilinks"] = state.lower() in ("on", "true", "yes")
        await db_automod.set(str(ctx.guild.id), cfg)
        await ctx.send(embed=success_embed(f"Anti-links: {'✅ ON' if cfg['antilinks'] else '❌ OFF'}"))

    @automod_group.command(name="antiinvite")
    @commands.has_permissions(administrator=True)
    async def automod_antiinvite(self, ctx, state: str = "on"):
        cfg = await db_automod.get(str(ctx.guild.id), {})
        cfg["antiinvite"] = state.lower() in ("on", "true", "yes")
        await db_automod.set(str(ctx.guild.id), cfg)
        await ctx.send(embed=success_embed(f"Anti-invite: {'✅ ON' if cfg['antiinvite'] else '❌ OFF'}"))

    @automod_group.command(name="anticaps")
    @commands.has_permissions(administrator=True)
    async def automod_anticaps(self, ctx, state: str = "on"):
        cfg = await db_automod.get(str(ctx.guild.id), {})
        cfg["anticaps"] = state.lower() in ("on", "true", "yes")
        await db_automod.set(str(ctx.guild.id), cfg)
        await ctx.send(embed=success_embed(f"Anti-caps: {'✅ ON' if cfg['anticaps'] else '❌ OFF'}"))

    @automod_group.command(name="badwords")
    @commands.has_permissions(administrator=True)
    async def automod_badwords(self, ctx, action: str, *, word: str = None):
        """Manage bad words. action: add/remove/list"""
        cfg = await db_automod.get(str(ctx.guild.id), {})
        badwords = cfg.get("badwords", [])

        if action.lower() == "add" and word:
            badwords.append(word.lower())
            cfg["badwords"] = badwords
            await db_automod.set(str(ctx.guild.id), cfg)
            await ctx.send(embed=success_embed(f"Added `{word}` to bad words list!"))
        elif action.lower() == "remove" and word:
            if word.lower() in badwords:
                badwords.remove(word.lower())
                cfg["badwords"] = badwords
                await db_automod.set(str(ctx.guild.id), cfg)
                await ctx.send(embed=success_embed(f"Removed `{word}` from bad words!"))
            else:
                await ctx.send(embed=error_embed("Word not in list!"))
        elif action.lower() == "list":
            if badwords:
                await ctx.send(embed=make_embed(title="🚫 Bad Words", description=", ".join(f"`{w}`" for w in badwords), color=LYTRIX_COLOR))
            else:
                await ctx.send(embed=make_embed(title="🚫 Bad Words", description="No bad words configured."))
        else:
            await ctx.send(embed=error_embed("Usage: `!automod badwords <add|remove|list> [word]`"))

    @automod_group.command(name="whitelist")
    @commands.has_permissions(administrator=True)
    async def automod_whitelist(self, ctx, *, user: discord.Member):
        cfg = await db_automod.get(str(ctx.guild.id), {})
        whitelist = cfg.get("whitelisted_users", [])
        if str(user.id) not in whitelist:
            whitelist.append(str(user.id))
            cfg["whitelisted_users"] = whitelist
            await db_automod.set(str(ctx.guild.id), cfg)
            await ctx.send(embed=success_embed(f"✅ {user.mention} bypasses automod now!"))
        else:
            whitelist.remove(str(user.id))
            cfg["whitelisted_users"] = whitelist
            await db_automod.set(str(ctx.guild.id), cfg)
            await ctx.send(embed=success_embed(f"❌ {user.mention} no longer bypasses automod."))

    # ==============================================
    # LEVELING COMMANDS
    # ==============================================
    @commands.command(name="rank", aliases=["level", "xp"])
    async def rank_cmd(self, ctx, *, member: discord.Member = None):
        """View rank card."""
        member = member or ctx.author
        data = await db_levels.get(f"{ctx.guild.id}:{member.id}", {"xp": 0, "level": 1, "total_xp": 0, "messages": 0})

        xp = data.get("xp", 0)
        level = data.get("level", 1)
        total_xp = data.get("total_xp", 0)
        msgs = data.get("messages", 0)
        next_level_xp = level * 100 + 50
        bar_fill = min(int((xp / next_level_xp) * 20), 20)
        bar = "🟣" * bar_fill + "⚫" * (20 - bar_fill)

        embed = Embed(title=f"📊 Rank: {member.name}", color=LYTRIX_COLOR)
        embed.add_field(name="Level", value=f"**{level}**", inline=True)
        embed.add_field(name="XP", value=f"**{xp}/{next_level_xp}**", inline=True)
        embed.add_field(name="Total XP", value=f"**{total_xp}**", inline=True)
        embed.add_field(name="Messages", value=str(msgs), inline=True)
        embed.add_field(name="Progress", value=f"{bar}\n`{xp}/{next_level_xp} XP`", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Lytrix Levels • Made by Reon")
        await ctx.send(embed=embed)

    @commands.command(name="leaderboard", aliases=["lb", "top"])
    async def leaderboard_cmd(self, ctx):
        """Server XP leaderboard."""
        all_data = await db_levels.all()
        guild_data = []
        for key, data in all_data.items():
            if key.startswith(f"{ctx.guild.id}:"):
                user_id = int(key.split(":")[1])
                guild_data.append((user_id, data.get("total_xp", 0), data.get("level", 1)))

        guild_data.sort(key=lambda x: x[1], reverse=True)
        embed = Embed(title=f"🏆 {ctx.guild.name} Leaderboard", color=LYTRIX_COLOR)

        for i, (user_id, total_xp, level) in enumerate(guild_data[:15], 1):
            medals = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"**{i}.**")
            embed.add_field(
                name=f"{medals} <@{user_id}>",
                value=f"Level: **{level}** | XP: **{total_xp:,}**",
                inline=False
            )

        if not guild_data:
            embed.description = "No one has XP yet! Start chatting to earn XP."
        embed.set_footer(text="Lytrix Levels • Made by Reon")
        await ctx.send(embed=embed)

    @commands.command(name="levelrole")
    @commands.has_permissions(manage_roles=True)
    async def levelrole_cmd(self, ctx, level: int, *, role: discord.Role):
        """Add a level reward role."""
        cfg = await db_guilds.get(str(ctx.guild.id), {})
        level_roles = cfg.get("level_roles", {})
        level_roles[str(level)] = role.id
        cfg["level_roles"] = level_roles
        await db_guilds.set(str(ctx.guild.id), cfg)
        await ctx.send(embed=success_embed(f"✅ {role.mention} will be given at Level **{level}**!"))

    # ==============================================
    # ECONOMY COMMANDS
    # ==============================================
    @commands.command(name="balance", aliases=["bal", "money", "wallet", "bank"])
    async def balance_cmd(self, ctx, *, member: discord.Member = None):
        """Check balance."""
        member = member or ctx.author
        data = await db_economy.get(f"{ctx.guild.id}:{member.id}", {
            "wallet": 100, "bank": 0, "total_earned": 100,
            "daily_last": 0, "weekly_last": 0, "monthly_last": 0,
        })
        embed = Embed(title=f"💰 {member.name}'s Balance", color=LYTRIX_COLOR2)
        embed.add_field(name="Wallet", value=f"**{data['wallet']:,}** 🪙", inline=True)
        embed.add_field(name="Bank", value=f"**{data['bank']:,}** 🪙", inline=True)
        embed.add_field(name="Total", value=f"**{data['wallet'] + data['bank']:,}** 🪙", inline=True)
        embed.set_footer(text="Lytrix Economy • Made by Reon")
        await ctx.send(embed=embed)

    @commands.command(name="daily")
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def daily_cmd(self, ctx):
        """Daily reward."""
        data = await db_economy.get(f"{ctx.guild.id}:{ctx.author.id}", {
            "wallet": 0, "bank": 0, "total_earned": 0,
            "daily_last": 0, "weekly_last": 0, "monthly_last": 0,
        })
        bonus = random.randint(200, 500)
        data["wallet"] += bonus
        data["total_earned"] += bonus
        data["daily_last"] = time.time()
        await db_economy.set(f"{ctx.guild.id}:{ctx.author.id}", data)
        await ctx.send(embed=success_embed(f"📅 Daily reward: **+{bonus:,}** 🪙\nNew balance: **{data['wallet']:,}** 🪙"))

    @commands.command(name="weekly")
    @commands.cooldown(1, 604800, commands.BucketType.user)
    async def weekly_cmd(self, ctx):
        """Weekly reward."""
        data = await db_economy.get(f"{ctx.guild.id}:{ctx.author.id}", {"wallet": 0, "bank": 0, "total_earned": 0})
        bonus = random.randint(1500, 3000)
        data["wallet"] += bonus
        data["total_earned"] += bonus
        await db_economy.set(f"{ctx.guild.id}:{ctx.author.id}", data)
        await ctx.send(embed=success_embed(f"📅 Weekly reward: **+{bonus:,}** 🪙"))

    @commands.command(name="work")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def work_cmd(self, ctx):
        """Work for money."""
        data = await db_economy.get(f"{ctx.guild.id}:{ctx.author.id}", {"wallet": 0, "bank": 0, "total_earned": 0})
        jobs = [
            ("software developer", random.randint(100, 400)),
            ("pizza delivery", random.randint(50, 150)),
            ("bug tester", random.randint(80, 300)),
            ("streamer", random.randint(50, 500)),
            ("musician", random.randint(60, 350)),
            ("chef", random.randint(70, 250)),
            ("teacher", random.randint(90, 280)),
            ("doctor", random.randint(200, 600)),
        ]
        job, pay = random.choice(jobs)
        data["wallet"] += pay
        data["total_earned"] += pay
        await db_economy.set(f"{ctx.guild.id}:{ctx.author.id}", data)
        await ctx.send(embed=success_embed(f"💼 Worked as **{job}**: **+{pay:,}** 🪙"))

    @commands.command(name="beg")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def beg_cmd(self, ctx):
        """Beg for coins."""
        data = await db_economy.get(f"{ctx.guild.id}:{ctx.author.id}", {"wallet": 0, "bank": 0})
        if random.random() < 0.6:
            amount = random.randint(10, 100)
            data["wallet"] += amount
            await db_economy.set(f"{ctx.guild.id}:{ctx.author.id}", data)
            await ctx.send(embed=success_embed(f"🥺 Someone gave you **{amount:,}** 🪙!"))
        else:
            await ctx.send(embed=error_embed("No one gave you anything... Try again!"))

    @commands.command(name="rob")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def rob_cmd(self, ctx, *, target: discord.Member):
        """Rob someone."""
        if target.id == ctx.author.id:
            await ctx.send(embed=error_embed("You can't rob yourself!"))
            return

        target_data = await db_economy.get(f"{ctx.guild.id}:{target.id}", {"wallet": 0, "bank": 0})
        if target_data["wallet"] < 50:
            await ctx.send(embed=error_embed("They're too poor to rob!"))
            return

        if random.random() < 0.4:
            stolen = random.randint(10, min(500, target_data["wallet"]))
            target_data["wallet"] -= stolen
            await db_economy.set(f"{ctx.guild.id}:{target.id}", target_data)

            author_data = await db_economy.get(f"{ctx.guild.id}:{ctx.author.id}", {"wallet": 0})
            author_data["wallet"] += stolen
            await db_economy.set(f"{ctx.guild.id}:{ctx.author.id}", author_data)
            await ctx.send(embed=success_embed(f"🦹 Robbed **{stolen:,}** 🪙 from {target.mention}!"))
        else:
            fine = random.randint(50, 300)
            author_data = await db_economy.get(f"{ctx.guild.id}:{ctx.author.id}", {"wallet": 0})
            author_data["wallet"] = max(0, author_data["wallet"] - fine)
            await db_economy.set(f"{ctx.guild.id}:{ctx.author.id}", author_data)
            await ctx.send(embed=error_embed(f"🚔 Caught! Fined **{fine:,}** 🪙!"))

    @commands.command(name="crime")
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def crime_cmd(self, ctx):
        """Commit a crime."""
        data = await db_economy.get(f"{ctx.guild.id}:{ctx.author.id}", {"wallet": 0})
        if random.random() < 0.5:
            reward = random.randint(200, 1000)
            data["wallet"] += reward
            await db_economy.set(f"{ctx.guild.id}:{ctx.author.id}", data)
            await ctx.send(embed=success_embed(f"🕵️ Crime successful! **+{reward:,}** 🪙"))
        else:
            fine = random.randint(100, 500)
            data["wallet"] = max(0, data["wallet"] - fine)
            await db_economy.set(f"{ctx.guild.id}:{ctx.author.id}", data)
            await ctx.send(embed=error_embed(f"🚔 Busted! Lost **{fine:,}** 🪙"))

    @commands.command(name="slots")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def slots_cmd(self, ctx, bet: int = 10):
        """Slot machine."""
        data = await db_economy.get(f"{ctx.guild.id}:{ctx.author.id}", {"wallet": 0})
        if bet > data["wallet"] or bet < 1:
            await ctx.send(embed=error_embed("Invalid bet amount!"))
            return

        emojis = ["🍒", "🍋", "🍊", "🍇", "💎", "7️⃣", "⭐"]
        result = [random.choice(emojis) for _ in range(3)]
        slot = " | ".join(result)

        if result[0] == result[1] == result[2]:
            multiplier = 10 if result[0] == "💎" else 5 if result[0] == "7️⃣" else 3
            win = bet * multiplier
            data["wallet"] += win
            outcome = f"🎉 JACKPOT! Won **{win:,}** 🪙"
        elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
            win = bet * 2
            data["wallet"] += win
            outcome = f"✨ Two match! Won **{win:,}** 🪙"
        else:
            data["wallet"] -= bet
            outcome = f"😢 Lost **{bet:,}** 🪙"

        await db_economy.set(f"{ctx.guild.id}:{ctx.author.id}", data)
        await ctx.send(embed=make_embed(title="🎰 Slots", description=f"```\n{slot}\n```\n{outcome}", color=LYTRIX_COLOR2))

    @commands.command(name="give", aliases=["pay", "transfer", "send"])
    async def give_cmd(self, ctx, target: discord.Member, amount: int):
        """Give money to someone."""
        if target.id == ctx.author.id:
            await ctx.send(embed=error_embed("Can't send to yourself!"))
            return
        if amount < 1:
            await ctx.send(embed=error_embed("Invalid amount!"))
            return

        author_data = await db_economy.get(f"{ctx.guild.id}:{ctx.author.id}", {"wallet": 0})
        if amount > author_data["wallet"]:
            await ctx.send(embed=error_embed("Insufficient funds!"))
            return

        author_data["wallet"] -= amount
        await db_economy.set(f"{ctx.guild.id}:{ctx.author.id}", author_data)

        target_data = await db_economy.get(f"{ctx.guild.id}:{target.id}", {"wallet": 0})
        target_data["wallet"] += amount
        await db_economy.set(f"{ctx.guild.id}:{target.id}", target_data)

        await ctx.send(embed=success_embed(f"💸 Sent **{amount:,}** 🪙 to {target.mention}!"))

    @commands.command(name="richlist", aliases=["richest"])
    async def richlist_cmd(self, ctx):
        """Server wealth leaderboard."""
        all_data = await db_economy.all()
        guild_wealth = []
        for key, data in all_data.items():
            if key.startswith(f"{ctx.guild.id}:"):
                user_id = int(key.split(":")[1])
                total = data.get("wallet", 0) + data.get("bank", 0)
                guild_wealth.append((user_id, total))

        guild_wealth.sort(key=lambda x: x[1], reverse=True)

        embed = Embed(title="💰 Wealth Leaderboard", color=LYTRIX_COLOR2)
        for i, (uid, wealth) in enumerate(guild_wealth[:15], 1):
            medals = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"**{i}.**")
            embed.add_field(name=f"{medals} <@{uid}>", value=f"**{wealth:,}** 🪙", inline=False)

        if not guild_wealth:
            embed.description = "No one has started earning yet!"
        embed.set_footer(text="Lytrix Economy • Made by Reon")
        await ctx.send(embed=embed)

    @commands.command(name="inventory", aliases=["inv", "items", "backpack"])
    async def inventory_cmd(self, ctx):
        """View inventory."""
        data = await db_economy.get(f"{ctx.guild.id}:{ctx.author.id}", {"inventory": []})
        inv = data.get("inventory", [])
        if inv:
            item_counts = Counter(inv)
            items_text = "\n".join(f"• {item}: x{count}" for item, count in item_counts.items())
            await ctx.send(embed=make_embed(title="🎒 Inventory", description=items_text, color=LYTRIX_COLOR))
        else:
            await ctx.send(embed=make_embed(title="🎒 Inventory", description="Empty! Use `!shop` to buy items.", color=LYTRIX_COLOR))

    @commands.command(name="shop")
    async def shop_cmd(self, ctx):
        """View item shop."""
        embed = Embed(title="🏪 Lytrix Shop", color=LYTRIX_COLOR2)
        items = [
            ("🎣 Fishing Rod", "500", "Better fishing chances"),
            ("⛏️ Pickaxe", "500", "Better mining results"),
            ("🪓 Axe", "400", "Better chop results"),
            ("🔫 Hunting Rifle", "800", "Better hunting results"),
            ("💍 Lucky Ring", "2000", "10% more coins from all actions"),
            ("🛡️ Shield", "1000", "Protection from rob"),
            ("📱 Phone", "3000", "Access to more commands"),
            ("🚗 Car", "10000", "Flex item"),
            ("🏠 House", "50000", "Ultimate flex"),
        ]
        for name, price, desc in items:
            embed.add_field(name=f"{name} — {price} 🪙", value=desc, inline=False)
        embed.set_footer(text="Use !buy <item> to purchase • Lytrix Economy")
        await ctx.send(embed=embed)

    @commands.command(name="buy")
    async def buy_cmd(self, ctx, *, item: str):
        """Buy an item from the shop."""
        shop_items = {
            "fishing rod": 500, "pickaxe": 500, "axe": 400,
            "hunting rifle": 800, "lucky ring": 2000, "shield": 1000,
            "phone": 3000, "car": 10000, "house": 50000,
        }
        item_lower = item.lower()
        if item_lower not in shop_items:
            await ctx.send(embed=error_embed("Item not found! Use `!shop` to see items."))
            return

        price = shop_items[item_lower]
        data = await db_economy.get(f"{ctx.guild.id}:{ctx.author.id}", {"wallet": 0, "inventory": []})

        if data["wallet"] < price:
            await ctx.send(embed=error_embed(f"Insufficient funds! Need **{price:,}** 🪙"))
            return

        data["wallet"] -= price
        data["inventory"].append(item_lower)
        await db_economy.set(f"{ctx.guild.id}:{ctx.author.id}", data)
        await ctx.send(embed=success_embed(f"🛒 Purchased **{item}** for **{price:,}** 🪙!"))

    # ==============================================
    # WELCOME & LEAVE COMMANDS
    # ==============================================
    @commands.group(name="welcome", aliases=["welc", "joinmsg"], invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def welcome_group(self, ctx):
        """Welcome message settings."""
        cfg = await db_welcome.get(f"welcome_{ctx.guild.id}", {
            "channel": None, "message": "Welcome {user} to {server}!",
            "embed": True, "dm": False, "role": None, "enabled": True,
            "image": None, "color": LYTRIX_COLOR,
        })
        embed = Embed(title="👋 Welcome Settings", color=LYTRIX_COLOR)
        embed.add_field(name="Enabled", value="✅" if cfg.get("enabled") else "❌", inline=True)
        embed.add_field(name="Channel", value=f"<#{cfg['channel']}>" if cfg.get("channel") else "Not set", inline=True)
        embed.add_field(name="Auto Role", value=f"<@&{cfg['role']}>" if cfg.get("role") else "None", inline=True)
        embed.add_field(name="Message", value=cfg.get("message", "N/A"), inline=False)
        embed.set_footer(text="Lytrix Welcome • Made by Reon")
        await ctx.send(embed=embed)

    @welcome_group.command(name="channel")
    @commands.has_permissions(manage_guild=True)
    async def welcome_channel(self, ctx, *, channel: discord.TextChannel):
        cfg = await db_welcome.get(f"welcome_{ctx.guild.id}", {})
        cfg["channel"] = str(channel.id)
        await db_welcome.set(f"welcome_{ctx.guild.id}", cfg)
        await ctx.send(embed=success_embed(f"Welcome channel set to {channel.mention}"))

    @welcome_group.command(name="message")
    @commands.has_permissions(manage_guild=True)
    async def welcome_message(self, ctx, *, message: str):
        cfg = await db_welcome.get(f"welcome_{ctx.guild.id}", {})
        cfg["message"] = message
        await db_welcome.set(f"welcome_{ctx.guild.id}", cfg)
        await ctx.send(embed=success_embed(f"Welcome message set!\nPreview: {message.replace('{user}', ctx.author.mention).replace('{server}', ctx.guild.name)}"))

    @welcome_group.command(name="role")
    @commands.has_permissions(manage_guild=True)
    async def welcome_role(self, ctx, *, role: discord.Role):
        cfg = await db_welcome.get(f"welcome_{ctx.guild.id}", {})
        cfg["role"] = str(role.id)
        await db_welcome.set(f"welcome_{ctx.guild.id}", cfg)
        await ctx.send(embed=success_embed(f"Auto-role set to {role.mention}"))

    @welcome_group.command(name="test")
    async def welcome_test(self, ctx):
        """Test welcome message."""
        cfg = await db_welcome.get(f"welcome_{ctx.guild.id}", {})
        msg = cfg.get("message", "Welcome {user} to {server}!").replace("{user}", ctx.author.mention).replace("{server}", ctx.guild.name)
        await ctx.send(embed=make_embed(title="👋 Welcome Test", description=msg, color=LYTRIX_COLOR))

    @welcome_group.command(name="enable")
    @commands.has_permissions(manage_guild=True)
    async def welcome_enable(self, ctx):
        cfg = await db_welcome.get(f"welcome_{ctx.guild.id}", {})
        cfg["enabled"] = True
        await db_welcome.set(f"welcome_{ctx.guild.id}", cfg)
        await ctx.send(embed=success_embed("Welcome messages enabled!"))

    @welcome_group.command(name="disable")
    @commands.has_permissions(manage_guild=True)
    async def welcome_disable(self, ctx):
        cfg = await db_welcome.get(f"welcome_{ctx.guild.id}", {})
        cfg["enabled"] = False
        await db_welcome.set(f"welcome_{ctx.guild.id}", cfg)
        await ctx.send(embed=success_embed("Welcome messages disabled!"))

    @commands.group(name="leave", aliases=["leavemsg", "byemsg"], invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def leave_group(self, ctx):
        """Leave message settings."""
        cfg = await db_welcome.get(f"leave_{ctx.guild.id}", {
            "channel": None, "message": "Goodbye {user}! We'll miss you 😢",
            "enabled": True,
        })
        embed = Embed(title="👋 Leave Settings", color=LYTRIX_COLOR)
        embed.add_field(name="Enabled", value="✅" if cfg.get("enabled") else "❌", inline=True)
        embed.add_field(name="Channel", value=f"<#{cfg['channel']}>" if cfg.get("channel") else "Not set", inline=True)
        embed.add_field(name="Message", value=cfg.get("message", "N/A"), inline=False)
        await ctx.send(embed=embed)

    @leave_group.command(name="channel")
    @commands.has_permissions(manage_guild=True)
    async def leave_channel(self, ctx, *, channel: discord.TextChannel):
        cfg = await db_welcome.get(f"leave_{ctx.guild.id}", {})
        cfg["channel"] = str(channel.id)
        await db_welcome.set(f"leave_{ctx.guild.id}", cfg)
        await ctx.send(embed=success_embed(f"Leave channel set to {channel.mention}"))

    @leave_group.command(name="message")
    @commands.has_permissions(manage_guild=True)
    async def leave_message(self, ctx, *, message: str):
        cfg = await db_welcome.get(f"leave_{ctx.guild.id}", {})
        cfg["message"] = message
        await db_welcome.set(f"leave_{ctx.guild.id}", cfg)
        await ctx.send(embed=success_embed(f"Leave message set!"))

    # ==============================================
    # REACTION ROLE COMMANDS
    # ==============================================
    @commands.group(name="reactionrole", aliases=["rr", "reactrole"], invoke_without_command=True)
    @commands.has_permissions(manage_roles=True)
    async def rr_group(self, ctx):
        """Reaction role management."""
        await ctx.send(embed=make_embed(
            title="🎭 Reaction Roles",
            description="`!rr add <#channel> <msg_id> <emoji> <role>`\n`!rr remove <msg_id> <emoji>`\n`!rr list`\n`!rr panel <#channel> <title>`",
            color=LYTRIX_COLOR
        ))

    @rr_group.command(name="add")
    @commands.has_permissions(manage_roles=True)
    async def rr_add(self, ctx, channel: discord.TextChannel, message_id: str, emoji: str, *, role: discord.Role):
        try:
            msg = await channel.fetch_message(int(message_id))
            await msg.add_reaction(emoji)
        except:
            await ctx.send(embed=error_embed("Could not find message or add reaction!"))
            return

        rrs = await db_reaction_roles.get(f"{ctx.guild.id}:{message_id}", [])
        rrs.append({"emoji": emoji, "role_id": role.id, "channel_id": channel.id})
        await db_reaction_roles.set(f"{ctx.guild.id}:{message_id}", rrs)
        await ctx.send(embed=success_embed(f"✅ Reaction role added! {emoji} → {role.mention}"))

    @rr_group.command(name="remove")
    @commands.has_permissions(manage_roles=True)
    async def rr_remove(self, ctx, message_id: str, emoji: str):
        rrs = await db_reaction_roles.get(f"{ctx.guild.id}:{message_id}", [])
        rrs = [r for r in rrs if r["emoji"] != emoji]
        if rrs:
            await db_reaction_roles.set(f"{ctx.guild.id}:{message_id}", rrs)
        else:
            await db_reaction_roles.delete(f"{ctx.guild.id}:{message_id}")
        await ctx.send(embed=success_embed("✅ Reaction role removed!"))

    @rr_group.command(name="list")
    async def rr_list(self, ctx):
        all_rrs = await db_reaction_roles.all()
        embed = Embed(title="🎭 Reaction Roles", color=LYTRIX_COLOR)
        found = False
        for key, rrs in all_rrs.items():
            if key.startswith(f"{ctx.guild.id}:"):
                msg_id = key.split(":")[1]
                for rr in rrs[:5]:
                    role = ctx.guild.get_role(rr["role_id"])
                    embed.add_field(
                        name=f"Message: {msg_id}",
                        value=f"{rr['emoji']} → {role.mention if role else 'Deleted'}",
                        inline=False
                    )
                    found = True
        if not found:
            embed.description = "No reaction roles configured."
        await ctx.send(embed=embed)

    @rr_group.command(name="panel")
    @commands.has_permissions(manage_roles=True)
    async def rr_panel(self, ctx, channel: discord.TextChannel, *, title: str):
        """Create a reaction role panel."""
        embed = Embed(title=title, description="React to get roles!", color=LYTRIX_COLOR)
        embed.set_footer(text="Lytrix Reaction Roles • Made by Reon")
        await ctx.send(embed=make_embed(title="📋 Setup", description="Now use `!rr add #channel <msg_id> <emoji> <role>` to add roles to this message."))

    # ==============================================
    # CONFIGURATION COMMANDS
    # ==============================================
    @commands.command(name="config", aliases=["settings", "cfg"])
    @commands.has_permissions(manage_guild=True)
    async def config_cmd(self, ctx):
        """View server configuration."""
        cfg = await db_guilds.get(str(ctx.guild.id), {})
        embed = Embed(title=f"⚙️ {ctx.guild.name} Configuration", color=LYTRIX_COLOR)
        embed.add_field(name="Prefix", value=cfg.get("prefix", BOT_PREFIX), inline=True)
        embed.add_field(name="AntiNuke", value="✅" if (await db_antinuke.get(str(ctx.guild.id), {})).get("enabled") else "❌", inline=True)
        embed.add_field(name="AutoMod", value="✅" if (await db_automod.get(str(ctx.guild.id), {})).get("enabled") else "❌", inline=True)
        embed.add_field(name="Tickets", value="✅" if cfg.get("tickets", {}).get("enabled", True) else "❌", inline=True)
        embed.add_field(name="Welcome", value="✅" if (await db_welcome.get(f"welcome_{ctx.guild.id}", {})).get("enabled") else "❌", inline=True)
        embed.add_field(name="Leave", value="✅" if (await db_welcome.get(f"leave_{ctx.guild.id}", {})).get("enabled") else "❌", inline=True)
        embed.set_footer(text="Lytrix Config • Made by Reon")
        await ctx.send(embed=embed)

    # ==============================================
    # PRIVATE HELPERS
    # ==============================================
    def _parse_duration(self, duration: str) -> int:
        """Convert duration string to seconds."""
        match = re.match(r'(\d+)([smhd])', duration.lower())
        if not match:
            return 0
        value, unit = int(match.group(1)), match.group(2)
        multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        return value * multipliers.get(unit, 0)

    async def _log_case(self, ctx, case_type: str, target: Union[discord.Member, discord.User], reason: str):
        """Log a moderation case."""
        self.bot.case_counter[ctx.guild.id] = self.bot.case_counter.get(ctx.guild.id, 0) + 1
        case_id = self.bot.case_counter[ctx.guild.id]

        cases = await db_cases.get(str(ctx.guild.id), {})
        cases[str(case_id)] = {
            "case_id": case_id,
            "type": case_type,
            "user_id": target.id if hasattr(target, 'id') else target.id,
            "mod_id": ctx.author.id,
            "reason": reason,
            "time": time.time(),
            "timestamp": str(datetime.datetime.utcnow()),
        }
        await db_cases.set(str(ctx.guild.id), cases)

    # ==============================================
    # OWNER COMMANDS
    # ==============================================
    @commands.command(name="eval", hidden=True)
    @commands.is_owner()
    async def eval_cmd(self, ctx, *, code: str):
        """Evaluate Python code."""
        code = code.strip('`').replace('py\n', '').replace('python\n', '')
        try:
            result = eval(code)
            await ctx.send(f"```py\n{result}\n```")
        except Exception as e:
            await ctx.send(f"```py\n{type(e).__name__}: {e}\n```")

    @commands.command(name="reload", hidden=True)
    @commands.is_owner()
    async def reload_cmd(self, ctx):
        """Reload the bot's cog."""
        await self.bot.reload_extension("main")
        await ctx.send(embed=success_embed("🔄 Bot reloaded!"))

    @commands.command(name="shutdown", aliases=["die", "kill"], hidden=True)
    @commands.is_owner()
    async def shutdown_cmd(self, ctx):
        """Shutdown the bot."""
        await ctx.send(embed=warn_embed("Shutting down..."))
        await self.bot.close()


# ============================================================
# EVENT LISTENERS
# ============================================================
@bot.event
async def on_ready():
    await bot.wait_until_ready()
    # Register persistent views
    bot.add_view(TicketView(bot))
    bot.add_view(TicketManageView(bot, 0))

    # Initialize anti_nuke on the bot
    global anti_nuke
    anti_nuke = bot.anti_nuke

    print(f"✅ Lytrix Bot is fully ready! ({len(bot.guilds)} guilds)")
    print(f"🔗 Invite: https://discord.com/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot+applications.commands")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # AFK check
    if message.author.id in bot.afk_users:
        reason, afk_time = bot.afk_users.pop(message.author.id)
        try:
            await message.channel.send(
                embed=success_embed(f"👋 Welcome back {message.author.mention}! You were AFK: **{reason}**"),
                delete_after=10
            )
        except:
            pass

    # Check if a mentioned user is AFK
    for mention in message.mentions:
        if mention.id in bot.afk_users:
            reason, afk_time = bot.afk_users[mention.id]
            try:
                await message.channel.send(
                    embed=make_embed(
                        title="💤 User is AFK",
                        description=f"{mention.name} is AFK: **{reason}**\nSet <t:{int(afk_time)}:R>",
                        color=LYTRIX_COLOR
                    ),
                    delete_after=10
                )
            except:
                pass

    # Leveling XP
    if message.guild:
        key = f"{message.guild.id}:{message.author.id}"
        data = await db_levels.get(key, {"xp": 0, "level": 1, "total_xp": 0, "messages": 0})
        data["messages"] = data.get("messages", 0) + 1
        xp_gain = random.randint(5, 15)
        data["xp"] = data.get("xp", 0) + xp_gain
        data["total_xp"] = data.get("total_xp", 0) + xp_gain

        next_level = data["level"] * 100 + 50
        if data["xp"] >= next_level:
            data["level"] += 1
            data["xp"] = data["xp"] - next_level

            # Check level role rewards
            cfg = await db_guilds.get(str(message.guild.id), {})
            level_roles = cfg.get("level_roles", {})
            if str(data["level"]) in level_roles:
                role = message.guild.get_role(level_roles[str(data["level"])])
                if role and role not in message.author.roles:
                    try:
                        await message.author.add_roles(role, reason="Level role reward")
                        await message.channel.send(
                            embed=success_embed(f"🎉 {message.author.mention} reached Level **{data['level']}** and earned {role.mention}!"),
                            delete_after=10
                        )
                    except:
                        pass

        await db_levels.set(key, data)

    # Process commands
    ctx = await bot.get_context(message)
    if ctx.valid:
        bot.command_usage[ctx.command.name] += 1
        await bot.invoke(ctx)


@bot.event
async def on_message_delete(message: discord.Message):
    if message.author.bot or not message.guild:
        return
    bot.snipes[message.channel.id] = {
        "content": message.content or "*[No text content]*",
        "author": str(message.author),
        "time": datetime.datetime.utcnow(),
        "attachment": message.attachments[0].url if message.attachments else None,
    }


@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    if before.author.bot or not before.guild:
        return
    if before.content != after.content:
        bot.edit_snipes[before.channel.id] = {
            "before": before.content or "*[No content]*",
            "after": after.content or "*[No content]*",
            "author": str(before.author),
            "time": datetime.datetime.utcnow(),
        }


@bot.event
async def on_reaction_remove(reaction: discord.Reaction, user: discord.Member):
    if user.bot or not reaction.message.guild:
        return
    bot.reaction_snipes[reaction.message.channel.id] = {
        "emoji": str(reaction.emoji),
        "user": str(user),
        "message_id": reaction.message.id,
        "time": datetime.datetime.utcnow(),
    }


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.member and payload.member.bot:
        return

    # Reaction roles
    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return

    rrs = await db_reaction_roles.get(f"{guild.id}:{payload.message_id}", [])
    for rr in rrs:
        if str(payload.emoji) == rr["emoji"]:
            role = guild.get_role(rr["role_id"])
            member = guild.get_member(payload.user_id)
            if role and member and role not in member.roles:
                try:
                    await member.add_roles(role, reason="Reaction role")
                except:
                    pass


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return

    rrs = await db_reaction_roles.get(f"{guild.id}:{payload.message_id}", [])
    for rr in rrs:
        if str(payload.emoji) == rr["emoji"]:
            role = guild.get_role(rr["role_id"])
            member = guild.get_member(payload.user_id)
            if role and member and role in member.roles:
                try:
                    await member.remove_roles(role, reason="Reaction role removed")
                except:
                    pass

    # Giveaway reactions
    giveaway = await db_giveaways.get(str(payload.message_id), {})
    if giveaway and not giveaway.get("ended"):
        if str(payload.emoji) == "🎉":
            participants = giveaway.get("participants", [])
            if payload.user_id in participants:
                participants.remove(payload.user_id)
                giveaway["participants"] = participants
                await db_giveaways.set(str(payload.message_id), giveaway)


@bot.event
async def on_member_join(member: discord.Member):
    # Welcome message
    cfg = await db_welcome.get(f"welcome_{member.guild.id}", {})
    if cfg.get("enabled") and cfg.get("channel"):
        channel = member.guild.get_channel(int(cfg["channel"]))
        if channel:
            msg = cfg.get("message", "Welcome {user} to {server}!")
            msg = msg.replace("{user}", member.mention).replace("{server}", member.guild.name).replace("{count}", str(member.guild.member_count))

            if cfg.get("embed", True):
                embed = Embed(
                    title=f"👋 Welcome to {member.guild.name}!",
                    description=msg,
                    color=cfg.get("color", LYTRIX_COLOR),
                    timestamp=datetime.datetime.utcnow()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.add_field(name="Member Count", value=f"#{member.guild.member_count}", inline=True)
                embed.set_footer(text="Lytrix Welcome • Made by Reon")
                await channel.send(embed=embed)
            else:
                await channel.send(msg)

    # Auto-role
    if cfg.get("role"):
        role = member.guild.get_role(int(cfg["role"]))
        if role:
            try:
                await member.add_roles(role, reason="Auto-role on join")
            except:
                pass

    # AutoMod: Anti-bot (part of anti-nuke)
    if member.bot:
        an_config = await bot.anti_nuke.get_config(member.guild.id)
        if an_config.get("enabled") and an_config.get("modules", {}).get("anti_bot_add"):
            if not bot.anti_nuke.has_bypass(an_config, member):
                # Check who added the bot
                async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
                    if entry.target.id == member.id:
                        inviter = entry.user
                        if inviter and not bot.anti_nuke.has_bypass(an_config, inviter):
                            await bot.anti_nuke.punish(member.guild, inviter, f"Unauthorized bot addition: {member.name}")
                            try:
                                await member.ban(reason="AntiNuke: Unauthorized bot")
                            except:
                                pass
                            await bot.anti_nuke.log_action(
                                member.guild, "Anti-Bot", f"{member.name} ({member.id})",
                                f"{inviter.name} ({inviter.id})", "Bot addition blocked and punisher applied"
                            )


@bot.event
async def on_member_remove(member: discord.Member):
    # Leave message
    cfg = await db_welcome.get(f"leave_{member.guild.id}", {})
    if cfg.get("enabled") and cfg.get("channel"):
        channel = member.guild.get_channel(int(cfg["channel"]))
        if channel:
            msg = cfg.get("message", "Goodbye {user}! We'll miss you 😢")
            msg = msg.replace("{user}", member.mention).replace("{server}", member.guild.name)

            embed = Embed(
                title="👋 Member Left",
                description=msg,
                color=0xEF4444,
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="Member Count", value=f"#{member.guild.member_count}", inline=True)
            embed.set_footer(text="Lytrix Leave • Made by Reon")
            await channel.send(embed=embed)


@bot.event
async def on_member_ban(guild: Guild, user: Union[discord.User, discord.Member]):
    """Anti-nuke: Check for mass bans."""
    if not hasattr(bot, 'anti_nuke') or not bot.anti_nuke:
        return

    an_config = await bot.anti_nuke.get_config(guild.id)
    if not an_config.get("enabled") or not an_config.get("modules", {}).get("anti_ban"):
        return

    # Check audit log
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
        executor = entry.user
        if executor and executor.id != bot.user.id:
            if not bot.anti_nuke.has_bypass(an_config, executor):
                if await bot.anti_nuke.check_rate(guild.id, "ban", an_config, executor.id):
                    # Rate limit exceeded - mass ban detected
                    await bot.anti_nuke.punish(guild, executor, "Mass ban detected")
                    try:
                        await guild.unban(user, reason="AntiNuke: Reversing mass ban")
                    except:
                        pass
                    await bot.anti_nuke.log_action(
                        guild, "Mass Ban Blocked", str(user),
                        f"{executor.name} ({executor.id})", "Multiple bans detected in short period"
                    )


@bot.event
async def on_member_kick(member: discord.Member):
    """Anti-nuke: Check for mass kicks."""
    an_config = await bot.anti_nuke.get_config(member.guild.id)
    if not an_config.get("enabled") or not an_config.get("modules", {}).get("anti_kick"):
        return

    async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
        executor = entry.user
        if executor and executor.id != bot.user.id:
            if not bot.anti_nuke.has_bypass(an_config, executor):
                if await bot.anti_nuke.check_rate(member.guild.id, "kick", an_config, executor.id):
                    await bot.anti_nuke.punish(member.guild, executor, "Mass kick detected")
                    await bot.anti_nuke.log_action(
                        member.guild, "Mass Kick Blocked", str(member),
                        f"{executor.name}", "Multiple kicks detected"
                    )


@bot.event
async def on_guild_channel_create(channel: discord.abc.GuildChannel):
    """Anti-nuke: Check for mass channel creation."""
    an_config = await bot.anti_nuke.get_config(channel.guild.id)
    if not an_config.get("enabled") or not an_config.get("modules", {}).get("anti_channel_create"):
        return

    async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
        executor = entry.user
        if executor and executor.id != bot.user.id:
            if not bot.anti_nuke.has_bypass(an_config, executor):
                if await bot.anti_nuke.check_rate(channel.guild.id, "channel", an_config, executor.id):
                    await bot.anti_nuke.punish(channel.guild, executor, "Mass channel creation detected")
                    try:
                        await channel.delete(reason="AntiNuke: Reversing mass channel creation")
                    except:
                        pass
                    await bot.anti_nuke.log_action(
                        channel.guild, "Mass Channel Creation", channel.name,
                        f"{executor.name}", "Multiple channels created rapidly"
                    )


@bot.event
async def on_guild_channel_delete(channel: discord.abc.GuildChannel):
    """Anti-nuke: Check for mass channel deletion."""
    an_config = await bot.anti_nuke.get_config(channel.guild.id)
    if not an_config.get("enabled") or not an_config.get("modules", {}).get("anti_channel_delete"):
        return

    async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
        executor = entry.user
        if executor and executor.id != bot.user.id:
            if not bot.anti_nuke.has_bypass(an_config, executor):
                if await bot.anti_nuke.check_rate(channel.guild.id, "channel", an_config, executor.id):
                    await bot.anti_nuke.punish(channel.guild, executor, "Mass channel deletion detected")
                    await bot.anti_nuke.log_action(
                        channel.guild, "Mass Channel Deletion", channel.name,
                        f"{executor.name}", "Multiple channels deleted rapidly"
                    )


@bot.event
async def on_guild_role_create(role: discord.Role):
    """Anti-nuke: Check for mass role creation."""
    an_config = await bot.anti_nuke.get_config(role.guild.id)
    if not an_config.get("enabled") or not an_config.get("modules", {}).get("anti_role_create"):
        return

    async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
        executor = entry.user
        if executor and executor.id != bot.user.id:
            if not bot.anti_nuke.has_bypass(an_config, executor):
                if await bot.anti_nuke.check_rate(role.guild.id, "role", an_config, executor.id):
                    await bot.anti_nuke.punish(role.guild, executor, "Mass role creation detected")
                    try:
                        await role.delete(reason="AntiNuke: Reversing mass role creation")
                    except:
                        pass


@bot.event
async def on_guild_role_delete(role: discord.Role):
    """Anti-nuke: Check for mass role deletion."""
    an_config = await bot.anti_nuke.get_config(role.guild.id)
    if not an_config.get("enabled") or not an_config.get("modules", {}).get("anti_role_delete"):
        return

    async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
        executor = entry.user
        if executor and executor.id != bot.user.id:
            if not bot.anti_nuke.has_bypass(an_config, executor):
                if await bot.anti_nuke.check_rate(role.guild.id, "role", an_config, executor.id):
                    await bot.anti_nuke.punish(role.guild, executor, "Mass role deletion detected")


@bot.event
async def on_webhooks_update(channel: discord.TextChannel):
    """Anti-nuke: Check for webhook creation."""
    an_config = await bot.anti_nuke.get_config(channel.guild.id)
    if not an_config.get("enabled") or not an_config.get("modules", {}).get("anti_webhook_create"):
        return

    async for entry in channel.guild.audit_logs(limit=3, action=discord.AuditLogAction.webhook_create):
        executor = entry.user
        if executor and executor.id != bot.user.id:
            if not bot.anti_nuke.has_bypass(an_config, executor):
                if await bot.anti_nuke.check_rate(channel.guild.id, "webhook", an_config, executor.id):
                    await bot.anti_nuke.punish(channel.guild, executor, "Mass webhook creation detected")
                    try:
                        webhooks = await channel.webhooks()
                        for wh in webhooks:
                            if wh.user and wh.user.id == executor.id:
                                await wh.delete(reason="AntiNuke: Reversing webhook creation")
                    except:
                        pass


@bot.event
async def on_guild_update(before: discord.Guild, after: discord.Guild):
    """Anti-nuke: Check for dangerous guild updates."""
    an_config = await bot.anti_nuke.get_config(after.id)
    if not an_config.get("enabled") or not an_config.get("modules", {}).get("anti_guild_update"):
        return

    # Check for name change (potential raid)
    if before.name != after.name:
        async for entry in after.audit_logs(limit=1, action=discord.AuditLogAction.guild_update):
            executor = entry.user
            if executor and executor.id != bot.user.id:
                if not bot.anti_nuke.has_bypass(an_config, executor):
                    await bot.anti_nuke.punish(after, executor, f"Unauthorized server name change: {before.name} → {after.name}")
                    try:
                        await after.edit(name=before.name, reason="AntiNuke: Reversing name change")
                    except:
                        pass


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    """Handle 24/7 mode and voice state changes."""
    if member.id == bot.user.id:
        if before.channel and not after.channel:
            # Bot was disconnected
            player = bot._voice_clients.get(member.guild.id)
            if player and player._247_mode:
                # Reconnect for 24/7 mode
                try:
                    voice_client = await before.channel.connect(reconnect=True)
                    bot._voice_clients[member.guild.id].channel = before.channel
                except:
                    pass


@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    """Global error handler."""
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        perms = ", ".join(error.missing_permissions).replace('_', ' ').title()
        await ctx.send(embed=error_embed(f"You need **{perms}** permission!"), delete_after=10)
    elif isinstance(error, commands.BotMissingPermissions):
        perms = ", ".join(error.missing_permissions).replace('_', ' ').title()
        await ctx.send(embed=error_embed(f"I need **{perms}** permission!"), delete_after=10)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=error_embed(f"Missing argument: `{error.param.name}`\nUse `!help {ctx.command}` for usage."), delete_after=15)
    elif isinstance(error, commands.BadArgument):
        await ctx.send(embed=error_embed(f"Bad argument: {str(error)}"), delete_after=10)
    elif isinstance(error, commands.NotOwner):
        await ctx.send(embed=error_embed("Owner only command!"), delete_after=5)
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(embed=error_embed(f"⏳ Cooldown! Try again in **{format_time(error.retry_after)}**"), delete_after=5)
    elif isinstance(error, commands.MaxConcurrencyReached):
        await ctx.send(embed=error_embed("This command is already running!"), delete_after=5)
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send(embed=error_embed("Member not found!"), delete_after=5)
    elif isinstance(error, commands.RoleNotFound):
        await ctx.send(embed=error_embed("Role not found!"), delete_after=5)
    elif isinstance(error, commands.ChannelNotFound):
        await ctx.send(embed=error_embed("Channel not found!"), delete_after=5)
    elif isinstance(error, commands.CheckFailure):
        await ctx.send(embed=error_embed("You cannot use this command!"), delete_after=5)
    else:
        print(f"Error in {ctx.command}: {type(error).__name__}: {error}")
        traceback.print_exc()
        await ctx.send(embed=error_embed(f"An unexpected error occurred!\n```\n{type(error).__name__}: {str(error)[:500]}\n```"), delete_after=15)


# ============================================================
# SETUP & RUN
# ============================================================
async def setup():
    await bot.add_cog(LytrixCommands(bot))
    print("✅ All cogs loaded!")

async def main():
    async with bot:
        await setup()
        # Read token from environment or config
token = BOT_TOKEN
if token == "PUT_YOUR_BOT_TOKEN_HERE":
    print("⚠️ No token set! Open main.py and edit BOT_TOKEN, CLIENT_ID, and OWNER_IDS at the top.")
            print("Running in demo mode...")
            return
        await bot.start(token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Lytrix Bot shutting down...")
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
