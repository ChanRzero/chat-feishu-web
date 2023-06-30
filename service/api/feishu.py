import datetime

from Crypto.Cipher import AES
import hashlib
import json
import base64
import aiohttp
import os

from loguru import logger

from api.auth import create_token, UserInfo
from api.models import chatGPT, azureOpenAI
from api.models.azureOpenAI import MessageTurbo

from pydantic import BaseModel
from fastapi import FastAPI, Request, BackgroundTasks, APIRouter

router = APIRouter()

# 优先读取环境变量
app_id = os.environ.get('feishu_app_id')
app_secret = os.environ.get('feishu_app_secret')
verification_token = os.environ.get('feishu_verification_token')
encryption_key = os.environ.get('feishu_encryption_key')

# 如果环境变量为空，则从 .env.json 文件中读取
if app_id is None or app_secret is None or verification_token is None or encryption_key is None:
    with open('.env.json') as f:
        config = json.load(f)
        app_id = app_id or config.get('feishu_app_id')
        app_secret = app_secret or config.get('feishu_app_secret')
        verification_token = verification_token or config.get('feishu_verification_token')
        encryption_key = encryption_key or config.get('feishu_encryption_key')


class AESCipher(object):  # AES加密 ，对encryption_key进行解密
    def __init__(self, key):
        self.bs = AES.block_size
        self.key = hashlib.sha256(AESCipher.str_to_bytes(key)).digest()

    @staticmethod
    def str_to_bytes(data):
        u_type = type(b"".decode('utf8'))
        if isinstance(data, u_type):
            return data.encode('utf8')
        return data

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s) - 1:])]

    def decrypt(self, enc):
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:]))

    def decrypt_string(self, enc):
        enc = base64.b64decode(enc)
        return self.decrypt(enc).decode('utf8')


class TokenManager():  # 飞书token管理
    def __init__(self, app_id, app_secret) -> None:
        self.token = 'an_invalid_token'
        self.url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        self.req = {
            "app_id": app_id,
            "app_secret": app_secret
        }

    async def update(self):
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, headers={
                'Content-Type': 'application/json; charset=utf-8'
            }, data=json.dumps(self.req), timeout=5) as response:
                data = await response.json()
                if (data["code"] == 0):
                    self.token = data["tenant_access_token"]

    def get_token(self):
        return self.token


# TODO 获取飞书中的用户基本信息用户名,头像; 涉及隐私问题,暂时未使用
#      可以实现一些小功能，例如可以将用户名和头像信息放入token中，web端配置token时同步头像和用户名
class FeishuUserInfo():  # 获取飞书用户信息
    def __init__(self, user_id) -> None:
        self.token_manager = token_manager
        self.url = "https://open.feishu.cn/open-apis/contact/v3/users/"
        self.department_id_type = 'open_department_id'
        self.user_id_type = 'user_id'
        self.user_id = user_id
        self.avatar = ''
        self.name = ''

    async def get_user_info(self):
        headers = {
            'Authorization': 'Bearer ' + self.token_manager.get_token(),  # your access token
            'Content-Type': 'application/json'
        }
        params = {
            'department_id_type': self.department_id_type,
            'user_id_type': self.user_id_type,
            'user_id': self.user_id,
        }
        result = {'name': '', 'avatar': ''}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url, headers=headers, params=params) as response:
                    data = await response.json()

                    if (data["code"] == 0):
                        self.avatar = data["data"]['user']["avatar"]['avatar_72']
                        self.name = data["data"]['user']["name"]
                        result['name'] = self.name
                        result['avatar'] = self.avatar
        except:
            pass
        return result


class MsgSender():  # 飞书消息发送
    def __init__(self, token_manager: TokenManager) -> None:
        self.prefix = "https://open.feishu.cn/open-apis/im/v1/messages/"
        self.suffix = "/reply"
        self.token_manager = token_manager

    async def send(self, msg, msg_id):
        url = self.prefix + msg_id + self.suffix
        headers = {
            'Authorization': 'Bearer ' + self.token_manager.get_token(),  # your access token
            'Content-Type': 'application/json'
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=json.dumps({
                "msg_type": "text",
                "content": json.dumps({
                    "text": msg,
                })
            })) as response:
                data = await response.json()
        if (data["code"] == 99991668 or data["code"] == 99991663):  # token expired
            await self.token_manager.update()
            await self.send(msg, msg_id)
        elif (data["code"] == 0):
            return
        else:
            print("unreachable")
            # print(data)
            pass


# 获取会话历史消息
class HistoryMessages():
    def __init__(self, token_manager: TokenManager, page_size) -> None:
        self.prefix = "https://open.feishu.cn/open-apis/im/v1/messages"
        self.page_size = page_size
        self.container_id_type = "chat"
        self.token_manager = token_manager

    async def getHistoryMsg(self, start_time, end_time, chat_id):
        url = self.prefix
        headers = {
            'Authorization': 'Bearer ' + self.token_manager.get_token(),  # your access token
            'Content-Type': 'application/json'
        }
        params = {
            'container_id_type': self.container_id_type,
            'page_size': self.page_size,
            'start_time': start_time,
            'container_id': chat_id,
            'end_time': end_time
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                data = await response.json()
        if (data["code"] == 99991668 or data["code"] == 99991663):  # token expired
            await self.token_manager.update()
            await self.getHistoryMsg(start_time, end_time, chat_id)
        elif (data["code"] == 0):
            items = data['data']['items']
            result = []
            # 过滤出需要的响应消息
            for item in items:
                sender_type = item['sender']['sender_type']
                content = item['body']['content']
                result.append({'sender_type': sender_type, 'content': content})
            # 将消息体转换为模型需要的格式
            new_data = []
            for item in result:
                new_item = {}
                if item['sender_type'] == 'app':
                    new_item['role'] = 'assistant'
                else:
                    new_item['role'] = item['sender_type']
                if 'content' in item and 'text' in item['content']:
                    new_item['content'] = json.loads(item['content'])['text']
                    new_data.append(new_item)
            return new_data
        else:
            print("获取上下文失败")
            print(data)
            return


# 获取指定消息
class getTheMessage:
    def __init__(self, token_manager: TokenManager) -> None:
        self.prefix = "https://open.feishu.cn/open-apis/im/v1/messages/"
        self.token_manager = token_manager

    async def getMsg(self, msg_id):
        url = self.prefix + msg_id
        headers = {
            'Authorization': 'Bearer ' + self.token_manager.get_token(),  # your access token
            'Content-Type': 'application/json'
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
        if data["code"] == 99991668 or data["code"] == 99991663:  # token expired
            await self.token_manager.update()
            await self.getMsg(msg_id)
        elif (data["code"] == 0):
            content = data['data']['items'][0]['body']['content']
            return json.loads(content)['text']
        else:
            print("获取消息失败")
            print(data)
            return


cipher = AESCipher(encryption_key)
users_info = {}
token_manager = TokenManager(app_id=app_id, app_secret=app_secret)
sender = MsgSender(token_manager)


# TODO
async def completions_turbo(input: dict):
    """Get completions for the message."""
    content = None
    reply = ""
    logger.info("接受到飞书用户消息")
    if input['header']['token'] != verification_token:
        return

        # 检查输入中是否包含文本消息
    if 'event' in input and 'message' in input['event'] and 'content' in input['event']['message']:
        try:
            content = json.loads(input['event']['message']['content'])
            if 'text' not in content:
                reply = "抱歉，我只能接收文本消息哦"
                # 获取token
            else:
                if content['text'] == 'token':
                    # TODO 存放用户信息到token
                    userInfo = UserInfo(name='User', avatar_url='avatar_url')
                    # 创建token
                    token = create_token(userInfo)
                    reply = '您的token: 【' + token + '】，有效期为7天。\n请注意保管好您的token,切勿泄露他人。'
        except ValueError:
            reply = "消息格式错误"
    if reply != "":
        await sender.send(reply, input["event"]["message"]["message_id"])
        return

    # 判断是回复信息还是新消息
    if 'event' in input and 'message' in input['event'] and 'parent_id' in input['event']['message']:
        # 回复消息，将原消息作为上下文
        # 获取上下文消息
        parent_id = input['event']['message']['parent_id']
        get_msg = getTheMessage(token_manager)
        parent_msg = await get_msg.getMsg(parent_id)
        messages = [{'role': 'user', 'content': parent_msg}]
        new_message = content['text']
        messages.append({'role': 'user', 'content': new_message})
        logger.info("请求模型消息")
        try:
            message = MessageTurbo(messages=messages)
            reply = await azureOpenAI.completions_turbo(message, 3)
            logger.info("接受到模型消息")
        except Exception as e:
            reply = "出错了，请稍后重试！！！"
            logger.info("模型请求失败", e)
    # 新消息，将历史消息作为上下文
    else:
        # 获取10分钟前的时间戳
        timestamp = int(input["event"]["message"]["create_time"])  # 给定时间戳
        dt = datetime.datetime.fromtimestamp(timestamp / 1000)  # 将时间戳转换为 datetime 对象
        ago = dt - datetime.timedelta(minutes=10)  # 计算10分钟前的时间
        start_time = int(ago.timestamp())  # 将时间转换为时间戳
        now = dt - datetime.timedelta(seconds=1)  # 计算1秒前的时间
        end_time = int(now.timestamp())  # 将时间转换为时间戳

        # 获取会话id
        chatId = input['event']['message']['chat_id']
        # 获取一个小时之内的上下文消息，默认10条
        history_msg = HistoryMessages(token_manager, 10)
        his_messages = await history_msg.getHistoryMsg(start_time, end_time, chatId)
        # 给机器人知道当前时间
        now = datetime.datetime.now()
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")
        messages = [{'role': 'system', 'content': 'You are ChatGPT, a large language model trained by OpenAI.'}]
        newMessage = content['text']
        if his_messages is not None:
            his_messages = [{'role': item['role'], 'content': item['content'][:300]
            if len(item['content']) > 300
            else item['content']} for item in his_messages]  # 节省成本, 限制上下文消息长度  默认截取每个对话的前300个字符串
            messages.extend(his_messages)

        messages.append({'role': 'user', 'content': newMessage})
        logger.info("请求模型消息")
        try:
            message = MessageTurbo(messages=messages)
            reply = await azureOpenAI.completions_turbo(message, 3)
            logger.info("接受到模型消息")
        except Exception as e:
            reply = "出错了，请稍后重试！！！"
            logger.info("模型请求失败", e)
    await sender.send(reply, input["event"]["message"]["message_id"])


class LarkMsgType(BaseModel):
    encrypt: str


processed_message_ids = set()


@router.post("/feishu")  # 用于接收飞书消息
async def process(message: LarkMsgType, request: Request, background_tasks: BackgroundTasks):
    plaintext = json.loads(cipher.decrypt_string(message.encrypt))  # 对encrypt解密
    logger.info("飞书API请求对接", plaintext)
    # plaintext：
    #   "challenge": "ajls384kdjx98XX", // 应用需要在响应中原样返回的值
    #   "token": "xxxxxx", // 即VerificationToken
    #   "type": "url_verification" // 表示这是一个验证请求

    # 接收到客户端消息，如果有challenge就响应challenge
    if 'challenge' in plaintext:  # url verification
        return {'challenge': plaintext['challenge']}

    if 'event' in plaintext and 'message' in plaintext['event'] and 'message_id' in plaintext['event']['message']:
        message_id = plaintext['event']['message']['message_id']
        if message_id not in processed_message_ids:
            # 将message_id加入到已处理列表，避免下次重复处理,并且为了避免内存溢出问题，当set达到20，则删除掉
            if len(processed_message_ids) > 20:
                for _ in range(len(processed_message_ids) - 20):
                    processed_message_ids.pop()
            processed_message_ids.add(message_id)

            background_tasks.add_task(completions_turbo, plaintext)  # reply in background

    return {'message': 'ok'}  # 接受到消息后，立即返回ok，避免客户端重试
