import asyncio
from datetime import datetime
import discord
from discord.ext import commands
from discord.ui import Select, View, Button
from sqlFn import runSQLFn
import requests

token = "MTA5NjA2MTc2Mjk0OTg3MzgxNQ.GGKy5T.s1no8lKyMOLqrP7-SUrh8nHPLAg9ZIg1b8EF8Q"

intents = discord.Intents.all()
intents.message_content = True  # Enable the message content intent

bot = commands.Bot(command_prefix='!', intents=intents)
# Bybit API Base URL
BASE_URL = 'https://api.bybit.com'

# Public API Endpoint to get market data
MARKET_DATA_ENDPOINT = '/v2/public/tickers'


@bot.event
async def on_ready():
    print("Online")
    print(datetime.today())

    def get_market_data(symbol_name):
        url = f"{BASE_URL}{MARKET_DATA_ENDPOINT}?symbol={symbol_name}"
        response = requests.get(url)
        data = response.json()
        return data

    # 异步函数来查找市场价
    async def check_market_price():
        while True:
            # 在这里执行你的查找市场价的代码
            # 比如调用API获取市场价，处理数据等
            # 让你的查找市场价的逻辑在这个位置

            sqlFn = runSQLFn("select", "trade_order_record", {
                             "where": {"status": {"condition": "=", "value": "order", "type": "AND"}}})
            contents = sqlFn.sqlQuery()

            for content in contents:
                market_data = get_market_data(content["coin"])
                if market_data['ret_code'] == 0 and market_data['ret_msg'] == 'OK':
                    last_price = market_data['result'][0]['last_price']
                    mark_price = market_data['result'][0]['mark_price']
                    content_float_value = float(content["price"])
                    last_price_float_value = float(last_price)
                    mark_price_float_value = float(mark_price)

                    # ! LONG
                    if content["trend_type"] == "LONG" and content["order_type"] == "enter" and last_price_float_value <= content_float_value:
                        sqlFnE1 = runSQLFn("select", "trade_order", {"where": {
                                           "id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"}}})
                        dataE = sqlFnE1.sqlQuery()

                        sqlFnE2 = runSQLFn("update", "trade_order_record", {"where": {"id": {"condition": "=", "value": content["id"], "type": "AND"}}, "set": {
                            "status": "fill", "updated_at": datetime.today()}})
                        sqlFnE2.sqlQuery()

                        if dataE[0]["status"] == "order":
                            sqlFnE3 = runSQLFn("update", "trade_order", {"where": {"id": {"condition": "=", "value": dataE[0]["id"], "type": "AND"}},
                                                                         "set": {"enter_price": content_float_value, "status": "enter", "updated_at": datetime.today()}})
                            sqlFnE3.sqlQuery()
                        elif dataE[0]["status"] == "enter":
                            enter_price_float_value = float(
                                dataE[0]["enter_price"])
                            sqlFnE3 = runSQLFn("update", "trade_order", {"where": {"id": {"condition": "=", "value": dataE[0]["id"], "type": "AND"}},
                                                                         "set": {"enter_price": (enter_price_float_value + last_price_float_value) / 2, "updated_at": datetime.today()}})
                            sqlFnE3.sqlQuery()

                        sqlFnE4 = runSQLFn("select", "trade_order_record", {"where": {"trade_order_id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"},
                                                                                      "order_type": {"condition": "=", "value": "enter", "type": "AND"},
                                                                                      "status": {"condition": "=", "value": "order", "type": "AND"}}})
                        dataE2 = sqlFnE4.sqlQuery()

                        if len(dataE2) == 0:
                            sqlFnE5 = runSQLFn("update", "trade_order", {"where": {"id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"}},
                                                                         "set": {"status": "all enter", "updated_at": datetime.today()}})
                            sqlFnE5.sqlQuery()

                    if content["trend_type"] == "LONG" and content["order_type"] == "tp" and last_price_float_value >= content_float_value:
                        sqlFnT1 = runSQLFn("select", "trade_order", {"where": {
                                           "id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"}}})
                        dataT = sqlFnT1.sqlQuery()

                        if len(dataT) != 0:
                            if dataT[0]["status"] == "order":
                                sqlFnT2 = runSQLFn("update", "trade_order_record", {"where": {"trade_order_id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"},
                                                                                              "status": {"condition": "=", "value": "order", "type": "AND"}},
                                                                                    "set": {"status": "cancel", "updated_at": datetime.today()}})
                                sqlFnT2.sqlQuery()
                                sqlFnT3 = runSQLFn("update", "trade_order", {"where": {"id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"}},
                                                                             "set": {"status": "tp cancel", "updated_at": datetime.today()}})
                                sqlFnT3.sqlQuery()
                            else:
                                sqlFnT2 = runSQLFn("update", "trade_order_record", {"where": {"id": {"condition": "=", "value": content['id'], "type": "AND"},
                                                                                              "status": {"condition": "=", "value": "order", "type": "AND"}},
                                                                                    "set": {"status": "fill", "updated_at": datetime.today()}})
                                sqlFnT2.sqlQuery()
                                sqlFnT3 = runSQLFn("select", "trade_order_record", {"where": {"trade_order_id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"},
                                                                                              "order_type": {"condition": "=", "value": "tp", "type": "AND"},
                                                                                              "status": {"condition": "=", "value": "order", "type": "AND"}}})
                                dataT2 = sqlFnT3.sqlQuery()
                                enter_float_value = float(
                                    dataT[0]["enter_price"])
                                if len(dataT2) != 0:
                                    tp_number = int(dataT[0]["tp_number"]) + 1
                                    sqlFnT4 = runSQLFn("update", "trade_order", {"where": {"id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"}},
                                                                                 "set": {"status": f"tp {tp_number}", "tp_number": tp_number, "tp": last_price_float_value, "percentage": ((last_price_float_value - enter_float_value) / enter_float_value) * 100, "updated_at": datetime.today()}})
                                    sqlFnT4.sqlQuery()
                                    sqlFn = runSQLFn("insert", "trade_order_record", {"insertValue": {"keys": ["trade_order_id", "coin", "trend_type", "order_type", "price", "status"],
                                                                                                      "columns": [content['trade_order_id'], content['coin'], content['trend_type'], "sl", dataT[0]["enter_price"], "order"]}})
                                    sqlFn.sqlQuery()
                                else:
                                    tp_number = int(dataT[0]["tp_number"]) + 1
                                    sqlFnT4 = runSQLFn("update", "trade_order", {"where": {"id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"}},
                                                                                 "set": {"status": "full tp", "tp_number": tp_number, "tp": last_price_float_value, "percentage": ((last_price_float_value - enter_float_value) / enter_float_value) * 100, "updated_at": datetime.today()}})
                                    sqlFnT4.sqlQuery()
                                    sqlFnT5 = runSQLFn("update", "trade_order_record", {"where": {"trade_order_id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"},
                                                                                                  "status": {"condition": "=", "value": "order", "type": "AND"}},
                                                                                        "set": {"status": "cancel", "updated_at": datetime.today()}})
                                    sqlFnT5.sqlQuery()

                    if content["trend_type"] == "LONG" and content["order_type"] == "sl" and mark_price_float_value <= content_float_value:
                        sqlFnS = runSQLFn("select", "trade_order", {"where": {
                                          "id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"}}})
                        dataS = sqlFnS.sqlQuery()

                        sqlFnS1 = runSQLFn("select", "trade_order_record", {
                                           "where": {"id": {"condition": "=", "value": content['id'], "type": "AND"}}})
                        dataS1 = sqlFnS1.sqlQuery()

                        sqlFnS2 = runSQLFn("update", "trade_order_record", {"where": {"id": {"condition": "=", "value": content['id'], "type": "AND"},
                                                                                      "status": {"condition": "=", "value": "order", "type": "AND"}},
                                                                            "set": {"status": "fill", "updated_at": datetime.today()}})
                        sqlFnS2.sqlQuery()

                        if len(dataS) != 0:
                            sqlFnS3 = runSQLFn("update", "trade_order_record", {"where": {"trade_order_id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"},
                                                                                          "status": {"condition": "=", "value": "order", "type": "AND"}},
                                                                                "set": {"status": "cancel", "updated_at": datetime.today()}})
                            sqlFnS3.sqlQuery()

                            if dataS[0]["enter_price"] == dataS1[0]["price"]:
                                sqlFnS4 = runSQLFn("update", "trade_order", {"where": {"id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"}},
                                                                             "set": {"status": "be", "updated_at": datetime.today()}})
                                sqlFnS4.sqlQuery()
                            else:
                                sqlFnS4 = runSQLFn("update", "trade_order", {"where": {"id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"}},
                                                                             "set": {"status": "sl", "sl": mark_price_float_value, "percentage": ((mark_price_float_value - enter_float_value) / enter_float_value) * 100, "updated_at": datetime.today()}})
                                sqlFnS4.sqlQuery()

                    # ! SHORT
                    if content["trend_type"] == "SHORT" and content["order_type"] == "enter" and last_price_float_value >= content_float_value:
                        sqlFnE1 = runSQLFn("select", "trade_order", {"where": {
                                           "id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"}}})
                        dataE = sqlFnE1.sqlQuery()

                        sqlFnE2 = runSQLFn("update", "trade_order_record", {"where": {"id": {"condition": "=", "value": content["id"], "type": "AND"}}, "set": {
                            "status": "fill", "updated_at": datetime.today()}})
                        sqlFnE2.sqlQuery()

                        if dataE[0]["status"] == "order":
                            sqlFnE3 = runSQLFn("update", "trade_order", {"where": {"id": {"condition": "=", "value": dataE[0]["id"], "type": "AND"}},
                                                                         "set": {"enter_price": content_float_value, "status": "enter", "updated_at": datetime.today()}})
                            sqlFnE3.sqlQuery()
                        elif dataE[0]["status"] == "enter":
                            enter_price_float_value = float(
                                dataE[0]["enter_price"])
                            sqlFnE3 = runSQLFn("update", "trade_order", {"where": {"id": {"condition": "=", "value": dataE[0]["id"], "type": "AND"}},
                                                                         "set": {"enter_price": (enter_price_float_value + last_price_float_value) / 2, "updated_at": datetime.today()}})
                            sqlFnE3.sqlQuery()

                        sqlFnE4 = runSQLFn("select", "trade_order_record", {"where": {"trade_order_id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"},
                                                                                      "order_type": {"condition": "=", "value": "enter", "type": "AND"},
                                                                                      "status": {"condition": "=", "value": "order", "type": "AND"}}})
                        dataE2 = sqlFnE4.sqlQuery()

                        if len(dataE2) == 0:
                            sqlFnE5 = runSQLFn("update", "trade_order", {"where": {"id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"}},
                                                                         "set": {"status": "all enter", "updated_at": datetime.today()}})
                            sqlFnE5.sqlQuery()

                    if content["trend_type"] == "SHORT" and content["order_type"] == "tp" and last_price_float_value <= content_float_value:
                        sqlFnT1 = runSQLFn("select", "trade_order", {"where": {
                                           "id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"}}})
                        dataT = sqlFnT1.sqlQuery()

                        if len(dataT) != 0:
                            if dataT[0]["status"] == "order":
                                sqlFnT2 = runSQLFn("update", "trade_order_record", {"where": {"trade_order_id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"},
                                                                                              "status": {"condition": "=", "value": "order", "type": "AND"}},
                                                                                    "set": {"status": "cancel", "updated_at": datetime.today()}})
                                sqlFnT2.sqlQuery()
                                sqlFnT3 = runSQLFn("update", "trade_order", {"where": {"id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"}},
                                                                             "set": {"status": "tp cancel", "updated_at": datetime.today()}})
                                sqlFnT3.sqlQuery()
                            else:
                                sqlFnT2 = runSQLFn("update", "trade_order_record", {"where": {"id": {"condition": "=", "value": content['id'], "type": "AND"},
                                                                                              "status": {"condition": "=", "value": "order", "type": "AND"}},
                                                                                    "set": {"status": "fill", "updated_at": datetime.today()}})
                                sqlFnT2.sqlQuery()
                                sqlFnT3 = runSQLFn("select", "trade_order_record", {"where": {"trade_order_id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"},
                                                                                              "order_type": {"condition": "=", "value": "tp", "type": "AND"},
                                                                                              "status": {"condition": "=", "value": "order", "type": "AND"}}})
                                dataT2 = sqlFnT3.sqlQuery()
                                if len(dataT2) != 0:
                                    tp_number = int(dataT[0]["tp_number"]) + 1
                                    sqlFnT4 = runSQLFn("update", "trade_order", {"where": {"id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"}},
                                                                                 "set": {"status": f"tp {tp_number}", "tp_number": tp_number, "tp": last_price_float_value, "percentage": -(((last_price_float_value - enter_float_value) / enter_float_value) * 100), "updated_at": datetime.today()}})
                                    sqlFnT4.sqlQuery()
                                    sqlFn = runSQLFn("insert", "trade_order_record", {"insertValue": {"keys": ["trade_order_id", "coin", "trend_type", "order_type", "price", "status"],
                                                                                                      "columns": [content['trade_order_id'], content['coin'], content['trend_type'], "sl", dataT[0]["enter_price"], "order"]}})
                                    sqlFn.sqlQuery()
                                else:
                                    tp_number = int(dataT[0]["tp_number"]) + 1
                                    sqlFnT4 = runSQLFn("update", "trade_order", {"where": {"id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"}},
                                                                                 "set": {"status": "full tp", "tp_number": tp_number, "tp": last_price_float_value, "percentage": -(((last_price_float_value - enter_float_value) / enter_float_value) * 100), "updated_at": datetime.today()}})
                                    sqlFnT4.sqlQuery()
                                    sqlFnT5 = runSQLFn("update", "trade_order_record", {"where": {"trade_order_id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"},
                                                                                                  "status": {"condition": "=", "value": "order", "type": "AND"}},
                                                                                        "set": {"status": "cancel", "updated_at": datetime.today()}})
                                    sqlFnT5.sqlQuery()

                    if content["trend_type"] == "SHORT" and content["order_type"] == "sl" and mark_price_float_value >= content_float_value:
                        sqlFnS = runSQLFn("select", "trade_order", {"where": {
                                          "id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"}}})
                        dataS = sqlFnS.sqlQuery()

                        sqlFnS1 = runSQLFn("select", "trade_order_record", {
                                           "where": {"id": {"condition": "=", "value": content['id'], "type": "AND"}}})
                        dataS1 = sqlFnS1.sqlQuery()

                        sqlFnS2 = runSQLFn("update", "trade_order_record", {"where": {"id": {"condition": "=", "value": content['id'], "type": "AND"},
                                                                                      "status": {"condition": "=", "value": "order", "type": "AND"}},
                                                                            "set": {"status": "fill", "updated_at": datetime.today()}})
                        sqlFnS2.sqlQuery()

                        if len(dataS) != 0:
                            sqlFnS3 = runSQLFn("update", "trade_order_record", {"where": {"trade_order_id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"},
                                                                                          "status": {"condition": "=", "value": "order", "type": "AND"}},
                                                                                "set": {"status": "cancel", "updated_at": datetime.today()}})
                            sqlFnS3.sqlQuery()

                            if dataS[0]["enter_price"] == dataS1[0]["price"]:
                                sqlFnS4 = runSQLFn("update", "trade_order", {"where": {"id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"}},
                                                                             "set": {"status": "be", "updated_at": datetime.today()}})
                                sqlFnS4.sqlQuery()
                            else:
                                sqlFnS4 = runSQLFn("update", "trade_order", {"where": {"id": {"condition": "=", "value": content['trade_order_id'], "type": "AND"}},
                                                                             "set": {"status": "sl", "sl": mark_price_float_value, "percentage": -(((mark_price_float_value - enter_float_value) / enter_float_value) * 100), "updated_at": datetime.today()}})
                                sqlFnS4.sqlQuery()

                else:
                    print(f"Failed to get market data for {content}.")

            # 为了避免频繁请求，可以添加适当的延迟
            await asyncio.sleep(1)  # 1秒钟后继续下一次查找市场价

    # 在客户端的事件循环中调度异步函数
    loop = asyncio.get_event_loop()
    loop.create_task(check_market_price())

@bot.event
async def on_message(message):
    # Ignore messages from bots to prevent potential loops
    if message.author.bot:
        return

    # def get_market_data(symbol_name):
    #     url = f"{BASE_URL}{MARKET_DATA_ENDPOINT}?symbol={symbol_name}"
    #     response = requests.get(url)
    #     data = response.json()
    #     return data

    if __name__ == "__main__":
        # Split the message into lines
        lines = message.content.split('\n')
        # Get the number of lines in the message
        num_lines = len(lines)
        # Get the first line of content (if it exists)
        if num_lines >= 11:
            contents = []
            for line in lines:
                # Convert the message content to uppercase
                uppercased_content = line.upper()
                # Remove '/' and ' ' from the message content
                content = uppercased_content.replace('/', '').replace(' ', '')
                contents.append(content)

            checkEnterBool = False
            checkTPBool = False
            checkSLBool = False

            for content in contents:

                # Submit Enter Record
                if content == "ENTER":
                    checkEnterBool = True
                elif checkEnterBool == True and content == "":
                    checkEnterBool = False

                if checkEnterBool == True and content != "ENTER":
                    sqlFnU = runSQLFn("select", "trader", {"where": {"trader_discord_id": {
                                        "condition": "=", "value": message.author.id}}})
                    trades = sqlFnU.sqlQuery()
                    
                    message.author.id
                    sqlFn1 = runSQLFn("insert", "trade_order", {"insertValue": {
                                      "keys": ["trader_id", "coin", "type"], "columns": [trades[0]["id"], contents[0], contents[1]]}})
                    dataId = sqlFn1.sqlQuery()
                    sqlFn2 = runSQLFn("insert", "trade_order_record", {"insertValue": {"keys": ["trade_order_id", "coin", "trend_type", "order_type", "price", "status"],
                                                                                       "columns": [dataId, contents[0], contents[1], "enter", content, "order"]}})
                    sqlFn2.sqlQuery()

                # Submit TP Record
                if content == "TP":
                    checkTPBool = True
                elif checkTPBool == True and content == "":
                    checkTPBool = False

                if checkTPBool == True and content != "TP":
                    sqlFn = runSQLFn("insert", "trade_order_record", {"insertValue": {"keys": ["trade_order_id", "coin", "trend_type", "order_type", "price", "status"],
                                                                                      "columns": [dataId, contents[0], contents[1], "tp", content, "order"]}})
                    sqlFn.sqlQuery()

                # Submit SL Record
                if content == "SL":
                    checkSLBool = True
                elif checkSLBool == True and content == "":
                    checkSLBool = False

                if checkSLBool == True and content != "SL":
                    sqlFn = runSQLFn("insert", "trade_order_record", {"insertValue": {"keys": ["trade_order_id", "coin", "trend_type", "order_type", "price", "status"],
                                                                                      "columns": [dataId, contents[0], contents[1], "sl", content, "order"]}})
                    sqlFn.sqlQuery()

                # market_data = get_market_data(content)
                # if market_data['ret_code'] == 0 and market_data['ret_msg'] == 'OK':
                #     print(market_data)
                #     last_price = market_data['result'][0]['last_price']
                #     mark_price = market_data['result'][0]['mark_price']
                #     print(f"Last Price for {content}: {last_price}")
                #     print(f"Mark Price for {content}: {mark_price}")
                # else:
                #     print(f"Failed to get market data for {content}.")
        else:
            print("The message does not have enough lines.")
    # if message.content.lower() == 'hello':
    #     await message.channel.send(f'Hello, {message.author.mention}!')

    # await bot.process_commands(message)


@bot.command()
async def submit(ctx):
    embed = discord.Embed(
        title="成为交易者",
        description="快来成为交易者，大家一起加油进步，帮助更多需要的人",
        color=discord.Color.from_rgb(144, 238, 144)
    )
    button = Button(label="申请成为交易者",
                    style=discord.ButtonStyle.success)

    async def on_submit(interaction: discord.Interaction):
        sqlFn = runSQLFn("select", "trader", {"where": {"trader_discord_id": {
                     "condition": "=", "value": interaction.user.id}}})
        data = sqlFn.sqlQuery()
        if not data:
            sqlFn = runSQLFn("insert", "trader", {"insertValue": {"keys": ["trader_name", "trader_discord_id"], 
                            "columns": [interaction.user.name, interaction.user.id]}})
            sqlFn.sqlQuery()
            guild = bot.get_guild(interaction.guild_id)
            role_name = "交易者"  # 替换为你要添加的身份组名称
            role = discord.utils.get(guild.roles, name=role_name)
            await interaction.user.add_roles(role)
            embed = discord.Embed(
                title="成为交易者",
                description="你已经成为交易者了",
                color=discord.Color.from_rgb(213, 86, 145)
            )
            await interaction.response.edit_message(embed=embed, view=None)
        else:
            embed = discord.Embed(
                title="成为交易者",
                description="你已经提交过了 / 你已经成为交易者了",
                color=discord.Color.from_rgb(213, 86, 145)
            )
            await interaction.response.edit_message(embed=embed, view=None)

    button.callback = on_submit
    view = View()
    view.add_item(button)

    await ctx.send(embed=embed, view=view)

bot.run(token)
