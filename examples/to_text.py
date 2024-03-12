import asyncio
import base64
from os import path

from viam.robot.client import RobotClient
from viam.logging import getLogger
from viam.services.generic import Generic

LOGGER = getLogger(__name__)
AUDIO_FILE = path.join(path.dirname(path.realpath(__file__)), "example.wav")

async def connect():
    opts = RobotClient.Options.with_api_key(
      api_key='<API-Key>',
      api_key_id='<API-Key-ID>'
    )
    return await RobotClient.at_address('<robot-address>', opts)

async def main():
    machine = await connect()

    LOGGER.info('Resources:')
    LOGGER.info(machine.resource_names)

    stt = Generic.from_robot(machine, name="stt")
    with open(AUDIO_FILE, "rb") as file:
        audio_data = file.read()

    LOGGER.info("Converting audio data to text")
    result = await stt.do_command({ "to_text": [base64.b64encode(audio_data).decode()] })
    LOGGER.info(f"Text from the audio data:\n {result["to_text"]}")

    # Don't forget to close the machine when you're done!
    await machine.close()

if __name__ == '__main__':
    asyncio.run(main())
