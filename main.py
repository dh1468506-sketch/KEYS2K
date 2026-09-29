import discord
from discord.ext import commands
import random
import string
import os

TOKEN = os.environ.get('TOKEN')

keys = {}

def generar_key():
    chars = string.ascii_uppercase + string.digits
    return 'MONO-' + ''.join(random.choice(chars) for _ in range(8))

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

class KeyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎁 Obtener Key", style=discord.ButtonStyle.green, custom_id="get_key_btn")
    async def get_key(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        if user_id in keys:
            if keys[user_id].get('baneada'):
                await interaction.response.send_message("❌ Tu key fue baneada.", ephemeral=True)
                return
            await interaction.response.send_message(f"🔑 Tu key es:\n```{keys[user_id]['key']}```", ephemeral=True)
            return
        nueva_key = generar_key()
        while nueva_key in [k['key'] for k in keys.values()]:
            nueva_key = generar_key()
        keys[user_id] = {'key': nueva_key, 'user_name': str(interaction.user), 'baneada': False}
        await interaction.response.send_message(f"🔑 **Tu key única:**\n```{nueva_key}```\n⚠️ No la compartas.", ephemeral=True)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    embed = discord.Embed(title="🔑 MONOCHROME by_LOLMP3", description="Tocá el botón para obtener tu **key única**.", color=discord.Color.purple())
    embed.set_footer(text="No la compartas, es personal")
    await ctx.message.delete()
    await ctx.send(embed=embed, view=KeyView())

@bot.command()
@commands.has_permissions(administrator=True)
async def listarkeys(ctx):
    if not keys:
        await ctx.send("No hay keys registradas.")
        return
    txt = "**Keys registradas:**\n"
    for uid, data in keys.items():
        estado = "🚫 BANEADA" if data.get('baneada') else "✅ Activa"
        txt += f"`{data['key']}` - {data['user_name']} - {estado}\n"
    await ctx.send(txt[:2000])

@bot.command()
@commands.has_permissions(administrator=True)
async def banear(ctx, key: str):
    for uid, data in keys.items():
        if data['key'] == key:
            data['baneada'] = True
            await ctx.send(f"✅ Key baneada: `{key}`")
            return
    await ctx.send(f"❌ No encontré esa key.")

@bot.event
async def on_ready():
    bot.add_view(KeyView())
    print(f'✅ Bot conectado: {bot.user.name}')

bot.run(TOKEN)
