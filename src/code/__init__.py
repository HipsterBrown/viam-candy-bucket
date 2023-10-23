"""
This file registers the model with the Python SDK.
"""

from viam.components.board import ResourceRegistration
from viam.resource.registry import Registry, ResourceCreatorRegistration
from .api import CodeService, CodeClient, CodeRPCService
from .candy_bucket import candy_bucket

from viam.logging import getLogger

LOGGER = getLogger(__name__)

LOGGER.info("CANDY BUCKET: registering subtype and resource creators")

Registry.register_subtype(
    ResourceRegistration(
        CodeService, CodeRPCService, lambda name, channel: CodeClient(name, channel)
    )
)

Registry.register_resource_creator(
    CodeService.SUBTYPE,
    candy_bucket.MODEL,
    ResourceCreatorRegistration(candy_bucket.new, candy_bucket.validate),
)
