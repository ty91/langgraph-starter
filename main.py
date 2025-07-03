import asyncio
import json
import os
import sys
from copy import deepcopy
from typing import List, Union

from dotenv import load_dotenv
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)

from agent.graph import AgentGraph
from db import clear_db, init_db, load_messages, save_message

load_dotenv()
init_db()


class ChatCLI:
    def __init__(self):
        self.agent = None
        self.messages = self._load_messages()

    def _get_api_key(self) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ ANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다.")
            print("다음 명령으로 API 키를 설정하세요:")
            print("export ANTHROPIC_API_KEY=your_api_key_here")
            sys.exit(1)
        return api_key

    def _print_welcome(self):
        print("🤖 AgentFlow CLI 챗봇에 오신 것을 환영합니다!")
        print("💬 메시지를 입력하여 에이전트와 대화하세요.")
        print("🚪 종료하려면 'exit', 'quit', 또는 'q'를 입력하세요.")
        print("🔄 대화 기록을 지우려면 'clear'를 입력하세요.")
        print("-" * 50)

    def _should_exit(self, user_input: str) -> bool:
        return user_input.lower().strip() in ["exit", "quit", "q"]

    def _should_clear(self, user_input: str) -> bool:
        return user_input.lower().strip() == "clear"

    async def _stream_response(self, user_message: str):
        user_message = HumanMessage(content=user_message)
        self.messages.append(user_message)
        self._save_message(user_message)

        print("\n🤖 AgentFlow:")

        tool_call_map = {}

        try:
            response_content = ""
            async for event_type, event in self.agent.astream(
                messages=self.messages,
                max_iterations=10,
                stream_mode=["messages", "updates"],
            ):
                if event_type == "messages":
                    message, _ = event
                    if isinstance(message, AIMessageChunk):
                        if hasattr(message, "tool_calls"):
                            for tool_call in message.tool_calls:
                                if "name" in tool_call and tool_call["name"] != "":
                                    print(f"\n\n⚙️  도구 사용 중: {tool_call['name']}")
                                    tool_call_map[tool_call["id"]] = deepcopy(tool_call)
                        if isinstance(message.content, str):
                            print(message.content, end="", flush=True)
                            response_content += message.content
                        else:
                            for block in message.content:
                                if block["type"] == "text":
                                    print(block["text"], end="", flush=True)
                                    response_content += block["text"]
                    elif isinstance(message, ToolMessage):
                        print(f"✅ 도구 결과: {message.content[:100]}...")
                elif event_type == "updates":
                    for value in event.values():
                        if "messages" in value:
                            self.messages.extend(value["messages"])
                            for message in value["messages"]:
                                self._save_message(message)
                else:
                    print(f"Unknown event type: {event_type}")
                    print("\n")

            print("\n")

        except Exception as e:
            print(f"\n❌ 에러가 발생했습니다: {e}")
            print("다시 시도해주세요.")

    def _save_message(self, message: Union[HumanMessage, AIMessage, ToolMessage]):
        if isinstance(message, HumanMessage):
            role = "user"
        elif isinstance(message, AIMessage):
            role = "assistant"
        elif isinstance(message, ToolMessage):
            role = "tool"

        metadata = message.model_dump()

        save_message(
            id=message.id,
            role=role,
            content=message.content,
            metadata=metadata,
        )

    def _load_messages(self) -> List[BaseMessage]:
        messages = []
        db_messages = load_messages()
        for message in db_messages:
            if message[1] == "user":
                messages.append(HumanMessage(**json.loads(message[3])))
            elif message[1] == "assistant":
                messages.append(AIMessage(**json.loads(message[3])))
            elif message[1] == "tool":
                messages.append(ToolMessage(**json.loads(message[3])))

        return messages

    async def run(self):
        api_key = self._get_api_key()
        self.agent = AgentGraph(provider="openai", model="gpt-4o-mini", api_key=api_key)

        self._print_welcome()

        while True:
            try:
                user_input = input("\n👤 You: ").strip()

                if not user_input:
                    continue

                if self._should_exit(user_input):
                    print("👋 안녕히 가세요!")
                    break

                if self._should_clear(user_input):
                    self.messages = []
                    clear_db()
                    print("🧹 대화 기록이 지워졌습니다.")
                    continue

                await self._stream_response(user_input)

            except KeyboardInterrupt:
                print("\n\n👋 안녕히 가세요!")
                break
            except EOFError:
                print("\n\n👋 안녕히 가세요!")
                break


async def main():
    cli = ChatCLI()
    await cli.run()


if __name__ == "__main__":
    asyncio.run(main())
