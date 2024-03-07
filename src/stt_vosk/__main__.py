import asyncio

from viam.module.module import Module
from viam.services.generic import Generic

from . import SttVosk


async def main():
    module = Module.from_args()
    module.add_model_from_registry(Generic.SUBTYPE, SttVosk.MODEL)
    await module.start()


asyncio.run(main())
