"""Robot simulator.

Random-walks around Sousse, follows the route of a running mission, and can
raise the occasional obstacle or intrusion alert.

    python -m scripts.simulator --key <KEY> [--key <KEY2>] --interval 2 --events
"""

import argparse
import random
import time

import httpx

SOUSSE = (35.8256, 10.6369)


class SimulatedRobot:
    def __init__(self, key: str, index: int) -> None:
        self.key = key
        self.index = index
        self.lat = SOUSSE[0] + random.uniform(-0.001, 0.001)
        self.lng = SOUSSE[1] + random.uniform(-0.001, 0.001)
        self.battery = random.uniform(55, 98)
        self.waypoints: list[dict] = []
        self.waypoint_index = 0
        self.mission_id: int | None = None

    @property
    def headers(self) -> dict[str, str]:
        return {"X-Robot-Key": self.key}

    def refresh_mission(self, client: httpx.Client, api_url: str) -> None:
        try:
            response = client.get(f"{api_url}/api/v1/robot/mission", headers=self.headers)
            if response.status_code != 200:
                return
            mission = response.json().get("mission")
        except httpx.HTTPError:
            return

        if mission is None:
            if self.mission_id is not None:
                self.mission_id = None
                self.waypoints = []
                self.waypoint_index = 0
            return

        if mission["id"] != self.mission_id:
            self.mission_id = mission["id"]
            self.waypoints = sorted(
                mission["route"]["waypoints"], key=lambda point: point["seq"]
            )
            self.waypoint_index = 0

    def step(self) -> str:
        """Advance one tick and return the telemetry status to report."""
        if self.waypoints:
            target = self.waypoints[self.waypoint_index]
            step = 0.00035
            dlat = target["lat"] - self.lat
            dlng = target["lng"] - self.lng
            distance = max(abs(dlat), abs(dlng))
            if distance < 0.0004:
                self.waypoint_index = (self.waypoint_index + 1) % len(self.waypoints)
            else:
                self.lat += max(-step, min(step, dlat))
                self.lng += max(-step, min(step, dlng))
            return "active"

        if random.random() < 0.55:
            self.lat += random.uniform(-0.00025, 0.00025)
            self.lng += random.uniform(-0.00025, 0.00025)
            status = "active"
        else:
            status = "idle"
        return status

    def drain(self) -> None:
        self.battery = max(0.0, self.battery - 0.02)


def send_telemetry(client: httpx.Client, api_url: str, robot: SimulatedRobot, status: str) -> bool:
    body = {
        "lat": round(robot.lat, 6),
        "lng": round(robot.lng, 6),
        "battery_pct": round(robot.battery, 2),
        "status": status,
    }
    try:
        response = client.post(
            f"{api_url}/api/v1/robot/telemetry", json=body, headers=robot.headers
        )
    except httpx.HTTPError as exc:
        print(f"robot {robot.index}: connection error ({exc}); retrying next tick")
        return False

    if response.status_code == 201:
        print(
            f"robot {robot.index}: {status} {body['lat']:.5f},{body['lng']:.5f} "
            f"battery {body['battery_pct']:.2f}%"
        )
        return True

    print(f"robot {robot.index}: rejected {response.status_code} {response.text}")
    return False


def maybe_send_event(client: httpx.Client, api_url: str, robot: SimulatedRobot) -> None:
    roll = random.random()
    if roll < 0.01:
        alert_type = "intrusion"
    elif roll < 0.04:
        alert_type = "obstacle"
    else:
        return

    try:
        response = client.post(
            f"{api_url}/api/v1/robot/events",
            json={
                "type": alert_type,
                "lat": round(robot.lat, 6),
                "lng": round(robot.lng, 6),
            },
            headers=robot.headers,
        )
        print(f"robot {robot.index}: {alert_type} alert -> {response.status_code}")
    except httpx.HTTPError as exc:
        print(f"robot {robot.index}: event failed ({exc})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate one or more Fleet Control robots.")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--key", action="append", required=True, help="robot API key (repeatable)")
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--events", action="store_true", help="raise random alerts")
    args = parser.parse_args()

    robots = [SimulatedRobot(key, index + 1) for index, key in enumerate(args.key)]
    print(f"Simulating {len(robots)} robot(s) every {args.interval:g}s against {args.api_url}.")

    with httpx.Client(timeout=10) as client:
        try:
            while True:
                for robot in robots:
                    robot.refresh_mission(client, args.api_url)
                    status = robot.step()
                    robot.drain()
                    send_telemetry(client, args.api_url, robot, status)
                    if args.events:
                        maybe_send_event(client, args.api_url, robot)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nSimulator stopped.")


if __name__ == "__main__":
    main()
