import asyncio

from viam.module.module import Module

from speech_service_api import SpeechService
from . import SttVosk


async def main():
    module = Module.from_args()
    module.add_model_from_registry(SpeechService.API, SttVosk.MODEL)
    await module.start()


asyncio.run(main())
