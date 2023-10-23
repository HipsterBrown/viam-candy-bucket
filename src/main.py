import asyncio
import sys

from viam.module.module import Module
from .code import Code, candy_bucket
from viam.logging import getLogger

LOGGER = getLogger(__name__)


async def main(address: str):
    """This function creates and starts a new module, after adding all desired resources.
    Resources must be pre-registered. For an example, see the `__init__.py` file.
    Args:
        address (str): The address to serve the module on
    """
    LOGGER.info("Starting candy bucket module")
    LOGGER.info(address)
    module = Module(address)
    module.add_model_from_registry(Code.SUBTYPE, candy_bucket.MODEL)
    await module.start()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise Exception("Need socket path as command line argument")

    asyncio.run(main(sys.argv[1]))
