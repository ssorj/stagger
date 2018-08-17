import sys
import json

from data import *
from starlette import *
from starlette.routing import *

data = None

@asgi_application
async def serve_tag_index(request):
    return JSONResponse(data.tags)
    
@asgi_application
async def serve_tag(request):
    print(111, data)
    
    tag_id = request._scope["kwargs"]["tag_id"]
    
    if request.method == "GET":
        content = data.tags[tag_id]
        return JSONResponse(content)

    if request.method == "PUT":
        body = await request.body()

        with data.lock:
            data.tags[tag_id] = json.loads(body)

        data.modified.set()
            
        return Response("")

    if request.method == "DELETE":
        with data.lock:
            del data.tags[tag_id]
            
        data.modified.set()
            
        return Response("")

@asgi_application
async def serve_artifact_index(request):
    tag_id = request._scope["kwargs"]["tag_id"]
    content = data.tags[tag_id]["artifacts"]
    return JSONResponse(content)
        
@asgi_application
async def serve_artifact(request):
    tag_id = request._scope["kwargs"]["tag_id"]
    artifact_name = request._scope["kwargs"]["artifact_name"]

    if request.method == "GET":
        content = data.tags[tag_id]["artifacts"][artifact_name]
        return JSONResponse(content)
    
    if request.method == "PUT":
        raise NotImplementedError()

if __name__ == "__main__":
    router = Router([
        Path("/api/tags", app=serve_tag_index, methods=["GET"]),
        Path("/api/tags/{tag_id}", app=serve_tag, methods=["PUT", "GET", "DELETE"]),
        Path("/api/tags/{tag_id}/artifacts", app=serve_artifact_index, methods=["GET"]),
        Path("/api/tags/{tag_id}/artifacts/{artifact_name}", app=serve_artifact, methods=["PUT", "GET"]),
    ])

    data = Data("data.json")
    data.load()
    
    save_thread = SaveThread(data)
    save_thread.start()
    
    import uvicorn
    uvicorn.run(router, "0.0.0.0", 8080, log_level="warning")
