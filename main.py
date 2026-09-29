import discord
from discord.ext import commands
import random
import string
import os
import threading
from flask import Flask, request, jsonify
import json

TOKEN = os.environ.get('TOKEN')
KEY_FILE = 'keys.json'

app = Flask('__name__')

def cargar_keys():
    if os.path.exists(KEY_FILE):
        try:
            with open(KEY_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def guardar_keys(keys):
    with open(KEY_FILE, 'w') as f:
        json.dump(keys, f, indent=2)

def generar_key():
    chars = string.ascii_uppercase + string.digits
    return 'MONO-' + ''.join(random.choice(chars) for _ in range(8))

keys = cargar_keys()

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
        guardar_keys(keys)
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
    k = cargar_keys()
    if not k:
        await ctx.send("No hay keys registradas.")
        return
    txt = "**Keys registradas:**\n"
    for uid, data in k.items():
        estado = "🚫 BANEADA" if data.get('baneada') else "✅ Activa"
        txt += f"`{data['key']}` - {data['user_name']} - {estado}\n"
    await ctx.send(txt[:2000])

@bot.command()
@commands.has_permissions(administrator=True)
async def banear(ctx, key: str):
    k = cargar_keys()
    for uid, data in k.items():
        if data['key'] == key:
            data['baneada'] = True
            guardar_keys(k)
            await ctx.send(f"✅ Key baneada: `{key}`")
            return
    await ctx.send(f"❌ No encontré esa key.")

@bot.event
async def on_ready():
    bot.add_view(KeyView())
    print(f'✅ Bot conectado: {bot.user.name}')

@app.route('/verify', methods=['POST'])
def verify():
    try:
        data = request.get_json()
        key = data.get('key', '')
        k = cargar_keys()
        for uid, info in k.items():
            if info['key'] == key:
                if info.get('baneada'):
                    return jsonify({'valid': False, 'reason': 'baneada'})
                return jsonify({'valid': True})
        return jsonify({'valid': False, 'reason': 'no existe'})
    except Exception as e:
        return jsonify({'valid': False, 'reason': str(e)})

@app.route('/')
def home():
    return "MONOCHROME Key Server activo"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask, daemon=True).start()
bot.run(TOKEN)
