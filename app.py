import uvicorn as _uvicorn

class Application():
    def __init__(self, scope):
        self.scope = scope

    async def __call__(self, receive, send):
        method = self.scope["method"]
        path = self.scope["path"]
        
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [
                [b"content-type", b"text/plain"],
            ]
        })
        
        await send({
            "type": "http.response.body",
            "body": f"Hello, world! {method} {path}".encode("utf-8"),
        })

if __name__ == "__main__":
    _uvicorn.run(Application, "0.0.0.0", 8080, log_level="info")
