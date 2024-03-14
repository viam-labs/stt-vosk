import asyncio
from collections.abc import Mapping, Sequence
from io import BytesIO
import json
from typing import ClassVar, Literal
from typing_extensions import Self

from pydub import AudioSegment
from viam.logging import getLogger
from viam.module.module import Reconfigurable
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.proto.app.robot import ComponentConfig
from viam.resource.types import Model, ModelFamily
from viam.utils import struct_to_dict

import speech_recognition as sr
from vosk import Model as VoskModel
from speech_service_api import SpeechService

LOGGER = getLogger(__name__)


class SttVosk(SpeechService, Reconfigurable):
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

    def convert_audio(self, audio: sr.AudioData) -> str:
        try:
            result = json.loads(self.recognizer.recognize_vosk(audio))
            return result["text"]
        except Exception as error:
            LOGGER.error("There was an issue listening for speech recognition")
            LOGGER.error(error)
            return ""

    async def listen(self) -> str:
        with sr.Microphone() as source:
            LOGGER.debug("Listening...")
            audio = self.recognizer.listen(source)

        return self.convert_audio(audio)

    async def to_text(
        self,
        speech: bytes,
        format: str | Literal["wav", "mp3", "ogg", "flv", "mp4", "wma", "aac"] = "wav",
    ):
        audio = BytesIO(speech)

        if format != "wav":
            segment = AudioSegment.from_file(audio, format=format)
            audio = BytesIO()
            segment.export(audio, format="wav")

        with sr.AudioFile(audio) as source:
            return self.convert_audio(self.recognizer.record(source))
