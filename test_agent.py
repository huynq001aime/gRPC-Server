import os
import asyncio
from typing import Type
from queue import Queue
from typing import Generator

from dotenv import load_dotenv
from langchain import hub
from langchain.agents import AgentExecutor, create_tool_calling_agent
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
# from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks.base import BaseCallbackHandler

load_dotenv()

# Pydantic models for tool arguments


class SimpleSearchInput(BaseModel):
    query: str = Field(description="should be a search query")


class MultiplyNumbersArgs(BaseModel):
    x: float = Field(description="First number to multiply")
    y: float = Field(description="Second number to multiply")


# Custom tool with only custom input


class SimpleSearchTool(BaseTool):
    name: str = "simple_search"
    description: str = "useful for when you need to answer questions about current events"
    args_schema: Type[BaseModel] = SimpleSearchInput # type: ignore

    def _run(
        self,
        query: str,
    ) -> str:
        """Use the tool."""
        from tavily import TavilyClient

        api_key = os.getenv("TAVILY_API_KEY")
        client = TavilyClient(api_key=api_key)
        results = client.search(query=query)
        return f"Search results for: {query}\n\n\n{results}\n"


# Custom tool with custom input and output
class MultiplyNumbersTool(BaseTool):
    name: str = "multiply_numbers"
    description: str = "useful for multiplying two numbers"
    args_schema: Type[BaseModel] = MultiplyNumbersArgs # type: ignore

    def _run(
        self,
        x: float,
        y: float,
    ) -> str:
        """Use the tool."""
        result = x * y
        return f"The product of {x} and {y} is {result}"


# Create tools using the Pydantic subclass approach
tools = [
    SimpleSearchTool(), # type: ignore
    MultiplyNumbersTool(), # type: ignore
]


class StreamingTokenCallbackHandler(BaseCallbackHandler):
    def __init__(self):
        self.queue = Queue()

    def on_llm_new_token(self, token: str, **kwargs):
        self.queue.put(token)

    def end(self):
        self.queue.put("[DONE]")

    def stream_tokens(self) -> Generator[str, None, None]:
        while True:
            token = self.queue.get()
            yield token


prompt = hub.pull("hwchase17/openai-tools-agent")

async def stream_agent_response_async(question: str):
    callback = StreamingTokenCallbackHandler()

    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0,
        streaming=True,
        # callbacks=[StreamingStdOutCallbackHandler()],
        callbacks=[callback],
    )

    agent = create_tool_calling_agent(
        llm=llm,
        tools=tools,
        prompt=prompt,
    )

    # Create the agent executor
    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        handle_parsing_errors=True,
    )

    def run_agent():
        try:
            agent_executor.invoke({"input": question})
        finally:
            callback.end()

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, run_agent)

    gen = callback.stream_tokens()
    while True:
        token = await asyncio.to_thread(next, gen)
        yield token
        if token == "[DONE]":
            break

