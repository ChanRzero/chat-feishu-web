import inspect
import os
import time

from fastapi import FastAPI, Request, APIRouter, Response, Depends
from fastapi.responses import StreamingResponse
from loguru import logger
from openai.error import APIConnectionError

from pydantic import BaseModel, Field
from typing import Optional, AsyncGenerator
from api.auth import parse_payload
from api.models import azureOpenAI
from api.models.azureOpenAI import stream_completions_turbo, StreamMessageTurbo, MessageTurbo, web_completions_turbo
import json

from sse_starlette.sse import ServerSentEvent, EventSourceResponse

router = APIRouter()

# model = os.environ.get('gpt_model')

stream_response_headers = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Keep-Alive": "timeout=4",
}


# if model is None:
#     config = json.load(open('.env.json'))
#     model = config['gpt_model']


# @router.post("/completions_turbo")
# async def completions(request: Request, message: MessageTurbo):
#     res = await azureOpenAI.completions_turbo(message, 3)
#     return res


# 前端请求的数据模型
class RequestProps(BaseModel):
    prompt: Optional[str] = None
    options: Optional[dict] = {}
    systemMessage: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None


class msgResponse(BaseModel):
    status: Optional[bool] = None
    data: Optional[dict] = None
    message: Optional[str] = None


# 后端返回的数据模型
class ChatMessage(BaseModel):
    id: str
    text: str
    role: Optional[str] = Field(default="assistant", description="Model name")
    name: Optional[str] = None
    delta: Optional[str] = None
    detail: Optional[dict] = None
    parentMessageId: Optional[str] = None
    conversationId: Optional[str] = None


# web后端普通消息接口
# @router.post('/chat-process')
async def chat_process(request: Request, request_props: RequestProps, token_data=Depends(parse_payload)):
    result = msgResponse()
    if not token_data['status']:
        result.status = False
        result.message = token_data['message']
        logger.warning('请求ip:' + request.client.host + '。token认证失败，拒绝访问模型接口')
        return result

    logger.info("请求普通消息接口，访问IP：" + request.client.host)

    prompt = request_props.prompt
    options = request_props.options
    system_message = request_props.systemMessage
    temperature = request_props.temperature
    top_p = request_props.top_p

    messages = []
    # 构造发送聊天消息的参数
    if system_message:
        messages.append({'role': 'system', 'content': system_message})

    # 构造上下文消息
    if options.get('contextMessage'):
        contextMessage = [{'content': item['content'][:300] if len(item['content']) > 300 else item['content'],
                           # 节省成本, 限制上下文消息长度  默认截取每个对话的前300个字符串
                           'role': item['role']} for item in options.get('contextMessage')]
        messages.extend(contextMessage)

    messages.append({'role': 'user', 'content': prompt})
    # 生成聊天消息

    try:
        logger.info("请求模型中")
        messages = MessageTurbo(temperature=temperature, top_p=top_p, messages=messages)
        res = await web_completions_turbo(messages)
        result.message = res["choices"][0]["message"]["content"]
        result.status = True
        logger.info("模型消息返回成功！")
    except Exception as e:
        result.status = False
        result.message = '出错了,请稍后重试！！！'
        logger.error(e)
    result.data = token_data
    # 发送聊天消息
    return result





# web后端-流式接口
@router.post('/chat-process')
async def chat_process_stream(request: Request, request_props: RequestProps, token_data=Depends(parse_payload)):
    result = msgResponse()
    if not token_data['status']:
        result.status = True
        result.message = token_data['message']
        logger.warning('请求ip:' + request.client.host + '。token认证失败，拒绝访问模型接口')
        return result
    logger.info("请求流式接口，访问IP：" + request.client.host)
    # 获取响应流
    # 解析前端请求的数据
    prompt = request_props.prompt
    options = request_props.options
    system_message = request_props.systemMessage
    temperature = request_props.temperature
    top_p = request_props.top_p

    messages = []
    # 构造发送聊天消息的参数
    if system_message:
        messages.append({'role': 'system', 'content': system_message})

    # 构造上下文消息
    if options.get('contextMessage'):
        contextMessage = [{'content': item['content'][:300] if len(item['content']) > 300 else item['content'],
                           # 节省成本, 限制上下文消息长度  默认截取每个对话的前300个字符串
                           'role': item['role']} for item in options.get('contextMessage')]
        messages.extend(contextMessage)

    messages.append({'role': 'user', 'content': prompt})
    # 生成聊天消息
    answer_text = chat_reply_process(messages, temperature, top_p)

    return EventSourceResponse(content=answer_text, headers=stream_response_headers, media_type="text/event-stream")


# 聊天处理函数
async def chat_reply_process(message, temperature, top_p):
    global res
    messages = StreamMessageTurbo(prompt=message, temperature=temperature, top_p=top_p)
    try:
        res = await stream_completions_turbo(messages)
        text = ""
        role = ""
        async for openai_object in res:
            openai_object_dict = openai_object.to_dict_recursive()

            if not role:
                role = openai_object_dict["choices"][0]["delta"].get("role", "")

            text_delta = openai_object_dict["choices"][0]["delta"].get("content", "")
            text += text_delta
            message = json.dumps(dict(
                role=role,
                id=openai_object_dict["id"],
                text=text,
                delta=text_delta,
                # detail=dict(
                #     id=openai_object_dict["id"],
                #     object=openai_object_dict["object"],
                #     created=openai_object_dict["created"],
                #     model=openai_object_dict["model"],
                #     choices=openai_object_dict["choices"]
                #  )
            ))
            time.sleep(0.015)  # 由于响应速度过快，导致前端直接读取的打字机效果不明显，所以延时了一下
            yield "data:" + message
    except APIConnectionError as e:
        logger.info(e)
        s = "出错了，请稍后重试！！！"
        for i in range(len(s)):
            r = msgResponse()
            r.message = s[:i + 1]
            r.status = False
            r.data = 'error'
            yield r

