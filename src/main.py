import asyncio

from viam.module.module import Module

from stt_vosk import SttVosk

if __name__ == "__main__":
    asyncio.run(Module.run_from_registry())
