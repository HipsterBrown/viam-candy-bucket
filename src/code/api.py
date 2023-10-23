"""
This file outlines the general structure for the API around a custom, modularized services.

It defines the abstract class definition that all concrete implementations must follow,
the gRPC service that will handle calls to the service,
and the gRPC client that will be able to make calls to this service.

In this example, the ``Code`` abstract class defines what functionality is required for all Code servicess.
It extends ``ServiceBase``, as all services types must.
It also defines its specific ``SUBTYPE``, which is used internally to keep track of supported types.

The ``CodeRPCService`` implements the gRPC service for the Code services. This will allow other robots and clients to make
requests of the Code services. It extends both from ``CodeServiceBase`` and ``RPCServiceBase``.
The former is the gRPC service as defined by the proto, and the latter is the class that all gRPC services must inherit from.

Finally, the ``CodeClient`` is the gRPC client for a Code services. It inherits from CodeService since it implements
 all the same functions. The implementations are simply gRPC calls to some remote Code services.

To see how this custom modular services is registered, see the __init__.py file.
To see the custom implementation of this services, see the candy_bucket.py file.
"""

import abc
from typing import Final

from grpclib.client import Channel
from grpclib.server import Stream

from viam.resource.rpc_service_base import ResourceRPCServiceBase
from viam.resource.types import RESOURCE_TYPE_SERVICE, Subtype
from viam.services.service_base import ServiceBase

from ..proto.code_grpc import CodeServiceBase, CodeServiceStub

# update the below with actual methods for your API!
from ..proto.code_pb2 import EchoRequest, EchoResponse


class CodeService(ServiceBase):
    """service to use with the code module"""

    SUBTYPE: Final = Subtype("hipsterbrown", RESOURCE_TYPE_SERVICE, "code")

    @abc.abstractmethod
    async def echo(self, text: str) -> str:
        ...


class CodeRPCService(CodeServiceBase, ResourceRPCServiceBase):
    """gRPC service for the Code service"""

    RESOURCE_TYPE = CodeService

    # update with actual API methods
    async def Echo(self, stream: Stream[EchoRequest, EchoResponse]) -> None:
        request = await stream.recv_message()
        assert request is not None
        name = request.name
        service = self.get_resource(name)
        resp = await service.say(request.text)
        await stream.send_message(EchoResponse(text=resp))


class CodeClient(CodeService):
    """gRPC client for the Code Service"""

    def __init__(self, name: str, channel: Channel) -> None:
        self.channel = channel
        self.client = CodeServiceStub(channel)
        super().__init__(name)

    async def echo(self, text: str) -> str:
        request = EchoRequest(name=self.name, text=text)
        response: EchoResponse = await self.client.Echo(request)
        return response.text
