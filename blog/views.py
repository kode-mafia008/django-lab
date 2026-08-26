from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse


@api_view(["GET"])
def ping(request):
    return Response({"status": "ok"})

def Home(request):
    return HttpResponse("Hello, Suraj!")
