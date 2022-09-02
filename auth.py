from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

import jwt
import pydantic
from fastapi import Cookie, HTTPException, Response
from pydantic import BaseModel

# TODO: 環境変数から値を取ってくるようにする
SECRET = "dummy-token-do-not-use"
COOKIE_SESSION_KEY = "session"
SESSION_TTL = timedelta(hours=1)


# TODO: データベースに持たせる
class Group(str, Enum):
    admin = "admin"
    userGroup1 = "user-group-1"
    userGroup2 = "user-group-2"


class Role(str, Enum):
    admin = "admin"
    common = "common"
    items = "items"


userGroupMapping: dict[str, Group] = {
    "admin": Group.admin,
    "user-1": Group.userGroup1,
    "user-2": Group.userGroup1,
    "user-3": Group.userGroup2,
}

groupRoleMapping: dict[Group, list[Role]] = {
    Group.admin: [*Role],
    Group.userGroup1: [Role.common, Role.items],
    Group.userGroup2: [Role.common],
}


class AuthenticationError(Exception):
    ...


class AuthInfo(BaseModel):
    userId: str
    roles: list[Role]
    exp: datetime

    def token(self) -> str:
        return jwt.encode(self.dict(), SECRET, algorithm="HS256")

    @classmethod
    def decode(cls, session: Optional[str]) -> "AuthInfo":
        if session is None:
            raise AuthenticationError("トークンが無効です")

        try:
            data = jwt.decode(session, SECRET, algorithms=["HS256"])
            authInfo = AuthInfo(
                roles=data["roles"], userId=data["userId"], exp=data["exp"]
            )
        except (
            pydantic.error_wrappers.ValidationError,
            KeyError,
            jwt.exceptions.InvalidSignatureError,
            jwt.exceptions.ExpiredSignatureError,
        ) as e:
            raise AuthenticationError("トークンが無効です") from e

        return authInfo

    @classmethod
    def login(cls, response: Response, userId: str, password: str) -> "AuthInfo":
        if userId not in userGroupMapping:
            raise HTTPException(status_code=403)

        # 説明用のアプリケーションのため省略
        if password == "":
            raise HTTPException(status_code=403)

        authInfo = AuthInfo(
            userId=userId,
            roles=groupRoleMapping[userGroupMapping[userId]],
            exp=datetime.now(tz=timezone.utc) + SESSION_TTL,
        )

        response.set_cookie(
            key=COOKIE_SESSION_KEY,
            value=authInfo.token(),
            secure=True,
            httponly=True,
            samesite="lax",
        )

        return authInfo

    @classmethod
    def logout(cls, response: Response) -> None:
        response.delete_cookie(COOKIE_SESSION_KEY)


@dataclass(frozen=True, eq=True)
class AccessControl:
    permit: set[Role]

    def __call__(
        self,
        session: Optional[str] = Cookie(default=None, alias=COOKIE_SESSION_KEY),
    ) -> AuthInfo:
        try:
            authInfo = AuthInfo.decode(session)
        except AuthenticationError as e:
            raise HTTPException(status_code=403) from e

        if not self.has_compatible_role(authInfo):
            raise HTTPException(status_code=403)

        return authInfo

    def __hash__(self) -> int:
        return hash(",".join(sorted(map(str, list(self.permit)))))

    def has_compatible_role(self, requesterAuthInfo: AuthInfo) -> bool:
        requesterRoles = set(requesterAuthInfo.roles)
        return len(self.permit.intersection(requesterRoles)) > 0
