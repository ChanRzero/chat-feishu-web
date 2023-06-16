![cover](./docs/c1.png)
![cover2](./docs/c2.png)

![cover3](./docs/c3.png)

![cover4](./docs/c4.png)

![cover4](./docs/c5.png)

![cover4](./docs/c6.png)

## 介绍

该项目基于Azure OpenAI 进行实现

| 功能                                        | 特点 | 可拓展性  |
| --------------------------------------------- | ------ | ---------- |
| `Web端聊天页面`                  | 支持Markdown格式；响应消息呈现打字机效果；可以给模型赋予角色 | 较低     |
| `飞书机器人` | 仅支持文本格式；响应消息集中返回，速度较快； | 较高，可以结合飞书的功能进行许多新的功能拓展。 |

本项目Web前端页面是基于 [chatgpt-web](https://github.com/Chanzhaoyu/chatgpt-web) 的二次开发

#### 环境变量：

全部参数变量请查看或[这里](#环境变量)

```
/service/.env.example.json
```

## 待实现路线

[✓] web端打字机聊天效果

[✓] 多会话储存和上下文逻辑

[✓] 飞书指定消息作为上下文

[✓] 对代码等消息类型的格式化美化处理

[✓] 访问权限控制

[✓] 数据导入、导出

[✓] 保存消息到本地图片

[✓] 界面多语言

[✓] 界面主题

[✗] More...



## 飞书机器人搭建

[飞书开放平台](https://open.feishu.cn/app)

- 在飞书开放平台创建应用，打开`机器人`能力

![cover3](./docs/add_bot.png)

- 订阅`接收消息` 事件，并按需开通权限

![cover3](./docs/sub.png)

- 复制`.env.json.example`为`.env.json`，并填写`app_id` `app_secret` `encryption_key` `verification_token`，这几个字段在你的应用详情页可以找到

![cover3](./docs/appid_secret.png)

![cover3](./docs/encrypt_key_verification_token.png)



- 配置`请求地址`,格式为`http://your_domain:port/feishu`

![cover3](./docs/configure_url.png)





#### 机器人权限开放

应用详情 -> 开发配置 -> 权限管理

```
contact:contact:readonly_as_app

im:chat
im:chat.group_info:readonly
im:chat:readonly

im:message
im:message.group_at_msg
im:message.p2p_msg
im:message.p2p_msg:readonly
im:message:send_as_bot
```



## 前置要求

### Node

`node` 需要 `^16 || ^18 || ^19` 版本（`node >= 14` 需要安装 [fetch polyfill](https://github.com/developit/unfetch#usage-as-a-polyfill)），使用 [nvm](https://github.com/nvm-sh/nvm) 可管理本地多个 `node` 版本

```shell
node -v
```

### PNPM
如果你没有安装过 `pnpm`
```shell
npm install pnpm -g
```

### Python

Python需要3.8以上版本

```shell
python -V
```



## 安装依赖

### 后端

进入文件夹 `/service` 运行以下命令 Linux 系统用`Python3`和`pip3`

```shell
pip install -r requirements.txt
```

### 前端
根目录下运行以下命令
```shell
pnpm bootstrap
```

## 测试环境运行
### 后端服务

进入文件夹 `/service` 运行以下命令

```shell
python main.py
```

### 前端网页
根目录下运行以下命令
```shell
pnpm dev
```

## 环境变量

飞书相关变量：

- `feishu_app_id` 飞书机器人id
- `feishu_app_secret`  飞书机器人密钥
- `feishu_encryption_key` 飞书机器人加密key
- `feishu_verification_token` 飞书机器人身份校验码

Azure openAI相关变量：

- `gpt_app_key`  app_key
- `azure_api_base` api_base
- `azure_api_type` api_type
- `azure_api_version` api_version 

通用：

- `gpt_model` ：默认：openai-gpt，准备拓展多模型准备的变量



## 打包

#### 前端网页

1、修改根目录下 `.env` 文件中的 `VITE_GLOB_API_URL` 为你的实际后端接口地址

2、根目录下运行以下命令，然后将 `dist` 文件夹内的文件复制到你网站服务的根目录下

[参考信息](https://cn.vitejs.dev/guide/static-deploy.html#building-the-app)

```shell
pnpm build
```

#### 后端服务

1、后端目前无需打包，在系统中挂起运行即可，进入`/service`，其中log.log为运行日志文件

```shell
 nohup python3 main.py >> log.log 2>&1 &
```
