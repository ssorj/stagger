import sys
import json

from data import *
from starlette import *
from starlette.routing import *

@asgi_application
async def serve_tag_index(request):
    return JSONResponse(data["tags"])
    
@asgi_application
async def serve_tag(request):
    tag_id = request._scope["kwargs"]["tag_id"]
    
    if request.method == "GET":
        content = data["tags"][tag_id]
        return JSONResponse(content)

    if request.method == "PUT":
        body = await request.body()
        data["tags"][tag_id] = json.loads(body)
        return Response("")

    if request.method == "DELETE":
        del data["tags"][tag_id]
        return Response("")

@asgi_application
async def serve_artifact_index(request):
    tag_id = request._scope["kwargs"]["tag_id"]
    content = data["tags"][tag_id]["artifacts"]
    return JSONResponse(content)
        
@asgi_application
async def serve_artifact(request):
    tag_id = request._scope["kwargs"]["tag_id"]
    artifact_name = request._scope["kwargs"]["artifact_name"]

    if request.method == "GET":
        content = data["tags"][tag_id]["artifacts"][artifact_name]
        return JSONResponse(content)
    
    if request.method == "PUT":
        raise NotImplementedError()

app = Router([
    Path("/api/tags", app=serve_tag_index, methods=["GET"]),
    Path("/api/tags/{tag_id}", app=serve_tag, methods=["PUT", "GET", "DELETE"]),
    Path("/api/tags/{tag_id}/artifacts", app=serve_artifact_index, methods=["GET"]),
    Path("/api/tags/{tag_id}/artifacts/{artifact_name}", app=serve_artifact, methods=["PUT", "GET"]),
])

def pprint(*args, **kwargs):
    import pprint as _pprint
    kwargs["stream"] = sys.stderr
    _pprint.pprint(*args, **kwargs)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, "0.0.0.0", 8080, log_level="warning")
