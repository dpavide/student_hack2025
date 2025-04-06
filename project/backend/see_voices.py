import os
from pyneuphonic import Neuphonic

# Ensure the API key is set in your environment
client = Neuphonic(api_key=os.environ.get('NEUPHONIC_API_KEY'))

response = client.voices.list()  # get's all available voices
print(response.data['voices'])  # display list of voices