import sys
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

async def main():
    print(">>> 初始化加法客户端")
    # 假设server.py就在本目录下
    server_script = "server.py"
    params = StdioServerParameters(
        command=sys.executable,  # 当前python解释器
        args=[server_script],
    )
    transport = stdio_client(params)
    stdio, write = await transport.__aenter__()
    session = await ClientSession(stdio, write).__aenter__()
    await session.initialize()
    print(">>> 连接到MCP服务器成功")

    while True:
        print("\n请输入两个数字（用空格分隔，或输入'退出'结束）：")
        user_input = input("> ")
        if user_input.strip().lower() == '退出':
            break
        try:
            a_str, b_str = user_input.strip().split()
            a, b = int(a_str), int(b_str)
        except Exception:
            print("输入格式有误，请输入两个整数，例如：3 5")
            continue
        print(f"正在计算: {a} + {b}")
        result = await session.call_tool("add", {"a": a, "b": b})
        # 直接访问 result.content[0].text
        answer = None
        if hasattr(result, "content") and result.content:
            first = result.content[0]
            if hasattr(first, "text"):
                answer = first.text
            elif isinstance(first, dict) and "text" in first:
                answer = first["text"]
            else:
                answer = str(first)
        else:
            answer = str(result)
        print(f"\nAI 回答：{a} 加 {b} 的结果是 {answer}")

    await session.__aexit__(None, None, None)
    await transport.__aexit__(None, None, None)
    print(">>> 客户端已关闭")

if __name__ == "__main__":
    asyncio.run(main()) 