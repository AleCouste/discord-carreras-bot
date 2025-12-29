import discord
from discord.ext import commands
import random
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# DATOS GLOBALES
# =========================

# Estamina por usuario
estamina = {}  # {user_id: valor}

# Carrera multijugador
carrera_activa = False
participantes = {}  # {user_id: metros}

GASTO_ESTAMINA = {
    "sprint": 60,
    "medium": 80,
    "long": 100
}

# =========================
# EVENTOS
# =========================

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

# =========================
# COMANDOS BÁSICOS
# =========================

@bot.command()
async def ping(ctx):
    await ctx.send("🏁 Pong!")

# =========================
# ESTAMINA
# =========================

@bot.command()
async def set_estamina(ctx, cantidad: int):
    if cantidad <= 0:
        await ctx.send("❌ La estamina debe ser mayor a 0.")
        return

    estamina[ctx.author.id] = cantidad
    await ctx.send(f"🔋 Estamina establecida en **{cantidad}**.")

@bot.command()
async def status(ctx):
    valor = estamina.get(ctx.author.id)
    if valor is None:
        await ctx.send("❌ No tenés estamina seteada.")
    else:
        await ctx.send(f"🔋 Estamina actual: **{valor}**")

# =========================
# CARRERA MULTIJUGADOR
# =========================

@bot.command()
@commands.has_permissions(administrator=True)
async def crear_carrera(ctx):
    global carrera_activa, participantes

    carrera_activa = True
    participantes = {}

    await ctx.send("🏁 **¡Carrera iniciada!** Usá `!unirse` para participar.")

@bot.command()
@commands.has_permissions(administrator=True)
async def finalizar_carrera(ctx):
    global carrera_activa, participantes

    if not carrera_activa:
        await ctx.send("❌ No hay ninguna carrera activa.")
        return

    carrera_activa = False

    if not participantes:
        await ctx.send("🏁 Carrera finalizada sin participantes.")
        return

    ranking = sorted(participantes.items(), key=lambda x: x[1], reverse=True)

    mensaje = "🏆 **RESULTADOS FINALES**\n"
    for i, (uid, metros) in enumerate(ranking, start=1):
        user = await bot.fetch_user(uid)
        mensaje += f"{i}. {user.display_name} — {metros} m\n"

    participantes = {}
    await ctx.send(mensaje)

@bot.command()
async def unirse(ctx):
    if not carrera_activa:
        await ctx.send("❌ No hay ninguna carrera activa.")
        return

    if ctx.author.id in participantes:
        await ctx.send("❌ Ya estás en la carrera.")
        return

    participantes[ctx.author.id] = 0
    await ctx.send(f"✅ {ctx.author.display_name} se unió a la carrera.")

@bot.command()
async def posiciones(ctx):
    if not carrera_activa or not participantes:
        await ctx.send("❌ No hay carrera en curso.")
        return

    ranking = sorted(participantes.items(), key=lambda x: x[1], reverse=True)

    mensaje = "🏆 **POSICIONES ACTUALES**\n"
    for i, (uid, metros) in enumerate(ranking, start=1):
        user = await bot.fetch_user(uid)
        mensaje += f"{i}. {user.display_name} — {metros} m\n"

    await ctx.send(mensaje)

# =========================
# COMANDO PRINCIPAL
# =========================

@bot.command()
async def carrera(ctx, velocidad: int, tipo: str):
    user_id = ctx.author.id

    if not carrera_activa:
        await ctx.send("❌ No hay carrera activa.")
        return

    if user_id not in participantes:
        await ctx.send("❌ No estás participando en esta carrera.")
        return

    if user_id not in estamina:
        await ctx.send("❌ Primero usá `!set_estamina`.")
        return

    tipo = tipo.lower()

    if tipo not in GASTO_ESTAMINA:
        await ctx.send("❌ Tipo inválido. Usá: sprint / medium / long")
        return

    gasto = GASTO_ESTAMINA[tipo]

    if estamina[user_id] < gasto:
        await ctx.send("🥵 Estás demasiado cansado para correr este turno.")
        return

    # Cálculo
    dado = random.randint(1, 10)
    metros = velocidad * dado // 10

    # Aplicar resultados
    estamina[user_id] -= gasto
    participantes[user_id] += metros

    await ctx.send(
        f"🏁 **CARRERA ({tipo.upper()})**\n"
        f"🎲 Dado: {dado}\n"
        f"⚡ Velocidad: {velocidad}\n"
        f"🏃 Avanzás: **{metros} m**\n"
        f"📏 Total acumulado: **{participantes[user_id]} m**\n"
        f"🔥 Gasto de estamina: {gasto}\n"
        f"🔋 Estamina restante: **{estamina[user_id]}**"
    )

# =========================
# INICIO DEL BOT
# =========================

bot.run(os.getenv("DISCORD_TOKEN"))

