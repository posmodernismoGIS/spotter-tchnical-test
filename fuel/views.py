from django.shortcuts import render
import time
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import RouteQuerySerializer
from .services.locations import LocationError, resolve
from .services.optimizer import UnreachableRouteError
from .services.ors_client import RoutingError
from .services.planner import plan_trip

ERROOR_STATUS = {LocationError: 400, UnreachableRouteError: 422, RoutingError:502}

def _plan(params):
    query = RouteQuerySerializer(data=params)
    query.is_valid(raise_exception=True)
    return plan_trip(resolve(query.validated_data["start"]),
                     resolve(query.validated_data["finish"]))
    
class RoutePlanView(APIView):
    def get(self, request):
        t0 = time.perf_counter()
        try:
            result = _plan(request.querty_params)
        except tuple(ERROOR_STATUS) as exc:
            return Response({"error": str(exc)}, status=ERROOR_STATUS[type(exc)])
        result["map_url"] = request.build_absolute_uri(reverse("route-map")) + "?" + request.GET.urlencode()
        result["elapsed_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        return Response(result)
            
# def route_map(request):
#     try:
#         result = _plan(request.GET)
#     except (ValidationError, *ERROOR_STATUS) as exc:
#         return HttpResponseBadRequest(str(exc))
#     return render(request, "fuel")