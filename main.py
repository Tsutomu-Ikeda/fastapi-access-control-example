from fastapi import Depends, FastAPI, Response
from pydantic import BaseModel

from auth import AccessControl, AuthInfo, Role

app = FastAPI()


class LoginRequest(BaseModel):
    userId: str
    password: str


@app.post("/auth/")
def login(body: LoginRequest, response: Response) -> None:
    AuthInfo.login(response, body.userId, body.password)


@app.get("/auth/")
def getAuthInfo(authInfo: AuthInfo = Depends(AccessControl(permit={Role.common}))):
    return authInfo


@app.delete("/auth/")
def logout(response: Response) -> None:
    AuthInfo.logout(response)


@app.get(
    "/items/", dependencies=[Depends(AccessControl(permit={Role.items, Role.admin}))]
)
def getItems():
    return [{"name": "item-1"}, {"name": "item-2"}]


@app.post(
    "/items/", dependencies=[Depends(AccessControl(permit={Role.items, Role.admin}))]
)
def postItem():
    # 保存処理
    return {"result": "ok"}


@app.delete("/items/", dependencies=[Depends(AccessControl(permit={Role.admin}))])
def deleteItem():
    # 削除処理
    return {"result": "ok"}
