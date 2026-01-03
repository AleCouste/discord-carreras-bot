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

estamina = {}   # {user_id: valor}
carreras = {}   # {nombre: {creador, tipo, participantes}}

GASTO_ESTAMINA = {
    "sprint": 60,
    "medium": 80,
    "long": 100
}

# =========================
# FUNCIONES AUXILIARES
# =========================

def carrera_de_usuario(user_id):
    for nombre, carrera in carreras.items():
        if user_id in carrera["participantes"]:
            return nombre, carrera
    return None, None

# =========================
# EVENTO READY
# =========================

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

# =========================
# COMANDOS BÁSICOS
# =========================

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong! El bot está activo.")

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
# CARRERAS
# =========================

@bot.command()
async def crear_carrera(ctx, nombre: str, tipo: str):
    if nombre in carreras:
        await ctx.send("❌ Ya existe una carrera con ese nombre.")
        return

    tipo = tipo.lower()
    if tipo not in GASTO_ESTAMINA:
        await ctx.send("❌ Tipo inválido. Usá sprint / medium / long.")
        return

    carreras[nombre] = {
        "creador": ctx.author.id,
        "tipo": tipo,
        "participantes": {}
    }

    await ctx.send(
        f"🏁 **Carrera creada**\n"
        f"📛 Nombre: **{nombre}**\n"
        f"📌 Tipo: **{tipo.upper()}**\n"
        f"👤 Creador: {ctx.author.display_name}\n"
        f"👉 Usá `!unirse \"{nombre}\"`"
    )

@bot.command()
async def unirse(ctx, nombre: str):
    if nombre not in carreras:
        await ctx.send("❌ Esa carrera no existe.")
        return

    ya_nombre, _ = carrera_de_usuario(ctx.author.id)
    if ya_nombre:
        await ctx.send(f"❌ Ya estás participando en **{ya_nombre}**.")
        return

    carreras[nombre]["participantes"][ctx.author.id] = 0
    await ctx.send(f"✅ Te uniste a la carrera **{nombre}**.")

@bot.command()
async def finalizar_carrera(ctx, nombre: str):
    if nombre not in carreras:
        await ctx.send("❌ Esa carrera no existe.")
        return

    carrera = carreras[nombre]

    if ctx.author.id != carrera["creador"]:
        await ctx.send("🚫 Solo el creador puede finalizar esta carrera.")
        return

    participantes = carrera["participantes"]

    ranking = sorted(participantes.items(), key=lambda x: x[1], reverse=True)

    mensaje = f"🏆 **RESULTADOS — {nombre}**\n"
    for i, (uid, metros) in enumerate(ranking, start=1):
        user = await bot.fetch_user(uid)
        mensaje += f"{i}. {user.display_name} — {metros} m\n"

    del carreras[nombre]
    await ctx.send(mensaje)

@bot.command()
async def posiciones(ctx, nombre: str):
    if nombre not in carreras:
        await ctx.send("❌ Esa carrera no existe.")
        return

    participantes = carreras[nombre]["participantes"]

    if not participantes:
        await ctx.send("📭 No hay participantes.")
        return

    ranking = sorted(participantes.items(), key=lambda x: x[1], reverse=True)

    mensaje = f"📊 **POSICIONES — {nombre}**\n"
    for i, (uid, metros) in enumerate(ranking, start=1):
        user = await bot.fetch_user(uid)
        mensaje += f"{i}. {user.display_name} — {metros} m\n"

    await ctx.send(mensaje)

# =========================
# ACCIONES DE CARRERA
# =========================

@bot.command()
async def correr(ctx, velocidad: int):
    nombre, carrera = carrera_de_usuario(ctx.author.id)
    if not carrera:
        await ctx.send("❌ No estás en una carrera.")
        return

    if ctx.author.id not in estamina:
        await ctx.send("❌ Usá `!set_estamina` primero.")
        return

    tipo = carrera["tipo"]
    gasto = GASTO_ESTAMINA[tipo]

    if estamina[ctx.author.id] < gasto:
        await ctx.send("🥵 No tenés estamina suficiente.")
        return

    dado = random.randint(1, 10)
    metros = velocidad * dado // 10

    estamina[ctx.author.id] -= gasto
    carrera["participantes"][ctx.author.id] += metros

    await ctx.send(
        f"🏃 **CORRER — {nombre} ({tipo.upper()})**\n"
        f"🎲 Dado: {dado}\n"
        f"📏 +{metros} m\n"
        f"📍 Total: {carrera['participantes'][ctx.author.id]} m\n"
        f"🔋 Estamina: {estamina[ctx.author.id]}"
    )

@bot.command()
async def trote(ctx, velocidad: int):
    nombre, carrera = carrera_de_usuario(ctx.author.id)
    if not carrera:
        await ctx.send("❌ No estás en una carrera.")
        return

    tipo = carrera["tipo"]
    base = GASTO_ESTAMINA[tipo]
    recupera = base // 2

    dado = random.randint(1, 5)
    metros = velocidad * dado // 10

    estamina[ctx.author.id] = estamina.get(ctx.author.id, 0) + recupera
    carrera["participantes"][ctx.author.id] += metros

    await ctx.send(
        f"🚶 **TROTE — {nombre} ({tipo.upper()})**\n"
        f"🎲 Dado: {dado}\n"
        f"📏 +{metros} m\n"
        f"📍 Total: {carrera['participantes'][ctx.author.id]} m\n"
        f"💚 +{recupera} estamina\n"
        f"🔋 {estamina[ctx.author.id]}"
    )

@bot.command()
async def sprint(ctx, velocidad: int):
    nombre, carrera = carrera_de_usuario(ctx.author.id)
    if not carrera:
        await ctx.send("❌ No estás en una carrera.")
        return

    tipo = carrera["tipo"]
    gasto = GASTO_ESTAMINA[tipo] * 2

    if estamina.get(ctx.author.id, 0) < gasto:
        await ctx.send("🥵 No tenés estamina suficiente.")
        return

    dado = random.randint(5, 15)

    if dado == 5:
        await ctx.send("⚡ Sprint fallido, no avanzás metros.")
        return

    metros = velocidad * dado // 10
    estamina[ctx.author.id] -= gasto
    carrera["participantes"][ctx.author.id] += metros

    await ctx.send(
        f"🔥 **SPRINT — {nombre} ({tipo.upper()})**\n"
        f"🎲 Dado: {dado}\n"
        f"📏 +{metros} m\n"
        f"📍 Total: {carrera['participantes'][ctx.author.id]} m\n"
        f"🔋 Estamina: {estamina[ctx.author.id]}"
    )

# =========================
# ADMIN
# =========================

@bot.command()
@commands.has_permissions(administrator=True)
async def admin_carreras(ctx, accion: str = None, *, nombre: str = None):
    if accion is None:
        if not carreras:
            await ctx.send("📭 No hay carreras activas.")
            return

        mensaje = "📋 **CARRERAS ACTIVAS**\n"
        for n, c in carreras.items():
            creador = await bot.fetch_user(c["creador"])
            mensaje += f"\n🏁 {n} — {c['tipo'].upper()} | 👤 {creador.display_name}"
        await ctx.send(mensaje)
        return

    if accion.lower() == "borrar" and nombre in carreras:
        del carreras[nombre]
        await ctx.send(f"🧹 Carrera **{nombre}** eliminada.")
        return

    await ctx.send("❌ Acción inválida.")

# =========================
# INICIO
# =========================

bot.run(os.getenv("DISCORD_TOKEN"))

