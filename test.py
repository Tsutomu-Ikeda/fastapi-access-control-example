from datetime import datetime, timedelta, timezone

import freezegun
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from more_itertools import powerset

from auth import AccessControl, AuthInfo, Role
from main import app


@pytest.fixture(scope="function")
def test_client() -> TestClient:
    return TestClient(app)


@pytest.fixture(params=["user-1"])
def override_access_control_user(request):
    return request.param


@pytest.fixture
def override_access_control(role_patterns, override_access_control_user):
    def mock_access_control(access_control):
        def _mock_access_control():
            accessControlData = AuthInfo(
                roles=role_patterns,
                userId=override_access_control_user,
                exp=datetime.now(tz=timezone.utc) + timedelta(hours=1),
            )
            if access_control.has_compatible_role(accessControlData):
                return accessControlData
            else:
                raise HTTPException(status_code=403)

        return _mock_access_control

    for mock_target_roles in powerset([*Role]):
        app.dependency_overrides[
            AccessControl(permit=set(mock_target_roles))
        ] = mock_access_control(AccessControl(permit=set(mock_target_roles)))

    yield

    for mock_target_roles in powerset([*Role]):
        del app.dependency_overrides[AccessControl(permit=set(mock_target_roles))]


@freezegun.freeze_time("2022-08-30 13:00:00")
def test_normal():
    accessControl = AccessControl(permit={Role.admin})

    accessControlData = accessControl(
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VySWQiOiJhZG1pbiIsInJvbGVzIjpbImFkbWluIl0sImV4cCI6MTY2MTg2NjIwMH0.0MaSk8cecVa90jx0rAvw9Hfzsd9UShuFjKC1Sci8xjU"
    )
    assert accessControlData.roles == [Role.admin]
    assert accessControlData.userId == "admin"

    with pytest.raises(HTTPException) as e:
        accessControl(
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VySWQiOiJ1c2VyLTMiLCJyb2xlcyI6WyJjb21tb24iXSwiZXhwIjoxNjYxODY2MjAwfQ.5iIILqrCGeitsTrXUdY0sPm7-e_MjsW96u3niymE2YU"
        )

    assert e.value.status_code == 403


@freezegun.freeze_time("2022-08-30 14:00:00")
def test_expired():
    accessControl = AccessControl(permit={Role.admin})

    with pytest.raises(HTTPException) as e:
        accessControl(
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VySWQiOiJhZG1pbiIsInJvbGVzIjpbImFkbWluIl0sImV4cCI6MTY2MTg2NjIwMH0.0MaSk8cecVa90jx0rAvw9Hfzsd9UShuFjKC1Sci8xjU"
        )

    assert e.value.status_code == 403


@pytest.mark.usefixtures("override_access_control")
@pytest.mark.parametrize(
    "role_patterns",
    [
        {Role.admin},
    ],
)
def test_admin(test_client: TestClient):
    response = test_client.get("/items/")
    assert response.status_code == 200


@pytest.mark.usefixtures("override_access_control")
@pytest.mark.parametrize(
    "role_patterns",
    [
        {Role.common},
    ],
)
def test_forbidden(test_client: TestClient):
    response = test_client.get("/items/")
    assert response.status_code == 403
