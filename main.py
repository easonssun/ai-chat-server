from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import asyncio
from typing import AsyncGenerator
from langchain_core.callbacks import BaseCallbackHandler
from llm.model import chain_with_history, SESSION_ID

app = FastAPI(title="AI Chat Box API", description="基于DeepSeek的聊天API")

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源（前端域名）
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法（GET, POST 等）
    allow_headers=["*"],  # 允许所有请求头
)


# 定义请求模型
class ChatRequest(BaseModel):
    input: str


# 创建队列用于存储令牌
queue = asyncio.Queue()


async def generate_response(input_text: str) -> AsyncGenerator[str, None]:
    """
    生成流式响应
    """
    try:

        # 定义回调函数 必须继承 BaseCallbackHandler 类否则会报错
        class StreamCallback(BaseCallbackHandler):
            async def on_llm_new_token(self, token: str, **kwargs):
                await queue.put(json.dumps({"type": "token", "content": token}))

            async def on_llm_end(self, *args, **kwargs):
                await queue.put(json.dumps({"type": "done"}))
                await queue.put(None)  # 结束信号

            async def on_llm_error(self, error, **kwargs):
                await queue.put(json.dumps({"type": "error", "content": str(error)}))
                await queue.put(None)  # 结束信号

        # 创建回调实例
        callback = StreamCallback()

        # 在后台任务中运行模型
        async def run_model():
            try:
                await chain_with_history.ainvoke(
                    {"question": input_text},
                    config={
                        "callbacks": [callback],
                        "configurable": {"session_id": SESSION_ID},
                    },
                )
            except Exception as e:
                await queue.put(json.dumps({"type": "error", "content": str(e)}))
                await queue.put(None)

        # 启动模型运行任务
        task = asyncio.create_task(run_model())

        # 流式返回结果
        while True:
            item = await queue.get()
            if item is None:  # 结束信号
                break
            yield f"data: {item}\n\n"

        # 等待任务完成
        await task

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    聊天端点，支持流式传输
    """
    return StreamingResponse(
        generate_response(request.input),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
