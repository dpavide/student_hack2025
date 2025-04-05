import os
import asyncio
from dotenv import load_dotenv
from pyneuphonic import Neuphonic, Agent, AgentConfig

# LangChain imports
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI

load_dotenv()

# Set up LangChain memory and LLM
memory = ConversationBufferMemory()
conversation = ConversationChain(
    llm=ChatOpenAI(temperature=0),
    memory=memory,
    verbose=True
)

async def main():
    client = Neuphonic(api_key=(os.getenv("NEUPHONIC_API_KEY")))

    agent_id = client.agents.create(
        name='Squat assistant',
        prompt='You are a helpful gym training assistant. Answer clearly and conversationally. Keep track of the current session\'s chat history to maintain context.',
        greeting='Hi, Ready to workout with me?',
    ).data['agent_id']

    agent = Agent(client, agent_id=agent_id, tts_model='neu_hq')

    try:
        await agent.start()

        while True:
            user_input = input("You: ")

            if user_input.lower() in ["exit", "quit"]:
                break

            response = conversation.run(user_input)
            print("AI:", response)
            await agent.send(response)

            await asyncio.sleep(1)

    except KeyboardInterrupt:
        await agent.stop()

asyncio.run(main())
