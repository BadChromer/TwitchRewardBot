import twitchio
import random
import string
import api_helper
import asyncio
from datetime import datetime
from twitchio.ext import pubsub

DATE_TEMPLATE = "%Y-%m-%d %H:%M:%S"
USER_OAUTH_TOKEN = asyncio.new_event_loop().run_until_complete(api_helper.refresh_access_token("BROADCASTER_REFRESH_TOKEN"))
USER_CHANNEL_NAME = ""
USER_CHANNEL_ID = ""
TIMEOUT_MSG = ""
REWARD_PROMPT = ""
REWARD_TITLE = ""
REWARD_COST = ""
REWARD_COOLDOWN = ""

client = twitchio.Client(token=USER_OAUTH_TOKEN, initial_channels=[USER_CHANNEL_NAME])
client.pubsub = pubsub.PubSubPool(client)
broadcaster = client.create_user(USER_CHANNEL_ID, USER_CHANNEL_NAME)

vips = {}
whitelist = {"USER_NAME": "USER_ID"} # Users whose VIP status cannot be stolen
mods = ["USER_MOD_NAME"] # List of mods
timeout_text = [] # List of timeout messages
timeout_emotes = [] # List of emotes

def get_username_from_input(user_input: str):
    symbols_to_remove = list(string.punctuation.replace("_", ""))
    for symbol in symbols_to_remove:
        if symbol in user_input:
            user_input = user_input.replace(symbol, "")
    for input in user_input.lower().split():
        for vip_name in vips:
            if input == vip_name:
                return input
        for member in whitelist:
            if input == member:
                return input
        for mod in mods:
            if input == mod:
                return input
        for value in ["random", "рандом"]:
            if input == value:
                return "random"
    return user_input

async def create_reward():
    await broadcaster.create_custom_reward(token=USER_OAUTH_TOKEN,
                                           title=REWARD_TITLE,
                                           cost=REWARD_COST,
                                           prompt=REWARD_PROMPT,
                                           enabled=True,
                                           input_required=True,
                                           max_per_stream=48,
                                           global_cooldown=REWARD_COOLDOWN)

async def edit_reward(token: str, cooldown=REWARD_COOLDOWN, is_paused=False):
    main_reward = (await broadcaster.get_custom_rewards(token, only_manageable=True))[0]
    await main_reward.edit(token=token,
                           title=REWARD_TITLE,
                           cost=REWARD_COST,
                           enabled=True,
                           paused=is_paused,
                           max_per_stream_enabled=True,
                           max_per_stream=48,
                           max_per_user_per_stream_enabled=False,
                           max_per_user_per_stream=0,
                           global_cooldown_enabled=True,
                           global_cooldown=cooldown)

async def fulfill_or_refund(token: str, msg: str, reward_redemption: twitchio.CustomRewardRedemption, reward_action: str):
    if reward_action == "refund":
        await reward_redemption.refund(token)
        await edit_reward(token, cooldown = 1)
    elif reward_action == "fulfill":
        await reward_redemption.fulfill(token)
        await edit_reward(token)
    await broadcaster.channel.send(msg)

async def timeout_or_steal(token: str, msg: str, reward_redemption: twitchio.CustomRewardRedemption, user_id: int, event_action: str, time=None, remove_vip_id=None):
    if event_action == "steal":
        await broadcaster.add_channel_vip(token, user_id)
        await broadcaster.remove_channel_vip(token, remove_vip_id)
    elif event_action == "timeout":
        await broadcaster.timeout_user(token, USER_CHANNEL_ID, user_id, time, TIMEOUT_MSG)
    await broadcaster.channel.send(msg)
    await reward_redemption.fulfill(token)
    await edit_reward(token)

async def steal_vip_event(token: str, random_number: int, user_id: int, user_name: str, vip_id: int, vip_name: str, reward_redemption: twitchio.CustomRewardRedemption):
    if 2 <= random_number <= 13:
        msg = f"@{user_name} украл випку у @{vip_name} peepoBANDOS"
        await timeout_or_steal(token, msg, reward_redemption, user_id, "steal", remove_vip_id=vip_id)
    elif 14 <= random_number <= 70:
        msg=f"@{user_name} попытался украсть випку у @{vip_name}, но {random.choice(timeout_text)} 1 час {random.choice(timeout_emotes)}"
        await timeout_or_steal(token, msg, reward_redemption, user_id, "timeout", time=3600)
    elif 71 <= random_number <= 100:
        msg = f"@{user_name} попытался украсть випку у @{vip_name}, но {random.choice(timeout_text)} 2 часа {random.choice(timeout_emotes)}"
        await timeout_or_steal(token, msg, reward_redemption, user_id, "timeout", time=7200)
    elif random_number == 1:
        msg = f"POLICE @{user_name} вытянул счастливый билет и {random.choice(timeout_text)} 24 часа POLICE"
        await timeout_or_steal(token, msg, reward_redemption, user_id, "timeout", time=86400)

@client.event()
async def event_token_expired():
    token = await api_helper.refresh_access_token("BROADCASTER_REFRESH_TOKEN")
    return token

@client.event()
async def event_ready():
    print(datetime.now().strftime(DATE_TEMPLATE) + f" | Logged in as {client.nick}\n" + \
          datetime.now().strftime(DATE_TEMPLATE) + f" | User id is {client.user_id}\n")

@client.event()
async def event_pubsub_channel_points(event: pubsub.PubSubChannelPointsMessage):
    vips.clear()
    token = await api_helper.refresh_access_token("BROADCASTER_REFRESH_TOKEN")
    redeemed_user_name = event.user.name.lower()
    redeemed_user_id = event.user.id
    redeemed_reward_title = event.reward.title
    if redeemed_reward_title == REWARD_TITLE:
        for vip in await broadcaster.fetch_channel_vips(token=token, first=100):
            if vip.name.lower() not in whitelist:
                vips[vip.name.lower()] = vip.id
        reward_redemption = (await event.reward.get_redemptions(token=token, status="UNFULFILLED", first=50))[0]
        random_vip = random.choice(list(vips.items()))
        random_vip_name = random_vip[0]
        random_vip_id = random_vip[1]
        random_number = random.randint(1, 100)
        vip_name = get_username_from_input(reward_redemption.input)
        if vip_name in vips:
            vip_id = vips[vip_name]

        print(datetime.now().strftime(DATE_TEMPLATE) + f" | REDEEMED BY: {redeemed_user_name} | {redeemed_user_id}\n" + \
              datetime.now().strftime(DATE_TEMPLATE) + f" | USER INPUT: {vip_name}\n" + \
              datetime.now().strftime(DATE_TEMPLATE) + f" | RANDOM VIP: {random_vip_name} | {random_vip_id}\n" + \
              datetime.now().strftime(DATE_TEMPLATE) + f" | RANDOM NUMBER: {random_number}\n")

        if (redeemed_user_name in vips) or (redeemed_user_name in whitelist):
            msg = f"@{redeemed_user_name}, у тебя уже есть випка! Поинты возвращены, перезарядка награды сброшена!"
            await fulfill_or_refund(token, msg, reward_redemption, "refund")
        elif redeemed_user_name in mods:
            msg = f"@{redeemed_user_name}, модераторам нельзя випку :( Поинты возвращены, перезарядка награды сброшена!"
            await fulfill_or_refund(token, msg, reward_redemption, "refund")
        else:
            if vip_name == "random":
                await steal_vip_event(token, random_number, redeemed_user_id, redeemed_user_name, random_vip_id, random_vip_name, reward_redemption)
            elif vip_name in vips:
                await steal_vip_event(token, random_number, redeemed_user_id, redeemed_user_name, vip_id, vip_name, reward_redemption)
            elif vip_name in whitelist:
                msg=f"@{redeemed_user_name}, вип @{vip_name} под защитой всевышних сил и у него нельзя украсть випку! Поинты возвращены, перезарядка награды сброшена!"
                await fulfill_or_refund(token, msg, reward_redemption, "refund")
            elif vip_name in mods:
                msg = f"@{redeemed_user_name}, нельзя красть у модераторов! Поинты возвращены, перезарядка награды сброшена!"
                await fulfill_or_refund(token, msg, reward_redemption, "refund")
            else:
                msg=f"@{redeemed_user_name}, такого пользователя среди випов нет! Увы, твои поинты сгорели Jkrg"
                await fulfill_or_refund(token, msg, reward_redemption, "fulfill")

async def main():
    topics = [pubsub.channel_points(USER_OAUTH_TOKEN)[USER_CHANNEL_ID]]
    await client.pubsub.subscribe_topics(topics)
    await edit_reward(USER_OAUTH_TOKEN, 1)
    main_reward = (await broadcaster.get_custom_rewards(token=USER_OAUTH_TOKEN, only_manageable=True))[0]
    redemptions = await main_reward.get_redemptions(token=USER_OAUTH_TOKEN, status="UNFULFILLED", first=50)
    for redemption in redemptions:
        await redemption.refund(token=USER_OAUTH_TOKEN)
    await client.start()

client.loop.run_until_complete(main())