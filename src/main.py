import asyncio
import os
import sys
from dotenv import dotenv_values

from audioout import Audioout
from rgb import Rgb

from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions
from viam.components.board import Board
from viam.components.camera import Camera

from viam.logging import getLogger

LOGGER = getLogger(__name__)
SPOOKY_SOUND = os.path.abspath("./src/ghostly_whisper.mp3")


async def main():
    candy_bucket = CandyBucket()
    try:
        await candy_bucket.start()
    except Exception as error:
        LOGGER.error("Error starting up candy bucket", exc_info=error)
    finally:
        LOGGER.info("Stopped candy bucket program")


class CandyBucket:
    board: Board
    camera: Camera
    motion_sensor: Board.DigitalInterrupt
    speaker: Audioout
    lights: Rgb
    last_tick: int = 0
    q: asyncio.Queue

    def __init__(self):
        self.config = dotenv_values(os.path.abspath(".env"))

    async def start(self):
        robot_secret = self.config.get("ROBOT_SECRET")
        robot_location = self.config.get("ROBOT_LOCATION")
        board_name = self.config.get("BOARD")
        camera_name = self.config.get("CAMERA")
        motion_sensor_name = self.config.get("MOTION_SENSOR")
        speaker_name = self.config.get("SPEAKER")
        lights_name = self.config.get("LIGHTS")

        assert (
            isinstance(robot_location, str)
            and isinstance(robot_secret, str)
            and isinstance(board_name, str)
            and isinstance(camera_name, str)
            and isinstance(motion_sensor_name, str)
            and isinstance(speaker_name, str)
            and isinstance(lights_name, str)
        )
        robot = await self.connect()
        self.board = Board.from_robot(robot, board_name)
        self.camera = Camera.from_robot(robot, camera_name)
        self.motion_sensor = await self.board.digital_interrupt_by_name(
            motion_sensor_name
        )
        self.speaker = Audioout.from_robot(robot, name=speaker_name)
        self.lights = Rgb.from_robot(robot, lights_name)

        LOGGER.info("<-----STARTING CANDY BUCKET----->")
        try:
            await self.run()
        finally:
            await robot.close()

    async def connect(self):
        creds = Credentials(
            type="robot-location-secret", payload=self.config.get("ROBOT_SECRET")
        )
        opts = RobotClient.Options(
            refresh_interval=0, dial_options=DialOptions(credentials=creds)
        )
        return await RobotClient.at_address(self.config.get("ROBOT_LOCATION"), opts)

    async def run(self):
        LOGGER.info("Running candy_bucket program!")
        self.q = asyncio.Queue()
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


if __name__ == "__main__":
    asyncio.run(main())
