from audioout import Audioout
from rgb import Rgb

from typing import ClassVar, Mapping, Sequence, cast
from typing_extensions import Self
from viam.components.board import Board
from viam.components.camera import Camera

from viam.module.types import Reconfigurable
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.types import Model, ModelFamily
from viam.utils import struct_to_dict

from .api import CodeService
from viam.logging import getLogger

import os
import asyncio

LOGGER = getLogger(__name__)
SPOOKY_SOUND = os.path.abspath("./ghostly_whisper.mp3")


class candy_bucket(CodeService, Reconfigurable):
    MODEL: ClassVar[Model] = Model(ModelFamily("hipsterbrown", "code"), "candy_bucket")

    board: Board
    camera: Camera
    motion_sensor: Board.DigitalInterrupt
    speaker: Audioout
    lights: Rgb
    last_tick: int = 0
    started: asyncio.Task
    q: asyncio.Queue

    # Constructor
    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> Self:
        LOGGER.info("<-----CREATING NEW CANDY BUCKET----->")
        my_class = cls(config.name)
        my_class.reconfigure(config, dependencies)
        return my_class

    # Validates JSON Configuration
    @classmethod
    def validate(cls, config: ComponentConfig) -> Sequence[str]:
        # attrs = struct_to_dict(config.attributes)
        LOGGER.info("<-----VALIDATING CANDY BUCKET----->")
        LOGGER.info(config.attributes)
        # LOGGER.info(attrs)
        # board_name = attrs.get("board", "")
        # assert isinstance(board_name, str)
        # if board_name == "":
        #     raise Exception(
        #         "A board attribute must be defined with the name of the board component"
        #     )

        # camera_name = attrs.get("camera", "")
        # assert isinstance(camera_name, str)
        # if camera_name == "":
        #     raise Exception(
        #         "A camera attribute must be defined with the name of the camera component"
        #     )

        # motion_sensor_name = attrs.get("motion_sensor", "")
        # assert isinstance(motion_sensor_name, str)
        # if motion_sensor_name == "":
        #     raise Exception(
        #         "A motion_sensor attribute must be defined with the name of the motion_sensor component"
        #     )

        # speaker_name = attrs.get("speaker", "")
        # assert isinstance(speaker_name, str)
        # if speaker_name == "":
        #     raise Exception(
        #         "A speaker attribute must be defined with the name of the speaker component"
        #     )

        # lights_name = attrs.get("lights", "")
        # assert isinstance(lights_name, str)
        # if lights_name == "":
        #     raise Exception(
        #         "A lights attribute must be defined with the name of the lights component"
        #     )

        LOGGER.info("<-----VALIDATED CANDY BUCKET----->")
        # return [board_name, camera_name, motion_sensor_name, speaker_name, lights_name]
        return []

    # Handles attribute reconfiguration
    def reconfigure(
        self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ):
        LOGGER.info("<-----CONFIGURING CANDY BUCKET----->")
        LOGGER.info(config.attributes)
        LOGGER.info(dependencies)
        # attrs = struct_to_dict(config.attributes)
        # board_name = attrs.get("board")
        # camera_name = attrs.get("camera")
        # motion_sensor_name = attrs.get("motion_sensor")
        # speaker_name = attrs.get("speaker")
        # lights_name = attrs.get("lights")

        # assert (
        #     isinstance(board_name, str)
        #     and isinstance(camera_name, str)
        #     and isinstance(motion_sensor_name, str)
        #     and isinstance(speaker_name, str)
        #     and isinstance(lights_name, str)
        # )

        # board = dependencies[Board.get_resource_name(board_name)]
        # camera = dependencies[Camera.get_resource_name(camera_name)]
        # speaker = dependencies[Audioout.get_resource_name(speaker_name)]
        # lights = dependencies[Rgb.get_resource_name(lights_name)]

        # self.board = cast(Board, board)
        # self.camera = cast(Camera, camera)
        # self.motion_sensor_name = motion_sensor_name
        # self.speaker = cast(Audioout, speaker)
        # self.lights = cast(Rgb, lights)

        LOGGER.info("<-----CONFIGURED CANDY BUCKET----->")

        # if self.started:
        #     self.started.cancel()

        # self.started = asyncio.create_task(self.start())

        return self

    """ Implement the methods the Viam RDK defines for the Code API (hipsterbrown:services:code) """

    async def echo(self) -> str:
        return "Echo"

    async def start(self):
        LOGGER.info("Starting up candy_bucket program!")
        self.q = asyncio.Queue()
        self.motion_sensor = await self.board.digital_interrupt_by_name(
            name=self.motion_sensor_name
        )
        self.last_tick = await self.motion_sensor.value()

        LOGGER.info("Starting lights animation")
        animation = asyncio.create_task(self.lights.animate())
        await asyncio.sleep(5)
        LOGGER.info("Stopping lights animation")
        await self.lights.stop()
        await self.lights.clear()
        await animation
        LOGGER.info("Stopped lights animation")

        LOGGER.info("Playing spooky sound")
        await self.speaker.play(SPOOKY_SOUND)

        LOGGER.info("Starting working tasks")
        motion_task = asyncio.create_task(self.poll_motion())
        handle_task = asyncio.create_task(self.handle_interrupt())

        results = await asyncio.gather(motion_task, handle_task, return_exceptions=True)

        LOGGER.info(results)

    async def stop(self):
        LOGGER.info("<-----CLOSING CANDY BUCKET----->")
        if self.started:
            self.started.cancel()
            await self.started

    async def poll_motion(self) -> None:
        while True:
            next_tick = await self.motion_sensor.value()
            if next_tick != self.last_tick:
                self.last_tick = next_tick
                await self.q.put(self.last_tick)
                LOGGER.info("Motion detected!")
                await asyncio.sleep(3)
            else:
                await asyncio.sleep(0.1)

    async def handle_interrupt(self) -> None:
        while True:
            LOGGER.info("Waiting for motion event")
            _pin_value = await self.q.get()
            LOGGER.info("Handling motion event")
            image = await self.camera.get_image()
            LOGGER.info(f"camera get_image value: {image}")
            LOGGER.info("Animating!")
            animation = asyncio.create_task(self.lights.animate())
            sound = asyncio.create_task(self.speaker.play(SPOOKY_SOUND, 0, 0, 50))
            await asyncio.sleep(5)
            await self.lights.stop()
            await self.lights.clear()
            LOGGER.info("LEDs stopped")
            await asyncio.gather(animation, sound)
