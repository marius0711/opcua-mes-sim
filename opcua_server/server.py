import asyncio
import math
import random
import time

from asyncua import Server

ENDPOINT = "opc.tcp://0.0.0.0:4840/freeopcua/server/"
NAMESPACE_URI = "http://opcua-mes-sim/robotarm"

SAMPLE_INTERVAL_S = 0.005  # 200 Hz -> Nyquist 100 Hz, covers vibrations up to 100 Hz
CYCLE_LENGTH_S = 5.0


async def main():
    server = Server()
    await server.init()
    server.set_endpoint(ENDPOINT)
    idx = await server.register_namespace(NAMESPACE_URI)

    objects = server.get_objects_node()
    arm = await objects.add_object(idx, "RobotArm")

    axis1 = await arm.add_object(idx, "Axis1")
    position = await axis1.add_variable(idx, "Position", 0.0)
    vibration = await axis1.add_variable(idx, "Vibration", 0.0)
    torque = await axis1.add_variable(idx, "Torque", 0.0)
    cycle_count = await axis1.add_variable(idx, "CycleCount", 0)

    config = await arm.add_object(idx, "Config")
    target_freq = await config.add_variable(idx, "TargetFrequencyHz", 25.0)
    await target_freq.set_writable()

    print(f"Server running at {ENDPOINT}, namespace index {idx}")

    async with server:
        t0 = time.time()
        last_cycle = -1
        while True:
            t = time.time() - t0
            freq = await target_freq.get_value()

            vib_value = 0.5 * math.sin(2 * math.pi * freq * t) + random.gauss(0, 0.05)
            pos_value = 10 * math.sin(2 * math.pi * 0.2 * t) + random.gauss(0, 0.02)
            torque_value = 5 + random.gauss(0, 0.3)

            await vibration.write_value(vib_value)
            await position.write_value(pos_value)
            await torque.write_value(torque_value)

            current_cycle = int(t // CYCLE_LENGTH_S)
            if current_cycle != last_cycle:
                last_cycle = current_cycle
                await cycle_count.write_value(current_cycle)

            await asyncio.sleep(SAMPLE_INTERVAL_S)


if __name__ == "__main__":
    asyncio.run(main())
