from viam.resource.registry import Registry, ResourceCreatorRegistration
from viam.services.generic import Generic

from .stt import SttVosk

Registry.register_resource_creator(
    Generic.SUBTYPE,
    SttVosk.MODEL,
    ResourceCreatorRegistration(SttVosk.new, SttVosk.validate_config),
)
