import asyncio

from asyncua import Client

from opcua_client.client import ENDPOINT, NAMESPACE_URI, collect_run, compute_metrics, persist_run
from db.store import get_connection, init_db

TARGET_FREQUENCIES_HZ = [25.0, 25.0, 40.0]


async def main():
    db_conn = get_connection()
    init_db(db_conn)

    async with Client(url=ENDPOINT) as client:
        idx = await client.get_namespace_index(NAMESPACE_URI)
        config = await client.nodes.root.get_child(
            ["0:Objects", f"{idx}:RobotArm", f"{idx}:Config"]
        )
        target_freq_node = await config.get_child(f"{idx}:TargetFrequencyHz")

        for freq in TARGET_FREQUENCIES_HZ:
            await target_freq_node.write_value(freq)
            raw = await collect_run(client, idx)
            vibration_result, position_result, outlier_indices = compute_metrics(raw)
            run_id = persist_run(db_conn, raw, vibration_result, position_result, outlier_indices)
            print(f"Run {run_id}: target={freq} Hz -> "
                  f"peak={vibration_result['peak_frequency_hz']:.2f} Hz")

    db_conn.close()


if __name__ == "__main__":
    asyncio.run(main())
