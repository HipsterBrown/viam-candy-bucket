"""
This file registers the model with the Python SDK.
"""

from viam.components.board import ResourceRegistration
from viam.resource.registry import Registry, ResourceCreatorRegistration
from .api import Code, CodeClient, CodeRPCService
from .candy_bucket import candy_bucket

Registry.register_subtype(
    ResourceRegistration(
        Code, CodeRPCService, lambda name, channel: CodeClient(name, channel)
    )
)

Registry.register_resource_creator(
    Code.SUBTYPE,
    candy_bucket.MODEL,
    ResourceCreatorRegistration(candy_bucket.new, candy_bucket.validate),
)
