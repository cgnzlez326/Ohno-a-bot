import discord
import sqlite3
import random
import asyncio
import yaml

client = discord.Client()
conn = sqlite3.connect("database/botdb.db")
cursor = conn.cursor()
url_imgs = [
    "https://s1.eestatic.com/2020/04/06/como/Declaracion_Renta_2019_-_2020-Bitcoin-Criptomonedas-Declaracion_de_la_renta-Agencia_Tributaria-Como_hacer_480462598_149797020_1024x576.jpg",
    "https://www.crypto-news-flash.com/wp-content/uploads/2019/06/Evdokimov-Maxim-Bitcoin-1000x600.jpg",
    "https://criptopasion.com/wp-content/uploads/2020/05/a-historia-do-bitcoin-em-menos-de-8-minutos.jpg",
    "https://veja.abril.com.br/wp-content/uploads/2017/10/economia-bitcoins-20000101-003.jpg"]
with open('config\config.yml', 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)


@client.event
async def on_ready():
    print("{0.user} es un bot muy poco inteligente, como su programador xd".format(client))
    guilds = client.guilds
    cursor.execute("SELECT guild_identifier FROM guild;")
    guild_result = cursor.fetchall()
    saved_guilds = [item for query in guild_result for item in query]
    cursor.execute("SELECT user_token FROM discord_member;")
    members_result = cursor.fetchall()
    saved_members = [item for query in members_result for item in query]
    for guild in guilds:
        if str(guild.id) not in saved_guilds:
            insert_guild = """
            INSERT INTO guild (guild_name, guild_identifier, currency_id, prefix) VALUES (?, ?, ?, ?);
            """
            guild_data = (guild.name, guild.id, 1, '!')
            cursor.execute(insert_guild, guild_data)
        for member in guild.members:
            if str(member.id) not in saved_members:
                member_fullname = str(member.name) + "#" + str(member.discriminator)
                member_guild = str(member.guild.id)
                cursor.execute("SELECT id FROM guild WHERE guild_identifier = ?;", [member_guild])
                member_guild_id = cursor.fetchall()
                insert_member = """
                INSERT INTO discord_member (user_token, user_name) VALUES (?, ?);
                """
                members_data = (str(member.id), member_fullname)
                cursor.execute(insert_member, members_data)
                cursor.execute("SELECT id FROM discord_member WHERE user_token = ?;", [str(member.id)])
                member_id = cursor.fetchall()
                guild_member_data = (member_guild_id[0][0], member_id[0][0])
                insert_guild_member = """
                INSERT INTO guild_member (guild_id, discord_member_id) VALUES (?, ?);
                """
                cursor.execute(insert_guild_member, guild_member_data)
    conn.commit()
    cursor.close()
    await client.change_presence(activity=discord.Game(name="Botando plata en FGO"))


@client.event
async def on_message(message):
    message_cursor = conn.cursor()
    message_cursor.execute("SELECT prefix FROM guild WHERE guild_identifier = ?", [str(message.guild.id)])
    prefix = message_cursor.fetchall()
    message_cursor.execute("""
        SELECT plural_name, currency_name FROM currency WHERE id = (SELECT currency_id FROM guild WHERE guild_identifier = ?);
        """, [str(message.guild.id)])
    q_currency_name = message_cursor.fetchall()
    p_currency_name, currency_name = q_currency_name[0][0], q_currency_name[0][1]
    message_cursor.close()

    def p_or_s(gamble):
        if gamble == 1:
            return currency_name
        else:
            return p_currency_name

    if message.author == client.user:
        return

    if message.content.startswith("{0}ping".format(prefix[0][0])) or message.content.startswith(
            "{0}Ping".format(prefix[0][0])):
        await message.channel.send('pong')

    if message.content.startswith("{0}coinflip".format(prefix[0][0])) or message.content.startswith(
            "{0}Coinflip".format(prefix[0][0])):
        cursor_plata = conn.cursor()
        guild_id = str(message.guild.id)
        member_id = str(message.author.id)
        q_string = (guild_id, member_id)
        cursor_plata.execute('''SELECT q_currency FROM member_currency 
            WHERE guild_member_id IN (SELECT id FROM guild_member 
                WHERE guild_id = (SELECT id FROM guild WHERE guild_identifier = ?) 
                AND discord_member_id 
                    IN (SELECT id FROM discord_member WHERE user_token = ?))''', q_string)
        plata = cursor_plata.fetchall()
        bet = 0
        cursor_plata.close()

        if not plata or int(plata[0][0]) == 0:
            await message.channel.send(f"Pobre culiao, teni 0 {p_currency_name} no puedes apostar")
            return
        try:
            str_bet = message.content.split(" ")[1]
            bet = int(str_bet)
            if bet <= int(plata[0][0]):
                answer_to_claim = await message.channel.send("Elige: {0}cara o {0}sello".format(prefix[0][0]))

                def answer_check(answer):
                    return (answer.content.startswith("{0}cara".format(prefix[0][0])) or answer.content.startswith(
                        "{0}sello".format(prefix[0][0]))) and answer.author == message.author

                message_sent = await client.wait_for("message", check=answer_check, timeout=15.0)
                await answer_to_claim.delete(delay=7.0)
                aleatorio = random.randint(1, 100)
                act_cursor = conn.cursor()
                act_cursor.execute('''SELECT id FROM member_currency 
                                WHERE guild_member_id IN (SELECT id FROM guild_member 
                                WHERE guild_id = (SELECT id FROM guild WHERE guild_identifier = ?) 
                                AND discord_member_id 
                                IN (SELECT id FROM discord_member WHERE user_token = ?))''', q_string)
                results = act_cursor.fetchall()
                print(aleatorio)
                if aleatorio <= 49 and message_sent.content.startswith("{0}cara".format(prefix[0][0])):
                    embeded = discord.Embed(title=f"Cara, Ganaste {bet} {p_or_s(bet)}", color=0xFFD700)
                    embeded.set_image(url="https://i.imgur.com/7lBfLAa.jpg")
                    await message.channel.send(embed=embeded)
                    act_cursor.execute(f"""
                            UPDATE member_currency SET q_currency = q_currency + {bet} WHERE id = ?
                            """, [results[0][0]])
                elif aleatorio <= 49 and message_sent.content.startswith("{0}sello".format(prefix[0][0])):
                    embeded = discord.Embed(title=f"Cara, Perdiste {bet} {p_or_s(bet)}", color=0xFFD700)
                    embeded.set_image(url="https://i.imgur.com/7lBfLAa.jpg")
                    await message.channel.send(embed=embeded)
                    act_cursor.execute(f"""
                            UPDATE member_currency SET q_currency = q_currency - {bet} WHERE id = ?
                            """, [results[0][0]])
                elif 49 < aleatorio <= 99 and message_sent.content.startswith("{0}sello".format(prefix[0][0])):
                    embeded = discord.Embed(title=f"Sello, Ganaste {bet} {p_or_s(bet)}", color=0xFFD700)
                    embeded.set_image(url="https://i.imgur.com/79rkmoK.jpg")
                    await message.channel.send(embed=embeded)
                    act_cursor.execute(f"""
                            UPDATE member_currency SET q_currency = q_currency + {bet} WHERE id = ?
                            """, [results[0][0]])
                elif 49 < aleatorio <= 99 and message_sent.content.startswith("{0}cara".format(prefix[0][0])):
                    embeded = discord.Embed(title=f"Sello, Perdiste {bet} {p_or_s(bet)}", color=0xFFD700)
                    embeded.set_image(url="https://i.imgur.com/79rkmoK.jpg")
                    await message.channel.send(embed=embeded)
                    act_cursor.execute(f"""
                            UPDATE member_currency SET q_currency = q_currency - {bet} WHERE id = ?
                            """, [results[0][0]])
                elif aleatorio == 100:
                    embeded = discord.Embed(title=f"Canto, perdiste {bet} {p_or_s(bet)} jajaxd", color=0xFFD700)
                    embeded.set_image(url="https://i.imgur.com/BRJM75J.jpg")
                    await message.channel.send(embed=embeded)
                    act_cursor.execute(f"""
                            UPDATE member_currency SET q_currency = q_currency - {bet} WHERE id = ?
                            """, [results[0][0]])
                else:
                    message_to_delete = await message.channel.send(
                        f"Ha ocurrido un error, tu apuesta de {bet} {p_or_s(bet)} ha sido reintegrada")
                    await message_to_delete.delete(delay=5.0)
                conn.commit()
                act_cursor.close()
            else:
                await message.channel.send("No posees fondos suficientes para realizar dicha apuesta")
                return
        except ValueError:
            to_delete = await message.channel.send("Ingresa un número como apuesta.")
            await to_delete.delete(delay=5.0)
        except asyncio.TimeoutError:
            to_delete = await message.channel.send(
                f"No ingresaste una opción o ingresaste cualquier cosa a excepción de cara o sello, me diste cualquier pena hermano, te restablesco tu apuesta de {bet} {p_or_s(bet)}")
            await to_delete.delete(delay=7.0)
        except IndexError:
            to_delete = await message.channel.send("No ingresaste una apuesta")
            await to_delete.delete(delay=5.0)

    if random.randint(0, 20) == 14 and not message.content.startswith('{0}'.format(prefix[0][0])):
        embeded = discord.Embed(title=f"Un {currency_name} salvaje ha aparecido!",
                                description="Llévatelo con {0}claim".format(prefix[0][0]), color=0xFFD700)
        embeded.set_image(url=url_imgs[random.randint(0, 3)])
        msg = await message.channel.send(embed=embeded)

        def gain_currency(mensaje):
            return mensaje.content.startswith('{0}claim'.format(prefix[0][0]))

        try:
            dbcursor = conn.cursor()
            answer_to_claim = await client.wait_for("message", check=gain_currency, timeout=10.0)
            message_sent = await message.channel.send(f"+10 {p_currency_name}" + " a {0.author}".format(answer_to_claim))
            guild_id = str(answer_to_claim.guild.id)
            member_id = str(answer_to_claim.author.id)
            q_string = (guild_id, member_id)
            dbcursor.execute("""SELECT id FROM member_currency 
            WHERE guild_member_id IN (SELECT id FROM guild_member 
                WHERE guild_id = (SELECT id FROM guild WHERE guild_identifier = ?) 
                AND discord_member_id 
                    IN (SELECT id FROM discord_member WHERE user_token = ?))""", q_string)
            results = dbcursor.fetchall()
            if not results:
                dbcursor.execute("""
                INSERT INTO member_currency (guild_member_id, q_currency) VALUES 
                    ((SELECT id FROM guild_member WHERE guild_id = 
                        (SELECT id FROM guild WHERE guild_identifier = ?) 
                    AND discord_member_id = 
                        (SELECT id FROM discord_member WHERE user_token = ?)), 10)
                """, q_string)
            else:
                dbcursor.execute("""
                UPDATE member_currency SET q_currency = q_currency + 10 WHERE id = ?
                """, [results[0][0]])
            conn.commit()
            dbcursor.close()
            ms = await message.channel.fetch_message(msg.id)
            await ms.delete()
            ms = await message.channel.fetch_message(message_sent.id)
            await ms.delete(delay=3.0)
            await answer_to_claim.delete(delay=3.0)
        except asyncio.TimeoutError:
            ms = await message.channel.fetch_message(msg.id)
            await ms.delete()

    if message.content.startswith("{0}plata".format(prefix[0][0])) or message.content.startswith(
            "{0}Plata".format(prefix[0][0])):
        cursor_plata = conn.cursor()
        guild_id = str(message.guild.id)
        member_id = str(message.author.id)
        q_string = (guild_id, member_id)
        cursor_plata.execute('''SELECT q_currency FROM member_currency 
            WHERE guild_member_id IN (SELECT id FROM guild_member 
                WHERE guild_id = (SELECT id FROM guild WHERE guild_identifier = ?) 
                AND discord_member_id 
                    IN (SELECT id FROM discord_member WHERE user_token = ?))''', q_string)
        plata = cursor_plata.fetchall()

        if not plata or int(plata[0][0]) == 0:
            await message.channel.send(f"Teni 0 {p_currency_name}, hermanito tay terrible pobre")
        else:
            await message.channel.send(f"Teni {plata[0][0]} {p_or_s(int(plata[0][0]))}")
        cursor_plata.close()


client.run(config['token']['id'])
