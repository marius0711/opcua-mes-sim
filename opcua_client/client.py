import asyncio
import os
import time

from asyncua import Client

from opcua_client.transform import find_vibration_peak, position_repeatability, detect_outliers
from db.store import (
    DEFAULT_DB_PATH,
    get_connection,
    init_db,
    insert_run,
    insert_points,
    insert_evaluation,
)

ENDPOINT = os.environ.get("OPCUA_ENDPOINT", "opc.tcp://localhost:4840/freeopcua/server/")
NAMESPACE_URI = "http://opcua-mes-sim/robotarm"
ARM_ID = "arm1"
COLLECTION_DURATION_S = 3.0


async def collect_run(client, idx):
    root = await client.nodes.root.get_child(
        ["0:Objects", f"{idx}:RobotArm"]
    )
    axis1 = await root.get_child(f"{idx}:Axis1")
    config = await root.get_child(f"{idx}:Config")

    vibration_node = await axis1.get_child(f"{idx}:Vibration")
    position_node = await axis1.get_child(f"{idx}:Position")
    torque_node = await axis1.get_child(f"{idx}:Torque")
    target_freq_node = await config.get_child(f"{idx}:TargetFrequencyHz")

    target_frequency_hz = await target_freq_node.get_value()
    vibration, position, torque, timestamps = [], [], [], []
    t0 = time.time()
    while time.time() - t0 < COLLECTION_DURATION_S:
        vibration.append(await vibration_node.get_value())
        position.append(await position_node.get_value())
        torque.append(await torque_node.get_value())
        timestamps.append(time.time() - t0)

    # Network round-trips make polling slower and jitterier than any fixed sleep
    # interval, so the achieved sample rate must be measured, not assumed.
    actual_sample_rate_hz = (len(timestamps) - 1) / (timestamps[-1] - timestamps[0])

    return {
        "vibration": vibration,
        "position": position,
        "torque": torque,
        "timestamps": timestamps,
        "sample_rate_hz": actual_sample_rate_hz,
        "target_frequency_hz": target_frequency_hz,
    }


def compute_metrics(raw):
    vibration_result = find_vibration_peak(raw["vibration"], raw["sample_rate_hz"])
    position_result = position_repeatability(raw["position"])
    outlier_indices = detect_outliers(raw["torque"])
    return vibration_result, position_result, outlier_indices


def persist_run(db_conn, raw, vibration_result, position_result, outlier_indices):
    run_id = insert_run(
        db_conn,
        arm_id=ARM_ID,
        target_frequency_hz=raw["target_frequency_hz"],
        sample_rate_hz=raw["sample_rate_hz"],
    )
    insert_points(db_conn, run_id, "vibration", raw["vibration"], raw["timestamps"])
    insert_points(db_conn, run_id, "position", raw["position"], raw["timestamps"])
    insert_points(db_conn, run_id, "torque", raw["torque"], raw["timestamps"])
    insert_evaluation(db_conn, run_id, "peak_frequency_hz", vibration_result["peak_frequency_hz"])
    insert_evaluation(db_conn, run_id, "peak_magnitude", vibration_result["peak_magnitude"])
    insert_evaluation(db_conn, run_id, "position_std_dev", position_result["std_dev"])
    insert_evaluation(db_conn, run_id, "torque_outlier_count", len(outlier_indices))
    return run_id


async def main():
    async with Client(url=ENDPOINT) as client:
        idx = await client.get_namespace_index(NAMESPACE_URI)
        raw = await collect_run(client, idx)
        vibration_result, position_result, outlier_indices = compute_metrics(raw)

        print(f"Achieved sample rate: {raw['sample_rate_hz']:.1f} Hz")
        print(f"Vibration peak: {vibration_result['peak_frequency_hz']:.2f} Hz "
              f"(magnitude {vibration_result['peak_magnitude']:.2f})")
        print(f"Position: mean={position_result['mean']:.3f}, "
              f"std_dev={position_result['std_dev']:.3f}")
        print(f"Torque outliers: {len(outlier_indices)} of {len(raw['torque'])} samples")

        db_conn = get_connection()
        init_db(db_conn)
        run_id = persist_run(db_conn, raw, vibration_result, position_result, outlier_indices)
        db_conn.close()

        print(f"Stored as run_id={run_id} in {DEFAULT_DB_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
