import os
from dotenv import load_dotenv
load_dotenv()
import asyncio


class GeminiAgentWithMemory:
    def __init__(self, api_key, agent_name, prompt, greeting):
        self.api_key = api_key
        self.agent_name = agent_name
        self.prompt = prompt
        self.greeting = greeting
        self.chat_history = []  # Memory of conversation

    def create_agent(self):
        # Simulate agent creation (replace with real Gemini creation)
        print(f"Creating agent {self.agent_name} with prompt: {self.prompt}")
        return {"agent_id": "some_generated_id"}

    def update_memory(self, user_input, agent_response):
        """Simulate adding conversation to memory."""
        self.chat_history.append({"user": user_input, "agent": agent_response})
        if len(self.chat_history) > 10:  # Keep last 10 exchanges
            self.chat_history.pop(0)

    def get_full_conversation(self):
        """Return the conversation history as a string."""
        conversation = self.greeting + "\n"
        for entry in self.chat_history:
            conversation += f"User: {entry['user']}\nAgent: {entry['agent']}\n"
        return conversation

    async def start(self):
        """Start the conversation (mock interaction)."""
        print(f"🤖 {self.agent_name} is live! Let's chat.")
        await asyncio.sleep(1)  # Simulate waiting for input

        # Mock user input
        user_input = "What is your favorite workout?"
        print(f"User: {user_input}")

        # Simulate agent response based on memory (full conversation context)
        conversation = self.get_full_conversation()
        agent_response = f"Based on our chat, I love squats. Let's do some squats together!"
        print(f"Agent: {agent_response}")

        # Update memory with the new interaction
        self.update_memory(user_input, agent_response)

    async def stop(self):
        print(f"🛑 Stopping Agent {self.agent_name}.")

async def main():
    # Example API key and agent info
    api_key = os.environ.get('GEMINI_API_KEY')

    agent = GeminiAgentWithMemory(
        api_key=api_key,
        agent_name="My Ai girlfriend",
        prompt="Let's have some fun and workout together!",
        greeting="Hey! Ready to workout with me?"
    )

    agent_data = agent.create_agent()
    agent_id = agent_data.get("agent_id")

    try:
        await agent.start()

        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        await agent.stop()

asyncio.run(main())
