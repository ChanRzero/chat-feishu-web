import asyncio
import json
import os

import uvicorn
from loguru import logger

from fastapi import FastAPI, Request, HTTPException

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


from api.app import router as api_app
from api.feishu import router as api_feishu

app = FastAPI()

app.include_router(api_app)
app.include_router(api_feishu)

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DIST_DIR = os.path.join(BASE_DIR, 'dist')
# ASSETS_DIR = os.path.join(DIST_DIR, 'assets')
# app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
# templates = Jinja2Templates(directory=DIST_DIR)


# async def catch_exceptions_middleware(request: Request, call_next):
#     try:
#         return await call_next(request)
#     except Exception as exc:
#         logger.error()
#         return JSONResponse(content={"code": 500, 'status': False, 'data': None, 'message': "出错了，请稍后重试！！！"})

# class UnauthorizedException(HTTPException):
#     def __init__(self, detail: str):
#         super().__init__(status_code=403, detail=detail)
#
# @api_app.exception_handler(UnauthorizedException)
# async def unauthorized_exception_handler(request, exc):
#     return JSONResponse(content={"code": 403, "message": exc.detail})
#

# app.middleware('http')(catch_exceptions_middleware)

# 解决跨站问题
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# @app.get("/", response_class=HTMLResponse)
# async def root():
#     return templates.TemplateResponse("index.html", {"request": {}})

@app.post("/session")
async def create_session(reqeuest: Request):
    try:
        logger.info("访问Web，访问IP："+reqeuest.client.host)
        return {'status': 'Success', 'message': '', 'data': {'auth': bool(0), 'model': 'ChatGPTAPI'}}
    except Exception as e:
        logger.error("访问Web,Api失败",e)
        return {'status': 'Fail', 'message': str(e), 'data': None}



if __name__ == "__main__":
    # uvicorn.run("main:app", host="127.0.0.1", port=8090)
    config = uvicorn.Config("main:app",host='127.0.0.1', port=3002, log_level="info")
    server = uvicorn.Server(config)
    server.run()
