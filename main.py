import asyncio
import os

from dotenv import load_dotenv

from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions
from viam.components.board import Board
from viam.components.camera import Camera

from audioout import Audioout
from rgb import Rgb

load_dotenv()

ROBOT_SECRET = os.getenv("ROBOT_SECRET") or ""
ROBOT_LOCATION = os.getenv("ROBOT_LOCATION") or ""
BOARD_NAME = os.getenv("BOARD_NAME") or "pi"
CAMERA_NAME = os.getenv("CAMERA_NAME") or "camera"
MOTION_SENSOR_NAME = os.getenv("MOTION_SENSOR_NAME") or "motion"
SPEAKER_NAME = os.getenv("SPEAKER_NAME") or "speaker"
SPOOKY_SOUND = os.path.abspath("./ghostly_whisper.mp3")

last_tick = 0


async def connect():
    creds = Credentials(type="robot-location-secret", payload=ROBOT_SECRET)
    opts = RobotClient.Options(
        refresh_interval=0, dial_options=DialOptions(credentials=creds)
    )
    return await RobotClient.at_address(ROBOT_LOCATION, opts)


async def poll_motion(interrupt: Board.DigitalInterrupt, queue: asyncio.Queue) -> None:
    global last_tick

    while True:
        next_tick = await interrupt.value()
        if next_tick != last_tick:
            last_tick = next_tick
            await queue.put(last_tick)
            print("Motion detected!")
            await asyncio.sleep(3)
        else:
            await asyncio.sleep(0.1)


async def handle_interrupt(
    camera: Camera, leds: Rgb, speaker: Audioout, queue: asyncio.Queue
) -> None:
    while True:
        print("Waiting for motion event")
        pin_value = await queue.get()
        print("Handling motion event")
        image = await camera.get_image()
        print(f"camera get_image value: {image}")
        print("Animating!")
        animation = asyncio.create_task(leds.animate())
        sound = asyncio.create_task(speaker.play(SPOOKY_SOUND, 0, 0, 50))
        await asyncio.sleep(5)
        await leds.stop()
        await leds.clear()
        print("LEDs stopped")
        await asyncio.gather(animation, sound)


async def main():
    global last_tick
    q = asyncio.Queue()
    robot = await connect()

    print("Resources:")
    print(robot.resource_names)

    # pi
    pi = Board.from_robot(robot, BOARD_NAME)

    # motion interrupt
    motion_interrupt = await pi.digital_interrupt_by_name(name=MOTION_SENSOR_NAME)
    last_tick = await motion_interrupt.value()

    # arducam
    arducam = Camera.from_robot(robot, CAMERA_NAME)

    # lights
    lights = Rgb.from_robot(robot, "lights")
    print("Starting lights animation")
    animation = asyncio.create_task(lights.animate())
    await asyncio.sleep(5)
    print("Stopping lights animation")
    await lights.stop()
    await lights.clear()
    await animation
    print("Stopped lights animation")

    # speaker
    speaker = Audioout.from_robot(robot, name=SPEAKER_NAME)
    await speaker.play(SPOOKY_SOUND)

    motion_task = asyncio.create_task(poll_motion(motion_interrupt, q))
    handle_task = asyncio.create_task(handle_interrupt(arducam, lights, speaker, q))

    results = await asyncio.gather(motion_task, handle_task, return_exceptions=True)

    print(results)

    # Don't forget to close the robot when you're done!
    await robot.close()


if __name__ == "__main__":
    asyncio.run(main())
