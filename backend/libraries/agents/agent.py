from libraries.llm.groq.groq_llm import Groq
from langchain.agents import create_tool_calling_agent
from langchain import hub
from langchain.agents import AgentExecutor
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from libraries.prompts.system_prompt import sys_message

# Get the prompt to use - you can modify this!


class AdvancedGroq(Groq):

    prompt = hub.pull("hwchase17/openai-functions-agent")
    prompt.messages[0].prompt.template = sys_message
    store = {}

    def __init__(
        self,
        tools: list,
        **kwargs,
    ):
        # Call the parent constructor
        super().__init__(**kwargs)
        self.tools = tools

    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        else:
            if len(self.store[session_id].messages) > 4:
                print(self.store[session_id].messages)
                self.store[session_id].messages = self.store[session_id].messages[2:]
                print(len(self.store[session_id].messages))
        return self.store[session_id]

    def agent_create(self):
        agent = create_tool_calling_agent(self.client, self.tools, self.prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
        )
        agent_with_chat_history = RunnableWithMessageHistory(
            agent_executor,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )
        return agent_with_chat_history
