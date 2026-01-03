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

estamina = {}

carreras = {}

TIPOS = {
    "sprint": {"min": 800, "max": 1400, "curvas": 1, "gasto": 60},
    "medium": {"min": 1401, "max": 2400, "curvas": 2, "gasto": 80},
    "long": {"min": 2401, "max": 3600, "curvas": 3, "gasto": 100},
}

# =========================
# FUNCIONES AUXILIARES
# =========================

def tipo_por_distancia(dist):
    for t, d in TIPOS.items():
        if d["min"] <= dist <= d["max"]:
            return t
    return None

def carrera_de_usuario(uid):
    for nombre, carrera in carreras.items():
        if uid in carrera["participantes"]:
            return nombre, carrera
    return None, None

def en_curva(carrera, metros):
    tramo = carrera["meta"] / (carrera["curvas"] + 1)
    for i in range(1, carrera["curvas"] + 1):
        if tramo * i - 50 <= metros <= tramo * i + 50:
            return True
    return False

async def finalizar_carrera(nombre, carrera):
    ranking = sorted(carrera["participantes"].items(), key=lambda x: x[1], reverse=True)
    msg = f"🏆 **RESULTADOS — {nombre}**\n"
    for i, (uid, m) in enumerate(ranking, 1):
        user = await bot.fetch_user(uid)
        msg += f"{i}. {user.display_name} — {m} m\n"
    del carreras[nombre]
    return msg

# =========================
# READY
# =========================

@bot.event
async def on_ready():
    print(f"Bot listo como {bot.user}")

# =========================
# UTILIDAD
# =========================

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! `{round(bot.latency * 1000)} ms`")

# =========================
# ESTAMINA
# =========================

@bot.command()
async def set_estamina(ctx, cantidad: int):
    if cantidad <= 0:
        return await ctx.send("❌ Cantidad inválida.")
    estamina[ctx.author.id] = cantidad
    await ctx.send(f"🔋 Estamina: **{cantidad}**")

@bot.command()
async def status(ctx):
    await ctx.send(f"🔋 Estamina: **{estamina.get(ctx.author.id, 0)}**")

# =========================
# CARRERAS
# =========================

@bot.command()
async def crear_carrera(ctx, nombre: str, distancia: int):
    if nombre in carreras:
        return await ctx.send("❌ Ya existe esa carrera.")

    tipo = tipo_por_distancia(distancia)
    if not tipo:
        return await ctx.send("❌ Distancia inválida (800–3600 m).")

    carreras[nombre] = {
        "creador": ctx.author.id,
        "distancia": distancia,
        "tipo": tipo,
        "curvas": TIPOS[tipo]["curvas"],
        "meta": distancia,
        "participantes": {}
    }

    await ctx.send(
        f"🏁 **Carrera creada**\n"
        f"📛 {nombre}\n"
        f"📏 {distancia} m\n"
        f"📌 {tipo.upper()} | Curvas: {TIPOS[tipo]['curvas']}\n"
        f"👉 `!unirse {nombre}`"
    )

@bot.command()
async def unirse(ctx, nombre: str):
    if nombre not in carreras:
        return await ctx.send("❌ Carrera inexistente.")

    ya, _ = carrera_de_usuario(ctx.author.id)
    if ya:
        return await ctx.send("❌ Ya estás en otra carrera.")

    carreras[nombre]["participantes"][ctx.author.id] = 0
    await ctx.send(f"✅ Unido a **{nombre}**")

@bot.command()
async def posiciones(ctx, nombre: str):
    if nombre not in carreras:
        return await ctx.send("❌ No existe.")

    ranking = sorted(
        carreras[nombre]["participantes"].items(),
        key=lambda x: x[1],
        reverse=True
    )

    if not ranking:
        return await ctx.send("📭 Sin participantes.")

    msg = f"📊 **POSICIONES — {nombre}**\n"
    for i, (uid, m) in enumerate(ranking, 1):
        user = await bot.fetch_user(uid)
        msg += f"{i}. {user.display_name} — {m} m\n"
    await ctx.send(msg)

# =========================
# ACCIONES
# =========================

@bot.command()
async def trote(ctx, velocidad: int):
    nombre, carrera = carrera_de_usuario(ctx.author.id)
    if not carrera:
        return await ctx.send("❌ No estás en carrera.")

    tipo = carrera["tipo"]
    recupera = TIPOS[tipo]["gasto"]  # recupera TODO

    dado = random.randint(1, 5)
    metros = velocidad * dado // 10

    metros_antes = carrera["participantes"][ctx.author.id]
    carrera["participantes"][ctx.author.id] += metros
    metros_despues = carrera["participantes"][ctx.author.id]

    estamina[ctx.author.id] = estamina.get(ctx.author.id, 0) + recupera

    msg_curva = ""
    antes = en_curva(carrera, metros_antes)
    despues = en_curva(carrera, metros_despues)

    if not antes and despues:
        msg_curva = "\n🌀 **Entrás en una curva**"
    elif antes and not despues:
        msg_curva = "\n➡️ **Salís de la curva**"

    await ctx.send(
        f"🚶 **TROTE ({tipo.upper()})**\n"
        f"🎲 Dado: {dado}\n"
        f"⚡ Velocidad: {velocidad}\n"
        f"🏃 Avanzás: **{metros} m**\n"
        f"📏 Total acumulado: **{metros_despues} m**\n"
        f"💚 Recuperás estamina: +{recupera}\n"
        f"🔋 Estamina actual: **{estamina[ctx.author.id]}**"
        f"{msg_curva}"
    )


@bot.command()
async def correr(ctx, velocidad: int):
    nombre, carrera = carrera_de_usuario(ctx.author.id)
    if not carrera:
        return await ctx.send("❌ No estás en carrera.")

    tipo = carrera["tipo"]
    gasto = TIPOS[tipo]["gasto"]

    if estamina.get(ctx.author.id, 0) < gasto:
        return await ctx.send("🥵 Sin estamina.")

    metros_antes = carrera["participantes"][ctx.author.id]

    dado = random.randint(1, 10)
    metros = velocidad * dado // 10

    estamina[ctx.author.id] -= gasto
    carrera["participantes"][ctx.author.id] += metros
    metros_despues = carrera["participantes"][ctx.author.id]

    # 🏁 victoria automática
    if metros_despues >= carrera["meta"]:
        msg = await finalizar_carrera(nombre, carrera)
        return await ctx.send(msg)

    # 🌀 detección de entrada / salida de curva
    msg_curva = ""
    antes = en_curva(carrera, metros_antes)
    despues = en_curva(carrera, metros_despues)

    if not antes and despues:
        msg_curva = "\n🌀 **Entrás en una curva**"
    elif antes and not despues:
        msg_curva = "\n➡️ **Salís de la curva**"

    await ctx.send(
        f"🏁 **CARRERA ({tipo.upper()})**\n"
        f"🎲 Dado: {dado}\n"
        f"⚡ Velocidad: {velocidad}\n"
        f"🏃 Avanzás: **{metros} m**\n"
        f"📏 Total acumulado: **{metros_despues} m**\n"
        f"🔥 Gasto de estamina: {gasto}\n"
        f"🔋 Estamina restante: **{estamina[ctx.author.id]}**"
        f"{msg_curva}"
    )


@bot.command()
async def sprint(ctx, velocidad: int):
    nombre, carrera = carrera_de_usuario(ctx.author.id)
    if not carrera:
        return await ctx.send("❌ No estás en carrera.")

    tipo = carrera["tipo"]
    gasto = TIPOS[tipo]["gasto"] * 2

    if estamina.get(ctx.author.id, 0) < gasto:
        return await ctx.send("🥵 Sin estamina.")

    curva = en_curva(carrera, carrera["participantes"][ctx.author.id])
    dado = random.randint(5, 15)

    if (not curva and dado == 5) or (curva and 5 <= dado <= 7):
        return await ctx.send(
            f"⚡ **SPRINT FALLIDO**\n"
            f"🎲 {dado}\n"
            f"💥 Perdíste el control.\n"
            f"🔋 Estamina conservada."
        )

    metros = velocidad * dado // 10
    estamina[ctx.author.id] -= gasto
    carrera["participantes"][ctx.author.id] += metros

    if carrera["participantes"][ctx.author.id] >= carrera["meta"]:
        msg = await finalizar_carrera(nombre, carrera)
        return await ctx.send(msg)

    await ctx.send(
        f"⚡ **SPRINT ({tipo.upper()})**\n"
        f"🎲 Dado: {dado}\n"
        f"⚡ Velocidad: {velocidad}\n"
        f"🏃 Avanzás: **{metros} m**\n"
        f"📏 Total acumulado: **{metros_despues} m**\n"
        f"🔥 Gasto de estamina: {gasto}\n"
        f"🔋 Estamina restante: **{estamina[ctx.author.id]}**"
        f"{msg_curva}"
    )

# =========================
# ADMIN
# =========================

@bot.command()
@commands.has_permissions(administrator=True)
async def admin_carreras(ctx, accion: str = None, *, nombre: str = None):
    if not accion:
        if not carreras:
            return await ctx.send("📭 No hay carreras.")
        msg = "📋 **CARRERAS ACTIVAS**\n"
        for n, c in carreras.items():
            user = await bot.fetch_user(c["creador"])
            msg += f"\n🏁 {n} — {c['tipo'].upper()} — {user.display_name}"
        return await ctx.send(msg)

    if accion == "borrar" and nombre in carreras:
        del carreras[nombre]
        await ctx.send(f"🧹 Carrera **{nombre}** eliminada.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 Sin permisos.")

bot.run(os.getenv("DISCORD_TOKEN"))


