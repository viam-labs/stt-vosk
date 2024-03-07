from collections.abc import Mapping, Sequence
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

LOGGER = getLogger(__name__)


class SttVosk(Generic, Reconfigurable):
    MODEL: ClassVar[Model] = Model(ModelFamily("viam-labs", "stt-vosk"), "stt-vosk")

    def __init__(self, name: str) -> None:
        super().__init__(name)

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

    async def close(self):
        LOGGER.info(f"{self.name} is closed.")

    async def do_command(
        self,
        command: Mapping[str, ValueTypes],
        *,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> Mapping[str, ValueTypes]:
        return await super().do_command(command, timeout=timeout, **kwargs)
