from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy, ProviderStrategy
import os
from skills import SkillsMiddleware
import json
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import os
from tools import read_file, fetch_url, http_request


prompt_path = os.path.join(os.path.dirname(__file__), "default_agent_prompt.md")
with open(prompt_path, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

tools = [read_file]
agent_middleware = []


config = {"configurable": {"thread_id": "1", }}

checkpointer = InMemorySaver()

agent_middleware.append(SkillsMiddleware(
    skills_dir="./user-skills",
    project_skills_dir="./project-skills"
))

model = ChatOpenAI(
    model="DeepSeek-V3.2",
    base_url="https://www.dmxapi.com/v1",
    api_key='sk-7XXGRANcGq11GS8Dr78m8y9R45KB1V5ypzQGfFbedNeJ2cwG'
)

agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=tools,
    middleware=agent_middleware,
    checkpointer=checkpointer
)
#
user_input = input("👤 你: ").strip()
response = agent.invoke(
        {"messages": [{"role": "user", "content": user_input}]},
        config=config,
    )
ai = [m for m in response['messages'] if isinstance(m, AIMessage)][-1]
print("Agent:", ai.content)
# 1. 使用 .model_dump() 序列化所有消息
serialized_messages = [msg.model_dump() for msg in response['messages']]

# 2. 构建最终可 JSON 序列化的字典
output_data = {
    'messages': serialized_messages,
    'skills_metadata': response['skills_metadata']  # 这部分已经是普通 dict，无需处理
}

# 3. 写入 JSON 文件
output_file = Path("agent_response.json")
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"✅ 已保存到: {output_file.resolve()}")
# while True:
#     user_input = input("👤 你: ").strip()
#     if user_input.lower() in ("quit", "exit"):
#         break
#     response = agent.invoke(
#         {"messages": [{"role": "user", "content": user_input}]},
#         config=config,
#     )
#     print(response['messages'].model_dump())
#     # 1. 使用 .model_dump() 序列化所有消息
#     serialized_messages = [msg.model_dump() for msg in response['messages']]
#
#     # 2. 构建最终可 JSON 序列化的字典
#     output_data = {
#         'messages': serialized_messages,
#         'skills_metadata': response['skills_metadata']  # 这部分已经是普通 dict，无需处理
#     }