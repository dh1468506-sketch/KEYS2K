import discord
from discord.ext import commands
import random
import string
import os
import threading
from flask import Flask, request, jsonify
import json
from datetime import datetime, timedelta

TOKEN = os.environ.get('TOKEN')
KEY_FILE = 'keys.json'
HORAS_EXPIRACION = 24

SCRIPTS = {
    "monochrome": "🎮 MONOCHROME",
    "beta": "🔥 BETA TEST FIXED"
}

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

def key_expirada(info):
    try:
        expira = datetime.fromisoformat(info['expira'])
        return datetime.utcnow() > expira
    except:
        return False

keys = cargar_keys()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

class ScriptSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=nombre, value=codigo)
            for codigo, nombre in SCRIPTS.items()
        ]
        super().__init__(placeholder="🎯 Elegí el script...", options=options)

    async def callback(self, interaction: discord.Interaction):
        codigo = self.values[0]
        nombre = SCRIPTS[codigo]
        user_id = f"{interaction.user.id}_{codigo}"
        k = cargar_keys()
        
        if user_id in k:
            info = k[user_id]
            if info.get('baneada'):
                await interaction.response.send_message("❌ Tu key fue baneada.", ephemeral=True)
                return
            if key_expirada(info):
                nueva = generar_key()
                info['key'] = nueva
                info['creada'] = str(datetime.utcnow())
                info['expira'] = str(datetime.utcnow() + timedelta(hours=HORAS_EXPIRACION))
                guardar_keys(k)
                await interaction.response.send_message(
                    f"⏰ Tu key anterior expiró.\n🔑 **Key NUEVA para {nombre}:**\n```{nueva}```\n⏳ Dura {HORAS_EXPIRACION}h.",
                    ephemeral=True
                )
                return
            expira = datetime.fromisoformat(info['expira'])
            diff = expira - datetime.utcnow()
            horas = int(diff.total_seconds() // 3600)
            mins = int((diff.total_seconds() % 3600) // 60)
            await interaction.response.send_message(
                f"🔑 Tu key para **{nombre}** es:\n```{info['key']}```\n⏳ Expira en **{horas}h {mins}m**.",
                ephemeral=True
            )
            return
        
        nueva_key = generar_key()
        while nueva_key in [d['key'] for d in k.values()]:
            nueva_key = generar_key()
        
        k[user_id] = {
            'key': nueva_key,
            'user_name': str(interaction.user),
            'script': codigo,
            'baneada': False,
            'creada': str(datetime.utcnow()),
            'expira': str(datetime.utcnow() + timedelta(hours=HORAS_EXPIRACION))
        }
        guardar_keys(k)
        
        await interaction.response.send_message(
            f"🔑 **Tu key para {nombre}:**\n```{nueva_key}```\n⏳ Dura **{HORAS_EXPIRACION}h**.\n⚠️ Solo funciona en {nombre}.",
            ephemeral=True
        )

class KeyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ScriptSelect())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    embed = discord.Embed(
        title="🔑 KEYS by_LOLMP3",
        description="Elegí el script abajo y te doy tu key única.",
        color=discord.Color.purple()
    )
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
        if data.get('baneada'):
            estado = "🚫"
        elif key_expirada(data):
            estado = "⏰"
        else:
            expira = datetime.fromisoformat(data['expira'])
            diff = expira - datetime.utcnow()
            horas = int(diff.total_seconds() // 3600)
            estado = f"✅ {horas}h"
        sc = data.get('script', '?')
        txt += f"`{data['key']}` - {data['user_name']} - {sc} - {estado}\n"
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
        script = data.get('script', '')
        k = cargar_keys()
        for uid, info in k.items():
            if info['key'] == key:
                if info.get('baneada'):
                    return jsonify({'valid': False, 'reason': 'baneada'})
                if key_expirada(info):
                    return jsonify({'valid': False, 'reason': 'expirada'})
                if script and info.get('script') != script:
                    return jsonify({'valid': False, 'reason': 'script incorrecto'})
                return jsonify({'valid': True})
        return jsonify({'valid': False, 'reason': 'no existe'})
    except Exception as e:
        return jsonify({'valid': False, 'reason': str(e)})

@app.route('/')
def home():
    return "Key Server activo"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask, daemon=True).start()
bot.run(TOKEN)
