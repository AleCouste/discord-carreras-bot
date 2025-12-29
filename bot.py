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

estamina = {}            # {user_id: valor}
carrera_activa = False
participantes = {}       # {user_id: metros}
tipo_carrera = None      # sprint / medium / long

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
async def crear_carrera(ctx, tipo: str):
    global carrera_activa, participantes, tipo_carrera

    tipo = tipo.lower()

    if tipo not in GASTO_ESTAMINA:
        await ctx.send("❌ Tipo inválido. Usá: sprint / medium / long")
        return

    carrera_activa = True
    tipo_carrera = tipo
    participantes = {}

    await ctx.send(
        f"🏁 **¡Carrera iniciada!**\n"
        f"📌 Tipo de carrera: **{tipo.upper()}**\n"
        f"👉 Usá `!unirse` para participar."
    )

@bot.command()
@commands.has_permissions(administrator=True)
async def finalizar_carrera(ctx):
    global carrera_activa, participantes, tipo_carrera

    if not carrera_activa:
        await ctx.send("❌ No hay ninguna carrera activa.")
        return

    carrera_activa = False

    if not participantes:
        await ctx.send("🏁 Carrera finalizada sin participantes.")
        tipo_carrera = None
        return

    ranking = sorted(participantes.items(), key=lambda x: x[1], reverse=True)

    mensaje = "🏆 **RESULTADOS FINALES**\n"
    for i, (uid, metros) in enumerate(ranking, start=1):
        user = await bot.fetch_user(uid)
        mensaje += f"{i}. {user.display_name} — {metros} m\n"

    participantes = {}
    tipo_carrera = None
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

    mensaje = f"🏆 **POSICIONES ({tipo_carrera.upper()})**\n"
    for i, (uid, metros) in enumerate(ranking, start=1):
        user = await bot.fetch_user(uid)
        mensaje += f"{i}. {user.display_name} — {metros} m\n"

    await ctx.send(mensaje)

# =========================
# COMANDO PRINCIPAL
# =========================

@bot.command()
async def correr(ctx, velocidad: int):
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

    gasto = GASTO_ESTAMINA[tipo_carrera]

    if estamina[user_id] < gasto:
        await ctx.send("🥵 Estás demasiado cansado para correr este turno.")
        return

    dado = random.randint(1, 10)
    metros = velocidad * dado // 10

    estamina[user_id] -= gasto
    participantes[user_id] += metros

    await ctx.send(
        f"🏁 **CARRERA ({tipo_carrera.upper()})**\n"
        f"🎲 Dado: {dado}\n"
        f"⚡ Velocidad: {velocidad}\n"
        f"🏃 Avanzás: **{metros} m**\n"
        f"📏 Total acumulado: **{participantes[user_id]} m**\n"
        f"🔥 Gasto de estamina: {gasto}\n"
        f"🔋 Estamina restante: **{estamina[user_id]}**"
    )
    
@bot.command()
async def trote(ctx, velocidad: int):
    user_id = ctx.author.id

    if not carrera_activa or user_id not in participantes:
        await ctx.send("❌ No estás en una carrera activa.")
        return

    if user_id not in estamina:
        await ctx.send("❌ Primero usá `!set_estamina`.")
        return

    base = GASTO_ESTAMINA[tipo_carrera]
    recuperacion = base // 2

    dado = random.randint(1, 5)
    metros = velocidad * dado // 10

    estamina[user_id] += recuperacion
    participantes[user_id] += metros

    await ctx.send(
        f"🏁 **CARRERA ({tipo_carrera.upper()})**\n"
        f"⚡ Velocidad: {velocidad}\n"
        f"🎲 Dado: {dado}\n"
        f"📏 Avanzás: **{metros} m**\n"
        f"📏 Total acumulado: **{participantes[user_id]} m**\n"
        f"💚 Recuperás estamina: **+{recuperacion}**\n"
        f"🔋 Estamina actual: **{estamina[user_id]}**"
    )

@bot.command()
async def sprint(ctx, velocidad: int):
    user_id = ctx.author.id

    if not carrera_activa or user_id not in participantes:
        await ctx.send("❌ No estás en una carrera activa.")
        return

    if user_id not in estamina:
        await ctx.send("❌ Primero usá `!set_estamina`.")
        return

    base = GASTO_ESTAMINA[tipo_carrera]
    gasto = base * 2

    dado = random.randint(5, 15)

    # FALLO CONTROLADO
    if dado == 5:
        await ctx.send(
            f"⚡ **SPRINT FALLIDO**\n"
            f"🎲 Dado: 5\n"
            f"😖 Tropiezas al acelerar.\n"
            f"📏 No avanzás metros.\n"
            f"🔋 Estamina conservada: **{estamina[user_id]}**"
        )
        return

    if estamina[user_id] < gasto:
        await ctx.send("🥵 No tenés estamina suficiente para sprintar.")
        return

    metros = velocidad * dado // 10

    estamina[user_id] -= gasto
    participantes[user_id] += metros

    await ctx.send(
        f"🏁 **CARRERA ({tipo_carrera.upper()})**\n"
        f"⚡ Velocidad: {velocidad}\n"
        f"🎲 Dado: {dado}\n"
        f"📏 Avanzás: **{metros} m**\n"
        f"📏 Total acumulado: **{participantes[user_id]} m**\n"
        f"🔥 Gasto de estamina: **-{gasto}**\n"
        f"🔋 Estamina restante: **{estamina[user_id]}**"
    )

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Lero lero no podes\n https://tenor.com/view/umamusume-satono-diamond-lick-funny-gif-17230432331182465957")


# =========================
# INICIO DEL BOT
# =========================

bot.run(os.getenv("DISCORD_TOKEN"))

