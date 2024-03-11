import asyncio
from collections.abc import Mapping, Sequence
import json
from typing import ClassVar, Optional
from typing_extensions import Self

from viam.logging import getLogger
from viam.module.module import Reconfigurable
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.proto.app.robot import ComponentConfig
from viam.resource.types import Model, ModelFamily
from viam.services.generic import Generic
from viam.utils import struct_to_dict, ValueTypes

import speech_recognition as sr
from vosk import Model as VoskModel

LOGGER = getLogger(__name__)


class SttVosk(Generic, Reconfigurable):
    MODEL: ClassVar[Model] = Model(ModelFamily("viam-labs", "stt-vosk"), "stt-vosk")

    q: asyncio.Queue
    recognizer: sr.Recognizer

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.q = asyncio.Queue()

    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> Self:
        stt = cls(config.name)
        stt.reconfigure(config, dependencies)
        return stt

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        return []

    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        attrs = struct_to_dict(config.attributes)
        LOGGER.info(attrs)
        model_name = attrs.get("model_name", "vosk-model-small-en-us-0.15")
        model_lang = attrs.get("model_lang", "en-us")
        self.mic_name = attrs.get("mic_name", "default")
        self.recognizer = sr.Recognizer()
        self.recognizer.vosk_model = VoskModel(model_name=model_name, lang=model_lang)

        LOGGER.debug("Calibrating for ambient noise")
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source)

    async def close(self):
        LOGGER.info(f"{self.name} is closed.")

    async def do_command(
        self,
        command: Mapping[str, ValueTypes],
        *,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> Mapping[str, ValueTypes]:
        LOGGER.info(f"received {command=}.")
        for name, args in command.items():
            if name == "listen":
                result = await self.listen(*args)
                return {"listen": result}
            else:
                LOGGER.warning(f"Unknown command: {name}")
                return {}
        return {}

    async def listen(self) -> str:
        with sr.Microphone() as source:
            LOGGER.debug("Listening...")
            audio = self.recognizer.listen(source)

        try:
            result = json.loads(self.recognizer.recognize_vosk(audio))
            return result["text"]
        except Exception as error:
            LOGGER.error("There was an issue listening for speech recognition")
            LOGGER.error(error)
            return ""
