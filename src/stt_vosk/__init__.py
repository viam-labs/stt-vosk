from viam.resource.registry import Registry, ResourceCreatorRegistration

from speech_service_api import SpeechService
from .stt import SttVosk

Registry.register_resource_creator(
    SpeechService.API,
    SttVosk.MODEL,
    ResourceCreatorRegistration(SttVosk.new, SttVosk.validate_config),
)
