# fastapi-access-control-example

FastAPIの標準機能+αで作るアクセスコントロール

## セットアップ

```
pip install -r requirements.txt
```

## 起動

```
uvicorn main:app --reload
```

### ログイン

[Httpie](https://httpie.io/) を使った動作確認

```
$ http --session=test-admin POST localhost:8000/auth/ userId=admin password=password
HTTP/1.1 200 OK
content-length: 4
content-type: application/json
server: uvicorn
set-cookie: session=eyJ0eXAiOiJKV...; HttpOnly; Path=/; SameSite=lax; Secure

null

$ http --session=test-admin GET localhost:8000/items/
HTTP/1.1 200 OK
content-length: 37
content-type: application/json
server: uvicorn

[
    {
        "name": "item-1"
    },
    {
        "name": "item-2"
    }
]
```

## テスト

```
pytest test.py
```
