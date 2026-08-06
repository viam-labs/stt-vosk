from collections.abc import Mapping, Sequence
from io import BytesIO
import json
import os
import sys
from contextlib import contextmanager
from typing import ClassVar, Literal
from typing_extensions import Self

from pydub import AudioSegment
from viam.logging import getLogger
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.components.sensor import Sensor
from viam.resource.easy_resource import EasyResource
from viam.proto.app.robot import ComponentConfig
from viam.resource.types import Model
from viam.utils import struct_to_dict

import speech_recognition as sr
from vosk import Model as VoskModel
from speech_service_api import SpeechService

LOGGER = getLogger(__name__)


@contextmanager
def suppress_alsa_errors():
    """Context manager to suppress ALSA error messages during audio device initialization."""
    # Save the current stderr
    original_stderr = sys.stderr
    try:
        # Redirect stderr to devnull to suppress ALSA errors
        sys.stderr = open(os.devnull, 'w')
        yield
    finally:
        # Restore stderr
        sys.stderr.close()
        sys.stderr = original_stderr


class SttVoskBase:
    """Base class with shared functionality for SttVosk and SttVoskSensor."""
    
    recognizer: sr.Recognizer
    disable_mic: bool
    mic_device_name: str
    mic_device_index: int | None
    suppress_alsa_errors: bool
    mic: sr.Microphone
    listen_timeout: float | None
    phrase_time_limit: float | None
    energy_threshold: int | None
    pause_threshold: float

    @staticmethod
    def _parse_float_or_none(value) -> float | None:
        """Parse a value as float or return None if not set."""
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_int_or_none(value) -> int | None:
        """Parse a value as int or return None if not set."""
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _reconfigure_base(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        """Internal reconfigure method shared by both derived classes."""
        attrs = struct_to_dict(config.attributes)
        LOGGER.debug(attrs)
        model_name = str(attrs.get("model_name", "vosk-model-small-en-us-0.15"))
        model_lang = str(attrs.get("model_lang", "en-us"))
        self.disable_mic = bool(attrs.get("disable_mic", False))
        self.mic_device_name = str(attrs.get("mic_device_name", ""))
        
        # Ensure mic_device_index is either None or an integer
        mic_index_raw = attrs.get("mic_device_index", None)
        if mic_index_raw is None or mic_index_raw == "":
            self.mic_device_index = None
        else:
            try:
                self.mic_device_index = int(mic_index_raw)
                LOGGER.debug(f"mic_device_index set to: {self.mic_device_index}")
            except (ValueError, TypeError):
                LOGGER.error(f"Invalid mic_device_index value: {mic_index_raw}. Using None.")
                self.mic_device_index = None
        
        self.suppress_alsa_errors = bool(attrs.get("suppress_alsa_errors", True))
        LOGGER.debug(f"suppress_alsa_errors: {self.suppress_alsa_errors}")
        
        # Parse timeout and threshold configuration
        self.listen_timeout = self._parse_float_or_none(attrs.get("listen_timeout", None))
        self.phrase_time_limit = self._parse_float_or_none(attrs.get("phrase_time_limit", None))
        self.energy_threshold = self._parse_int_or_none(attrs.get("energy_threshold", None))
        self.pause_threshold = float(attrs.get("pause_threshold", 0.8))
        
        LOGGER.debug(f"listen_timeout: {self.listen_timeout}")
        LOGGER.debug(f"phrase_time_limit: {self.phrase_time_limit}")
        LOGGER.debug(f"energy_threshold: {self.energy_threshold}")
        LOGGER.debug(f"pause_threshold: {self.pause_threshold}")
        
        self.recognizer = sr.Recognizer()
        self.recognizer.vosk_model = VoskModel(model_name=model_name, lang=model_lang)
        
        # Apply energy threshold if configured
        if self.energy_threshold is not None:
            self.recognizer.energy_threshold = self.energy_threshold
            LOGGER.info(f"Set energy threshold to {self.energy_threshold}")
        
        # Apply pause threshold
        self.recognizer.pause_threshold = self.pause_threshold
        LOGGER.debug(f"Set pause threshold to {self.pause_threshold}")

        if not self.disable_mic:
            try:
                # Suppress ALSA errors during device enumeration if configured
                if self.suppress_alsa_errors:
                    with suppress_alsa_errors():
                        mics = sr.Microphone.list_microphone_names()
                else:
                    mics = sr.Microphone.list_microphone_names()
                
                self.logger.info(f"Available microphones: {mics}")
                
                # Initialize microphone based on configuration
                if self.mic_device_index is not None:
                    # Use explicit device index if provided
                    LOGGER.info(f"Using microphone at index {self.mic_device_index}")
                    if self.suppress_alsa_errors:
                        with suppress_alsa_errors():
                            self.mic = sr.Microphone(device_index=self.mic_device_index)
                    else:
                        self.mic = sr.Microphone(device_index=self.mic_device_index)
                elif self.mic_device_name != "":
                    # Use device name if provided
                    LOGGER.info(f"Using microphone: {self.mic_device_name}")
                    try:
                        device_index = mics.index(self.mic_device_name)
                        if self.suppress_alsa_errors:
                            with suppress_alsa_errors():
                                self.mic = sr.Microphone(device_index=device_index)
                        else:
                            self.mic = sr.Microphone(device_index=device_index)
                    except ValueError:
                        LOGGER.error(f"Microphone '{self.mic_device_name}' not found. Using default.")
                        if self.suppress_alsa_errors:
                            with suppress_alsa_errors():
                                self.mic = sr.Microphone()
                        else:
                            self.mic = sr.Microphone()
                else:
                    # Use default microphone
                    LOGGER.info("Using default microphone")
                    if self.suppress_alsa_errors:
                        with suppress_alsa_errors():
                            self.mic = sr.Microphone()
                    else:
                        self.mic = sr.Microphone()
                    
                LOGGER.debug("Calibrating for ambient noise")
                with self.mic as source:
                    self.recognizer.adjust_for_ambient_noise(source)
                    
            except Exception as e:
                LOGGER.error(f"Failed to initialize microphone: {e}")
                self.disable_mic = True
                raise

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

    def _listen(self) -> str:
        """Private API for listening to microphone and converting to text."""
        if self.disable_mic:
            LOGGER.warning(
                "Microphone usage has been disabled. Change the configuration for `disable_mic` to enable listening."
            )
            return ""

        try:
            with self.mic as source:
                LOGGER.debug("Listening...")
                audio = self.recognizer.listen(
                    source,
                    timeout=self.listen_timeout,
                    phrase_time_limit=self.phrase_time_limit
                )
            return self.convert_audio(audio)
        except sr.WaitTimeoutError:
            LOGGER.debug("Listen timeout - no speech detected")
            return ""
        except Exception as e:
            LOGGER.error(f"Error during listening: {e}")
            return ""

    def _to_text(
        self,
        speech: bytes,
        format: str | Literal["wav", "mp3", "ogg", "flv", "mp4", "wma", "aac"] = "wav",
    ) -> str:
        """Private API for converting audio bytes to text."""
        audio = BytesIO(speech)

        if format != "wav":
            segment = AudioSegment.from_file(audio, format=format)
            audio = BytesIO()
            segment.export(audio, format="wav")

        with sr.AudioFile(audio) as source:
            return self.convert_audio(self.recognizer.record(source))


class SttVosk(SpeechService, EasyResource, SttVoskBase):
    MODEL: ClassVar[Model] = Model.from_string("viam-labs:speech:stt-vosk")

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        return []

    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        self._reconfigure_base(config, dependencies)

    async def listen(self) -> str:
        return self._listen()

    async def to_text(
        self,
        speech: bytes,
        format: str | Literal["wav", "mp3", "ogg", "flv", "mp4", "wma", "aac"] = "wav",
    ) -> str:
        return self._to_text(speech, format)

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

class SttVoskSensor(Sensor, EasyResource, SttVoskBase):
    MODEL: ClassVar[Model] = Model.from_string("viam-labs:speech:stt-vosk-sensor")

    @classmethod
    def validate_config(cls, config: ComponentConfig) -> Sequence[str]:
        return []

    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        self._reconfigure_base(config, dependencies)

    async def get_readings(self, **kwargs):
        return {"heard": self._listen()}