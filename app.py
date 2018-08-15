import sys
import uvicorn

from starlette import *
from starlette.routing import *

# Match the eng git name when you can
#
# maven:<group>:<artifact>:<version>  # <version> embeds the build number
# rpm:<srpm-name>:<version>:<release> # <release> is the build number
#
# XXX Need multiple artifacts for each tag?

tags = {
    "rh-qpid-proton-j:master:untested": "maven:org.apache.qpid:proton-j:0.28.1.B1",
    "rh-pooled-jms:master:tested": "maven:org.messaginghub:pooled-jms:1.0.4.B2",
    "rh-qpid-jms:0.34.0-amq:untested": "maven:org.apache.qpid:qpid-jms-client:0.34.0.B9",
    "rh-qpid-dispatch:master:tested": "rpm:qpid-dispatch:1.3.0:4",
}

@asgi_application
async def put_get_tag(request):
    id = request._scope["kwargs"]["id"]
    content = ""
    
    if request.method == "PUT":
        tags[id] = await request.body()
    elif request.method == "GET":
        content = tags[id]
    else:
        raise Exception()

    return Response(content, media_type="text/plain")

app = Router([
    Path("/tags/{id}", app=put_get_tag, methods=["PUT", "GET"]),
])

def eprint(*args, **kwargs):
    kwargs["file"] = sys.stderr
    print(*args, **kwargs)
        
def pprint(*args, **kwargs):
    import pprint as _pprint
    kwargs["stream"] = sys.stderr
    _pprint.pprint(*args, **kwargs)

if __name__ == "__main__":
    uvicorn.run(app, "0.0.0.0", 8080, log_level="info")
