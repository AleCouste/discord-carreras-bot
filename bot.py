import discord
from discord.ext import commands
import random
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# DATOS
# =========================

estamina = {}  # {user_id: valor}

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
# COMANDOS
# =========================

@bot.command()
async def ping(ctx):
    await ctx.send("🏁 Pong!")

@bot.command()
async def set_estamina(ctx, cantidad: int):
    if cantidad <= 0:
        await ctx.send("❌ La estamina debe ser mayor a 0.")
        return

    estamina[ctx.author.id] = cantidad
    await ctx.send(f"🔋 Estamina establecida en **{cantidad}**.")

@bot.command()
async def carrera(ctx, velocidad: int, tipo: str):
    user_id = ctx.author.id

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

    # CÁLCULO DE CARRERA
    dado = random.randint(1, 10)
    metros = velocidad * dado // 10

    # DESCUENTO
    estamina[user_id] -= gasto

    await ctx.send(
        f"🏁 **CARRERA ({tipo.upper()})**\n"
        f"🎲 Dado: {dado}\n"
        f"⚡ Velocidad: {velocidad}\n"
        f"🏃 Metros recorridos: **{metros}**\n"
        f"🔥 Gasto de estamina: {gasto}\n"
        f"🔋 Estamina restante: **{estamina[user_id]}**"
    )

bot.run(os.getenv("DISCORD_TOKEN"))
