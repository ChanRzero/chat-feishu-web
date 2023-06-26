from typing import Optional

import jwt
import datetime

from fastapi import Depends
from jwt import exceptions, PyJWTError
from loguru import logger
from pydantic import BaseModel
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


JWT_SALT = 'iv%x6xo7l7_u9bf_u!9#g#m*)*=ej@bek5)(@u3kh*72+unjv=Rzero'


class UserInfo(BaseModel):
    name:  Optional[str] = None
    avatar_url:  Optional[str] = None

def create_token(userInfo: UserInfo, timeout=7):
    """
    :param payload:  例如：{'user_id':1,'username':'wupeiqi'}用户信息
    :param timeout: token的过期时间，默认7天
    :return:
    """
    headers = {
        'typ': 'jwt',
        'alg': 'HS256'
    }
    payload = userInfo.dict()
    payload['exp'] = datetime.datetime.utcnow() + datetime.timedelta(days=timeout)
    result = jwt.encode(payload=payload, key=JWT_SALT, algorithm="HS256", headers=headers)
    return result


# 定义一个 HTTPBearer 实例，用于从请求头中获取 token
bearer_scheme = HTTPBearer()

# 定义一个依赖项函数，用于从请求头中获取 token 并进行验证
def parse_payload(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    result = {'status': False, 'data': None, 'message': None}
    if token == "token":
        result['message'] = 'token不能为空，请在【设置】中填写保存正确的token \n\n `在飞书机器人中,发送"token",获取正确的token`'
        logger.info("token为空！")
        return result
    try:
        verified_payload = jwt.decode(token, JWT_SALT, algorithms=["HS256"])
        result['status'] = True
        result['data'] = verified_payload
        logger.info("token正常！")
    except exceptions.ExpiredSignatureError:
        logger.info("token失效！")
        result['message'] = 'token已失效，请刷新token并在【设置】中重新保存token \n\n`在飞书机器人中,发送"token",获取新的token`'
    except jwt.DecodeError as e:
        logger.info("token失败！", e)
        result['message'] = 'token认证失败，请在【设置】中填写保存正确的token \n\n `在飞书机器人中,发送"token",获取正确的token`'
    except jwt.InvalidTokenError as e:
        logger.info("token非法！", e)
        result['message'] = '非法token，请在【设置】中填写正确保存的token \n\n `在飞书机器人中,发送"token",获取合法的token`'
    except exceptions as e:
        logger.info("token认证异常", e)
        result['message'] = 'token认证失败，请在【设置】中填写保存正确的token \n\n `在飞书机器人中,发送"token",获取正确的token`'
    except PyJWTError as e:
        logger.info("token认证失败", e)
        result['message'] = 'token认证失败，请在【设置】中填写保存正确的token \n\n `在飞书机器人中,发送"token",获取正确的token`'
    return result




if __name__ == '__main__':
    user = UserInfo(name='test', avatar_url='test')
    token = create_token(user)
    print(token)
    token='eyJhbGciOiJIUzI1NiIsInR5cCI6Imp3dCJ9.eyJuYW1lIjoidGVzdCIsImF2YXRhcl91cmwiOiJ0ZXN0IiwiZXhwIjoxNjg3NDA1NjcyfQ.MD9N_W4BpxWXQ5V4LWP59XXAUHJCav2ICeRk8_iSUqU'
    # token = 'token'
    # print(parse_payload(token))
