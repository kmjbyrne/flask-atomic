import functools
import json

from flask import Response

JsonResponse = lambda content, *args, **kwargs: Response(
    json.dumps(content),
    content_type="application/json",
    *args, **kwargs
)

JsonOKResponse = functools.partial(JsonResponse, status=200)
JsonCreatedResponse = functools.partial(JsonResponse, status=201)
JsonBadRequestResponse = functools.partial(JsonResponse, status=400)
JsonNotAllowedResponse = functools.partial(JsonResponse, status=405)
JsonOverloadResponse = functools.partial(JsonResponse, status=429)
