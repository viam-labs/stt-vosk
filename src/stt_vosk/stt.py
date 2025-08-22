from collections.abc import Mapping, Sequence
from io import BytesIO
import json
from typing import ClassVar, Literal
from typing_extensions import Self

from pydub import AudioSegment
from viam.logging import getLogger
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.easy_resource import EasyResource
from viam.proto.app.robot import ComponentConfig
from viam.resource.types import Model
from viam.utils import struct_to_dict

import speech_recognition as sr
from vosk import Model as VoskModel
from speech_service_api import SpeechService

LOGGER = getLogger(__name__)


class SttVosk(SpeechService, EasyResource):
    MODEL: ClassVar[Model] = Model.from_string("viam-labs:speech:stt-vosk")

    recognizer: sr.Recognizer

    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> Self:
        return super().new(config, dependencies)

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        return []

    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        attrs = struct_to_dict(config.attributes)
        LOGGER.debug(attrs)
        model_name = str(attrs.get("model_name", "vosk-model-small-en-us-0.15"))
        model_lang = str(attrs.get("model_lang", "en-us"))
        self.disable_mic = bool(attrs.get("disable_mic", False))
        self.mic_device_name = str(attrs.get("mic__device_name", "default"))
        self.recognizer = sr.Recognizer()
        self.recognizer.vosk_model = VoskModel(model_name=model_name, lang=model_lang)

        if not self.disable_mic:
            mics = sr.Microphone.list_microphone_names()
            
            if self.mic_device_name != "":
                self.mic = sr.Microphone(mics.index(self.mic_device_name))
            else:
                self.mic = sr.Microphone()
                
            LOGGER.debug("Calibrating for ambient noise")
            with self.mic as source:
                self.recognizer.adjust_for_ambient_noise(source)

    async def close(self):
        LOGGER.debug(f"{self.name} is closed.")

    def convert_audio(self, audio: sr.AudioData) -> str:
        try:
            result = json.loads(self.recognizer.recognize_vosk(audio))
            return result["text"]
        except Exception as error:
            LOGGER.error("There was an issue listening for speech recognition")
            LOGGER.error(error)
            return ""

    async def listen(self) -> str:
        if self.disable_mic:
            LOGGER.warning(
                "Microphone usage has been disabled. Change the configuration for `disable_mic` to enable listening."
            )
            return ""

        with self.mic as source:
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

    async def to_speech(self, text: str):
        raise NotImplementedError()

    async def say(self, text: str, blocking: bool):
        raise NotImplementedError()

    async def completion(self, text: str, blocking: bool) -> str:
        raise NotImplementedError()

    async def get_commands(self, number: int) -> Sequence[str]:
        raise NotImplementedError()

    async def is_speaking(self) -> bool:
        raise NotImplementedError()

    async def listen_trigger(self, type: str) -> Sequence[str]:
        raise NotImplementedError()
