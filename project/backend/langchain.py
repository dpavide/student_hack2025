import os
from dotenv import load_dotenv
load_dotenv()
import asyncio
from pyneuphonic import Neuphonic, Agent

async def main():
    # Initialize Neuphonic client using API key from .env
    client = Neuphonic(api_key=os.environ.get('NEUPHONIC_API_KEY'))

    # Create a new voice AI agent with a short, helpful prompt
    agent_data = client.agents.create(
        name='My Ai girlfriend',
        prompt=(
            "Keep the conversation light and fun. "
        ),
        greeting='Hey! Ready to workout with me?.'
    )

    agent_id = agent_data.data['agent_id']

    # Initialize the Agent with the created ID and desired TTS model
    agent = Agent(client, agent_id=agent_id, tts_model='neu_hq')

    try:
        print("🤖 Neuphonic Agent is live! Speak to begin.")
        await agent.start()

        # Keep the agent running in the background
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Stopping Agent.")
        await agent.stop()

asyncio.run(main())
