from app.models.mission import Mission
from tests.conftest import make_route, unique_serial


def _create_robot(client, seed, name="Patrol unit"):
    response = client.post(
        "/api/v1/robots",
        json={"name": name, "serial_number": unique_serial()},
        headers=seed["admin_headers"],
    )
    assert response.status_code == 201
    return response.json()


def _create_mission(client, seed, robot_id, route_id):
    return client.post(
        "/api/v1/missions",
        json={"robot_id": robot_id, "route_id": route_id},
        headers=seed["operator_headers"],
    )


def test_routes_list_includes_waypoints(client, seed, db):
    make_route(db, seed["demo"].id)
    response = client.get("/api/v1/routes", headers=seed["operator_headers"])
    assert response.status_code == 200
    routes = response.json()
    assert routes[0]["name"] == "North perimeter"
    assert len(routes[0]["waypoints"]) == 3
    assert routes[0]["waypoints"][0]["seq"] == 1


def test_full_mission_lifecycle_records_events(client, seed, db):
    route = make_route(db, seed["demo"].id)
    mission = _create_mission(client, seed, seed["robot"].id, route.id).json()
    assert mission["status"] == "scheduled"
    assert mission["robot_name"] == "Atlas"

    started = client.post(
        f"/api/v1/missions/{mission['id']}/start", headers=seed["operator_headers"]
    )
    assert started.status_code == 200
    assert started.json()["status"] == "running"
    assert started.json()["started_at"] is not None
    assert [event["action"] for event in started.json()["events"]] == ["start"]

    stopped = client.post(
        f"/api/v1/missions/{mission['id']}/stop", headers=seed["operator_headers"]
    )
    assert stopped.status_code == 200
    body = stopped.json()
    assert body["status"] == "stopped"
    assert body["ended_at"] is not None
    assert [event["action"] for event in body["events"]] == ["start", "stop"]
    assert body["events"][0]["user_name"] == "Youssef Trabelsi"


def test_invalid_transitions_conflict(client, seed, db):
    route = make_route(db, seed["demo"].id)
    mission = _create_mission(client, seed, seed["robot"].id, route.id).json()

    assert client.post(
        f"/api/v1/missions/{mission['id']}/stop", headers=seed["operator_headers"]
    ).status_code == 409

    client.post(f"/api/v1/missions/{mission['id']}/start", headers=seed["operator_headers"])
    assert client.post(
        f"/api/v1/missions/{mission['id']}/start", headers=seed["operator_headers"]
    ).status_code == 409

    second = _create_mission(client, seed, seed["robot"].id, route.id).json()
    response = client.post(
        f"/api/v1/missions/{second['id']}/start", headers=seed["operator_headers"]
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "This robot already has a running mission"


def test_other_company_objects_are_not_found(client, seed, db):
    route = make_route(db, seed["demo"].id)
    response = client.post(
        "/api/v1/missions",
        json={"robot_id": seed["other_robot"].id, "route_id": route.id},
        headers=seed["operator_headers"],
    )
    assert response.status_code == 404

    mission = _create_mission(client, seed, seed["robot"].id, route.id).json()
    response = client.post(
        f"/api/v1/missions/{mission['id']}/start", headers=seed["other_admin_headers"]
    )
    assert response.status_code == 404


def test_robot_mission_endpoint(client, seed, db):
    route = make_route(db, seed["demo"].id)
    assert client.get("/api/v1/robot/mission", headers=seed["robot_headers"]).json() == {
        "mission": None
    }

    mission = _create_mission(client, seed, seed["robot"].id, route.id).json()
    client.post(f"/api/v1/missions/{mission['id']}/start", headers=seed["operator_headers"])

    body = client.get("/api/v1/robot/mission", headers=seed["robot_headers"]).json()
    assert body["mission"]["id"] == mission["id"]
    assert len(body["mission"]["route"]["waypoints"]) == 3

    assert client.get("/api/v1/robot/mission", headers=seed["other_robot_headers"]).json() == {
        "mission": None
    }
    assert client.get("/api/v1/robot/mission").status_code == 401


def test_start_and_stop_are_recorded_with_user(client, seed, db):
    route = make_route(db, seed["demo"].id)
    mission = _create_mission(client, seed, seed["robot"].id, route.id).json()
    client.post(f"/api/v1/missions/{mission['id']}/start", headers=seed["operator_headers"])

    stored = db.get(Mission, mission["id"])
    assert stored.events[0].user_id == seed["operator"].id
    assert stored.started_at is not None
