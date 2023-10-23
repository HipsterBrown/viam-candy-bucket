"""
This file registers the model with the Python SDK.
"""

from viam.resource.registry import Registry, ResourceCreatorRegistration
from .api import Code
from .candy_bucket import candy_bucket

from .candy_bucket import candy_bucket

Registry.register_resource_creator(
    Code.SUBTYPE,
    candy_bucket.MODEL,
    ResourceCreatorRegistration(candy_bucket.new, candy_bucket.validate),
)
