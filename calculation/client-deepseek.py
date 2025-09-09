import sys
import asyncio
import os
import json
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

async def main():
    print(">>> 初始化加法 LLM 工具客户端")
    server_script = "server.py"
    params = StdioServerParameters(
        command=sys.executable,
        args=[server_script],
    )
    transport = stdio_client(params)
    stdio, write = await transport.__aenter__()
    session = await ClientSession(stdio, write).__aenter__()
    await session.initialize()
    print(">>> 连接到MCP服务器成功")

    # 初始化 LLM
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )
    # 获取工具schema
    resp = await session.list_tools()
    tools = [{
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.inputSchema
        }
    } for tool in resp.tools]
    print("可用工具：", [t["function"]["name"] for t in tools])

    while True:
        print("\n请输入你的加法问题（如：5加7是多少？或'退出'）：")
        user_input = input("> ")
        if user_input.strip().lower() == '退出':
            break
        # 构造对话
        messages = [
            {"role": "system", "content": "你是一个加法助手，遇到加法问题请调用工具add，最后用自然语言回答用户。"},
            {"role": "user", "content": user_input}
        ]
        while True:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            message = response.choices[0].message
            messages.append(message)
            if not message.tool_calls:
                print("\nAI 回答：\n", message.content)
                break
            # 工具调用
            for tool_call in message.tool_calls:
                args = json.loads(tool_call.function.arguments)
                result = await session.call_tool(tool_call.function.name, args)
                messages.append({
                    "role": "tool",
                    "content": str(result),
                    "tool_call_id": tool_call.id
                })

    await session.__aexit__(None, None, None)
    await transport.__aexit__(None, None, None)
    print(">>> 客户端已关闭")

if __name__ == "__main__":
    asyncio.run(main()) 