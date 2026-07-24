import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta

class Reminders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminders = {}

    @app_commands.command(name="reminder", description="Créer un rappel")
    @app_commands.describe(
        duree="Durée (ex: 10m, 2h, 1d)",
        message="Le message de rappel"
    )
    async def reminder(self, interaction: discord.Interaction, duree: str, message: str):
        try:
            unit = duree[-1]
            value = int(duree[:-1])
            if unit == "s":
                seconds = value
            elif unit == "m":
                seconds = value * 60
            elif unit == "h":
                seconds = value * 3600
            elif unit == "d":
                seconds = value * 86400
            else:
                return await interaction.response.send_message("❌ Format: Xs/Xm/Xh/Xd", ephemeral=True)
        except:
            return await interaction.response.send_message("❌ Format: Xs/Xm/Xh/Xd (ex: 10m, 2h)", ephemeral=True)

        if seconds > 604800:
            return await interaction.response.send_message("❌ Maximum: 7 jours.", ephemeral=True)

        await interaction.response.send_message(
            f"⏰ Rappel créé! Je te ping dans **{duree}**: {message}"
        )
        await asyncio.sleep(seconds)
        try:
            embed = discord.Embed(
                title="⏰ Rappel!",
                description=message,
                color=0x5865F2,
                timestamp=datetime.utcnow()
            )
            await interaction.user.send(embed=embed)
        except:
            pass

    @app_commands.command(name="poll-create", description="Créer un sondage interactif")
    @app_commands.describe(question="La question", option1="Option 1", option2="Option 2", option3="Option 3", option4="Option 4")
    async def poll_create(
        self, interaction: discord.Interaction,
        question: str,
        option1: str,
        option2: str,
        option3: str = "",
        option4: str = ""
    ):
        options = [option1, option2]
        if option3:
            options.append(option3)
        if option4:
            options.append(option4)
        emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣']
        desc = "\n".join([f"{emojis[i]} {opt}" for i, opt in enumerate(options)])
        embed = discord.Embed(title=f"📊 {question}", description=desc, color=0x5865F2)
        embed.set_footer(text=f"Sondage par {interaction.user}")
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        for i in range(len(options)):
            await msg.add_reaction(emojis[i])

    @app_commands.command(name="weather", description="Simuler la météo")
    @app_commands.describe(ville="Une ville (simulation)")
    async def weather(self, interaction: discord.Interaction, ville: str = "Paris"):
        import random
        temp = random.randint(-5, 40)
        conditions = ["☀️ Ensoleillé", "⛅ Partiellement nuageux", "☁️ Nuageux", "🌧️ Pluvieux", "⛈️ Orageux", "❄️ Neigeux"]
        condition = random.choice(conditions)
        humidity = random.randint(20, 95)
        wind = random.randint(0, 80)
        embed = discord.Embed(title=f"🌤️ Météo à {ville}", color=0x5865F2)
        embed.add_field(name="Température", value=f"{temp}°C")
        embed.add_field(name="Condition", value=condition)
        embed.add_field(name="Humidité", value=f"{humidity}%")
        embed.add_field(name="Vent", value=f"{wind} km/h")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="color-info", description="Informations sur une couleur")
    @app_commands.describe(hex_color="Couleur hex (ex: #FF0000)")
    async def color_info(self, interaction: discord.Interaction, hex_color: str):
        try:
            hex_clean = hex_color.replace("#", "")
            r = int(hex_clean[0:2], 16)
            g = int(hex_clean[2:4], 16)
            b = int(hex_clean[4:6], 16)
            embed = discord.Embed(title=f"🎨 Couleur {hex_color}", color=int(hex_clean, 16))
            embed.add_field(name="HEX", value=f"#{hex_clean}", inline=True)
            embed.add_field(name="RGB", value=f"rgb({r}, {g}, {b})", inline=True)
            embed.add_field(name="Int", value=str(int(hex_clean, 16)), inline=True)
            embed.add_field(name="HSL", value=f"hsl({self.rgb_to_hsl(r, g, b)})", inline=True)
            await interaction.response.send_message(embed=embed)
        except:
            await interaction.response.send_message("❌ Couleur hex invalide.", ephemeral=True)

    def rgb_to_hsl(self, r, g, b):
        r, g, b = r / 255.0, g / 255.0, b / 255.0
        mx, mn = max(r, g, b), min(r, g, b)
        l = (mx + mn) / 2
        if mx == mn:
            h = s = 0
        else:
            d = mx - mn
            s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
            if mx == r:
                h = (g - b) / d + (6 if g < b else 0)
            elif mx == g:
                h = (b - r) / d + 2
            else:
                h = (r - g) / d + 4
            h /= 6
        return f"{int(h * 360)}, {int(s * 100)}%, {int(l * 100)}%"

    @app_commands.command(name="timestamp", description="Créer un timestamp Discord")
    @app_commands.describe(date="Date (YYYY-MM-DD HH:MM)", format="Format (R/D/t/T/f)")
    async def timestamp(self, interaction: discord.Interaction, date: str, format: str = "f"):
        from datetime import datetime as dt
        try:
            d = dt.strptime(date, "%Y-%m-%d %H:%M")
            unix = int(d.timestamp())
            formats = {"R": "R", "D": "D", "t": "t", "T": "T", "f": "f", "F": "F"}
            f = formats.get(format, "f")
            await interaction.response.send_message(
                f"`<t:{unix}:{f}>` = <t:{unix}:{f}>",
                ephemeral=True
            )
        except:
            await interaction.response.send_message("❌ Format: YYYY-MM-DD HH:MM", ephemeral=True)

    @app_commands.command(name="encode", description="Encoder du texte en base64")
    @app_commands.describe(texte="Le texte à encoder")
    async def encode(self, interaction: discord.Interaction, texte: str):
        import base64
        encoded = base64.b64encode(texte.encode()).decode()
        await interaction.response.send_message(f"🔐 `{encoded}`")

    @app_commands.command(name="decode", description="Décoder du base64")
    @app_commands.describe(texte="Le texte à décoder")
    async def decode(self, interaction: discord.Interaction, texte: str):
        import base64
        try:
            decoded = base64.b64decode(texte.encode()).decode()
            await interaction.response.send_message(f"🔓 `{decoded}`")
        except:
            await interaction.response.send_message("❌ Texte base64 invalide.", ephemeral=True)

    @app_commands.command(name="qr", description="Générer un QR code (texte)")
    @app_commands.describe(texte="Le texte/URL à encoder")
    async def qr(self, interaction: discord.Interaction, texte: str):
        await interaction.response.send_message(
            f"📱 QR Code pour: `{texte}`\n"
            f"[Génère-le ici](https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={texte})"
        )

    @app_commands.command(name="ascii", description="Convertir du texte en ASCII art")
    @app_commands.describe(texte="Le texte (1-10 caractères)")
    async def ascii(self, interaction: discord.Interaction, texte: str):
        if len(texte) > 10:
            return await interaction.response.send_message("❌ Max 10 caractères.", ephemeral=True)
        big_fonts = {
            'A': ['  ██  ', ' ████ ', '██  ██', '██████', '██  ██'],
            'B': ['█████ ', '██  ██', '█████ ', '██  ██', '█████ '],
            'C': [' ████ ', '██    ', '██    ', '██    ', ' ████ '],
            'D': ['████  ', '██ ██ ', '██  ██', '██ ██ ', '████  '],
            'E': ['██████', '██    ', '████  ', '██    ', '██████'],
            'F': ['██████', '██    ', '████  ', '██    ', '██    '],
            'G': [' ████ ', '██    ', '██ ███', '██  ██', ' ████ '],
            'H': ['██  ██', '██  ██', '██████', '██  ██', '██  ██'],
            'I': ['██████', '  ██  ', '  ██  ', '  ██  ', '██████'],
            'J': ['██████', '    ██', '    ██', '██  ██', ' ████ '],
            'K': ['██  ██', '██ ██ ', '████  ', '██ ██ ', '██  ██'],
            'L': ['██    ', '██    ', '██    ', '██    ', '██████'],
            'M': ['██  ██', '██████', '██████', '██  ██', '██  ██'],
            'N': ['██  ██', '███ ██', '██████', '██ ███', '██  ██'],
            'O': [' ████ ', '██  ██', '██  ██', '██  ██', ' ████ '],
            'P': ['█████ ', '██  ██', '█████ ', '██    ', '██    '],
            'Q': [' ████ ', '██  ██', '██  ██', '██ ██ ', ' ██ ██'],
            'R': ['█████ ', '██  ██', '█████ ', '██ ██ ', '██  ██'],
            'S': [' ████ ', '██    ', ' ████ ', '    ██', ' ████ '],
            'T': ['██████', '  ██  ', '  ██  ', '  ██  ', '  ██  '],
            'U': ['██  ██', '██  ██', '██  ██', '██  ██', ' ████ '],
            'V': ['██  ██', '██  ██', '██  ██', ' ████ ', '  ██  '],
            'W': ['██  ██', '██  ██', '██████', '██████', '██  ██'],
            'X': ['██  ██', ' ████ ', '  ██  ', ' ████ ', '██  ██'],
            'Y': ['██  ██', ' ████ ', '  ██  ', '  ██  ', '  ██  '],
            'Z': ['██████', '   ██ ', '  ██  ', ' ██   ', '██████'],
            ' ': ['      ', '      ', '      ', '      ', '      '],
            '!': ['  ██  ', '  ██  ', '  ██  ', '      ', '  ██  '],
            '0': [' ████ ', '██  ██', '██  ██', '██  ██', ' ████ '],
            '1': ['  ██  ', ' ███  ', '  ██  ', '  ██  ', '██████'],
            '2': [' ████ ', '    ██', ' ████ ', '██    ', '██████'],
            '3': [' ████ ', '    ██', ' ████ ', '    ██', ' ████ '],
            '4': ['██  ██', '██  ██', '██████', '    ██', '    ██'],
            '5': ['██████', '██    ', '█████ ', '    ██', '█████ '],
            '6': [' ████ ', '██    ', '█████ ', '██  ██', ' ████ '],
            '7': ['██████', '    ██', '   ██ ', '  ██  ', '  ██  '],
            '8': [' ████ ', '██  ██', ' ████ ', '██  ██', ' ████ '],
            '9': [' ████ ', '██  ██', ' █████', '    ██', ' ████ '],
        }
        result = ["", "", "", "", ""]
        for char in texte.upper():
            if char in big_fonts:
                for i in range(5):
                    result[i] += big_fonts[char][i] + " "
            elif char.upper() in big_fonts:
                for i in range(5):
                    result[i] += big_fonts[char.upper()][i] + " "
        art = "\n".join(result)
        await interaction.response.send_message(f"```\n{art}\n```")

async def setup(bot):
    await bot.add_cog(Reminders(bot))
