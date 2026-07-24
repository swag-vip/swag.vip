import discord
from discord.ext import commands
from discord import app_commands
import random
import aiohttp
import asyncio
import json
from io import BytesIO

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="8ball", description="Magic 8-ball")
    @app_commands.describe(question="Ta question")
    async def eightball(self, interaction: discord.Interaction, question: str):
        responses = [
            "🟢 Oui, absolument!", "🟢 Sans aucun doute", "🟢 C'est sûr",
            "🟢 Je pense que oui", "🟢 Probablement", "🟢 Les signes disent oui",
            "🟡 Peut-être", "🟡 Je ne peux pas dire", "🟡 Reviens plus tard",
            "🔴 Non", "🔴 Jamais", "🔴 Ne compte pas dessus",
            "🔴 C'est non", "🟡 Je doute fort", "🟢 Definitivement!",
            "🟡 Hmmm, laisse-moi réfléchir...", "🔴 HELL NO",
            "🟢 OUI OUI OUI!", "🟡 Mouais...", "🔴 Nah"
        ]
        embed = discord.Embed(title="🎱 Magic 8-Ball", color=0x9B59B6)
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Réponse", value=random.choice(responses), inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="coinflip", description="Lancer une pièce")
    async def coinflip(self, interaction: discord.Interaction):
        result = random.choice(["🪙 Pile", "🪙 Face"])
        embed = discord.Embed(title="🪙 Pile ou Face", description=result, color=0xF1C40F)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dice", description="Lancer des dés")
    @app_commands.describe(dice="Nombre de dés (ex: 2d6)")
    async def dice(self, interaction: discord.Interaction, dice: str = "1d6"):
        try:
            count, sides = map(int, dice.lower().split("d"))
            if count < 1 or count > 25 or sides < 1 or sides > 100:
                return await interaction.response.send_message("❌ Max: 25 dés, 100 faces.", ephemeral=True)
            rolls = [random.randint(1, sides) for _ in range(count)]
            total = sum(rolls)
            embed = discord.Embed(title="🎲 Lancer de dés", color=0xE74C3C)
            embed.add_field(name="Résultat", value=" + ".join(map(str, rolls)), inline=False)
            embed.add_field(name="Total", value=str(total), inline=True)
            await interaction.response.send_message(embed=embed)
        except:
            await interaction.response.send_message("❌ Format: XdY (ex: 2d6)", ephemeral=True)

    @app_commands.command(name="reverse", description="Inverser un texte")
    @app_commands.describe(texte="Le texte à inverser")
    async def reverse(self, interaction: discord.Interaction, texte: str):
        await interaction.response.send_message(f"🔄 {texte[::-1]}")

    @app_commands.command(name="mock", description="Moquer un texte (Alternating Case)")
    @app_commands.describe(texte="Le texte à moquer")
    async def mock(self, interaction: discord.Interaction, texte: str):
        mocked = "".join([c.upper() if i % 2 else c.lower() for i, c in enumerate(texte)])
        await interaction.response.send_message(f"Mocking: {mocked}")

    @app_commands.command(name="rate", description="Noter quelque chose")
    @app_commands.describe(chose="Ce que tu veux noter")
    async def rate(self, interaction: discord.Interaction, chose: str):
        rating = random.randint(0, 100)
        bar = "█" * (rating // 10) + "░" * (10 - rating // 10)
        embed = discord.Embed(title="⭐ Rating", color=0xF1C40F)
        embed.add_field(name=chose, value=f"**{rating}/100**\n`{bar}`")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ship", description="Shipper deux membres")
    @app_commands.describe(user1="Premier membre", user2="Deuxième membre")
    async def ship(self, interaction: discord.Interaction, user1: discord.Member, user2: discord.Member):
        love = random.randint(0, 100)
        if love < 20:
            emoji = "💔"
            msg = "Pas du tout compatible..."
        elif love < 40:
            emoji = "😐"
            msg = "Bof bof..."
        elif love < 60:
            emoji = "💕"
            msg = "Ça pourrait marcher!"
        elif love < 80:
            emoji = "❤️"
            msg = "Gros potentiel!"
        else:
            emoji = "💍"
            msg = "LE MARIAGE!"
        bar = "❤️" * (love // 10) + "🖤" * (10 - love // 10)
        embed = discord.Embed(title=f"💕 {user1.display_name} x {user2.display_name}", color=0xFF69B4)
        embed.add_field(name="Amour", value=f"**{love}%**\n`{bar}`", inline=False)
        embed.add_field(name="Verdict", value=f"{emoji} {msg}", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="meme", description="Afficher un meme aléatoire")
    async def meme(self, interaction: discord.Interaction):
        memes = [
            "https://media.tenor.com/images/memes/programming-meme.jpg",
            "https://i.kym-cdn.com/photos/images/newsfeed/001/840/253/d2c.jpg",
            "https://i.imgur.com/GB2mF8s.jpg",
        ]
        embed = discord.Embed(title="😂 Meme", color=0xFF6B6B)
        embed.set_image(url=random.choice(memes))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="joke", description="Raconter une blague")
    async def joke(self, interaction: discord.Interaction):
        jokes = [
            ("Pourquoi les plongeurs plongent-ils toujours en arrière?", "Parce que sinon ils tombent dans le bateau."),
            ("Que dit un bonhomme de neige en été?", "Oh non, je fonds!"),
            ("Qu'est-ce qu'un crocodile qui surveille la piscine?", "Un garde-froc."),
            ("Pourquoi les étudiants mangent de la grenouille?", "Parce qu'elle est pleine de cuisses (connaissances)."),
            ("Qu'est-ce qu'un canif?", "Un pif qui a gardé un f."),
            ("Pourquoi le chien traverse-t-il la route?", "Pour aller de l'autre côte! (cliché mais classique)"),
            ("Que fait une fraise sur un cheval?", "Tagada tagada!"),
            ("Quel est le sport le plus silencieux?", "Le lancer de poids (personne ne le voit)."),
        ]
        q, a = random.choice(jokes)
        embed = discord.Embed(title="😄 Blague", color=0xFEE75C)
        embed.add_field(name="?", value=q, inline=False)
        embed.add_field(name="!", value=a, inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="choose", description="Choisir parmi des options")
    @app_commands.describe(options="Options séparées par ;")
    async def choose(self, interaction: discord.Interaction, options: str):
        opts = [o.strip() for o in options.split(";") if o.strip()]
        if len(opts) < 2:
            return await interaction.response.send_message("❌ Au moins 2 options séparées par `;`.", ephemeral=True)
        chosen = random.choice(opts)
        embed = discord.Embed(title="🤔 Choix", description=f"J'ai choisi: **{chosen}**", color=0x5865F2)
        embed.add_field(name="Options", value=", ".join(opts))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rps", description="Pierre Papier Ciseaux")
    @app_commands.describe(choix="pierre/papier/ciseaux")
    async def rps(self, interaction: discord.Interaction, choix: str):
        choix = choix.lower()
        if choix not in ["pierre", "papier", "ciseaux"]:
            return await interaction.response.send_message("❌ Choisis: pierre, papier ou ciseaux.", ephemeral=True)
        bot_choice = random.choice(["pierre", "papier", "ciseaux"])
        emojis = {"pierre": "🪨", "papier": "📄", "ciseaux": "✂️"}
        if choix == bot_choice:
            result = "🤝 Égalité!"
            color = 0xFEE75C
        elif (choix == "pierre" and bot_choice == "ciseaux") or \
             (choix == "papier" and bot_choice == "pierre") or \
             (choix == "ciseaux" and bot_choice == "papier"):
            result = "🏆 Tu gagnes!"
            color = 0x57F287
        else:
            result = "💀 Tu perds!"
            color = 0xED4245
        embed = discord.Embed(title="🎮 Pierre Papier Ciseaux", color=color)
        embed.add_field(name="Toi", value=f"{emojis[choix]} {choix.title()}", inline=True)
        embed.add_field(name="Bot", value=f"{emojis[bot_choice]} {bot_choice.title()}", inline=True)
        embed.add_field(name="Résultat", value=result, inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="trivia", description="Question de culture générale")
    async def trivia(self, interaction: discord.Interaction):
        questions = [
            ("Quel est le plus grand océan?", ["Pacifique", "Atlantique", "Indien", "Arctique"], 0),
            ("Combien de pattes a une araignée?", ["6", "8", "10", "12"], 1),
            ("Qui a peint la Joconde?", ["Picasso", "Da Vinci", "Van Gogh", "Monet"], 1),
            ("Quel est le plus grand mammifère?", ["Éléphant", "Baleine bleue", "Girafe", "Hippopotame"], 1),
            ("Quelle est la capitale du Japon?", ["Pékin", "Séoul", "Tokyo", "Osaka"], 2),
        ]
        q, options, correct = random.choice(questions)
        embed = discord.Embed(title="🧠 Quiz", description=q, color=0x9B59B6)
        emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣']
        desc = "\n".join([f"{emojis[i]} {opt}" for i, opt in enumerate(options)])
        embed.add_field(name="Options", value=desc)
        embed.set_footer(text=f"Réponse dans 15 secondes...")
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        for i in range(len(options)):
            await msg.add_reaction(emojis[i])
        def check(reaction, user):
            return user == interaction.user and str(reaction.emoji) in emojis
        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=15.0, check=check)
            index = emojis.index(str(reaction.emoji))
            if index == correct:
                await interaction.followup.send(f"✅ Bonne réponse! C'était **{options[correct]}**!")
            else:
                await interaction.followup.send(f"❌ Mauvais! C'était **{options[correct]}**.")
        except asyncio.TimeoutError:
            await interaction.followup.send(f"⏰ Temps écoulé! La réponse était **{options[correct]}**.")

    @app_commands.command(name="howgay", description="Mesurer le niveau de gay")
    @app_commands.describe(membre="Le membre")
    async def howgay(self, interaction: discord.Interaction, membre: discord.Member = None):
        membre = membre or interaction.user
        percentage = random.randint(0, 100)
        bar = "🌈" * (percentage // 10) + "⬛" * (10 - percentage // 10)
        embed = discord.Embed(title="🌈 Gay-O-Mètre", color=0xFF69B4)
        embed.add_field(name=membre.display_name, value=f"**{percentage}%**\n`{bar}`")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="simp", description="Vérifier le niveau de simp")
    @app_commands.describe(membre="Le membre")
    async def simp(self, interaction: discord.Interaction, membre: discord.Member = None):
        membre = membre or interaction.user
        percentage = random.randint(0, 100)
        embed = discord.Embed(title="💕 Simp-O-Mètre", color=0xFF69B4)
        embed.add_field(name=membre.display_name, value=f"**{percentage}%** simp")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pp", description="Voir le PP de quelqu'un (ASCII)")
    @app_commands.describe(membre="Le membre")
    async def pp(self, interaction: discord.Interaction, membre: discord.Member = None):
        membre = membre or interaction.user
        size = random.randint(1, 15)
        pp_art = "8" + "=" * size + "D"
        embed = discord.Embed(title=f"PP de {membre.display_name}", description=f"`{pp_art}`", color=0xFF69B4)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="clap", description="Ajouter des claps à un message")
    @app_commands.describe(texte="Le texte")
    async def clap(self, interaction: discord.Interaction, texte: str):
        clapped = " 👏 ".join(texte.split())
        await interaction.response.send_message(clapped)

    @app_commands.command(name="triggered", description="Image triggered d'un membre")
    @app_commands.describe(membre="Le membre")
    async def triggered(self, interaction: discord.Interaction, membre: discord.Member = None):
        membre = membre or interaction.user
        embed = discord.Embed(title="🔴 TRIGGERED", color=0xED4245)
        embed.set_image(url=membre.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="deletehistory", description="Demander à un ami d'effacer l'historique de navigation")
    @app_commands.describe(membre="Le membre")
    async def deletehistory(self, interaction: discord.Interaction, membre: discord.Member):
        await interaction.response.send_message(f"🧹 {membre.mention} EFFACE TON HISTORIQUE DE NAVIGATION! 😂")

    @app_commands.command(name="f", description="Payer ses respects")
    @app_commands.describe(raison="La raison")
    async def pay_respects(self, interaction: discord.Interaction, raison: str = "quelque chose"):
        await interaction.response.send_message(f"🫡 **F** pour {raison}")

    @app_commands.command(name="owo", description="OwO-ifier un texte")
    @app_commands.describe(texte="Le texte à OwO-ifier")
    async def owo(self, interaction: discord.Interaction, texte: str):
        replacements = {'r': 'w', 'R': 'W', 'l': 'w', 'L': 'W'}
        result = ""
        for c in texte:
            result += replacements.get(c, c)
        owo_faces = [" OwO", " OwO!", " OwU", " OwO~", " >w<", " UwU"]
        await interaction.response.send_message(result + random.choice(owo_faces))

    @app_commands.command(name="8ball-ask", description="Demander au 8-ball")
    @app_commands.describe(question="Ta question au 8-ball")
    async def ball_ask(self, interaction: discord.Interaction, question: str):
        await eightball(interaction, question)

async def setup(bot):
    await bot.add_cog(Fun(bot))
