import asyncio
from os import path

from viam.robot.client import RobotClient
from viam.logging import getLogger

from speech_service_api import SpeechService

LOGGER = getLogger(__name__)
AUDIO_FILE = path.join(path.dirname(path.realpath(__file__)), "example.wav")


async def connect():
    opts = RobotClient.Options.with_api_key(
        api_key="<API-Key>", api_key_id="<API-Key-ID>"
    )
    return await RobotClient.at_address("<robot-address>", opts)


async def main():
    machine = await connect()

    LOGGER.info("Resources:")
    LOGGER.info(machine.resource_names)

    stt = SpeechService.from_robot(machine, name="stt")
    with open(AUDIO_FILE, "rb") as file:
        audio_data = file.read()

    LOGGER.info("Converting audio data to text")
    result = await stt.to_text(audio_data, format="wav")
    LOGGER.info(f"Text from the audio data:\n {result}")

    # Don't forget to close the machine when you're done!
    await machine.close()


if __name__ == "__main__":
    asyncio.run(main())
