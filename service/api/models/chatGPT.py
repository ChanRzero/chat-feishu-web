import datetime
import os
from typing import Optional, List
from pydantic import BaseModel, Field


import httpx
import openai
import json

# 优先读取环境变量
API_KEY = os.environ.get('gpt_app_key')
# 如果环境变量为空，则读取 .env.json 文件
if API_KEY is None:
    config = json.load(open('./.env.json'))
    API_KEY = config['gpt_app_key']


class MessageTurbo(BaseModel):
    model: Optional[str] = Field(default="gpt-3.5-turbo", description="Model name")
    messages: Optional[List] = Field(default=None, description="Messages")
    max_tokens: Optional[int] = Field(default=2048, description="Stop sequence")
    temperature: Optional[float] = Field(default=0.5, description="Temperature")
    frequency_penalty: Optional[float] = Field(default=0.0, description="Frequency penalty")
    presence_penalty: Optional[float] = Field(default=0.0, description="Presence penalty")


async def get_response_turbo(message):
    url = "https://api.openai.com/v1/chat/completions"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=message.dict(),
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=60,
        )
        res = response.json()
        print('response:', res)
        data = json.dumps(res)
        json_data = json.loads(data)
        return json_data


async def completions_turbo(message, retry):  # GPT3.5 turbo  feishu
    try:
        json_data = await get_response_turbo(message)
    except Exception as e:
        print(e)
        return '出错了，请稍后重试！！！'
    print(json_data)
    for i in range(retry):  # 重试，如果出错，重新请求一遍
        if json_data.get('error'):
            json_data = await get_response_turbo(message)
            if i == retry - 1:
                return '出错了，请稍后重试！！！'
        else:
            break
    return json_data.get('choices')[0].get('message').get('content')


async def web_completions_turbo(message): # GPT3.5 turbo  web
    PROXIES = "http://127.0.0.1:7890"
    url = "https://api.openai.com/v1/chat/completions"
    async with httpx.AsyncClient(proxies=PROXIES) as client:
        response = await client.post(
            url,
            json=message.dict(),
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=60,
        )
        res = response.json()
        print('response:', res)
        error = res.get('error')
        if error:
            res['error']['message'] = '出错了，请稍后重试！！！'
        return res
