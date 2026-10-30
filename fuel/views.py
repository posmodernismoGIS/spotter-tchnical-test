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

ERROR_STATUS = {LocationError: 400, UnreachableRouteError: 422, RoutingError:502}


class RoutePlanView(APIView):

    def get(self, request):
        t0 = time.perf_counter()
        query = RouteQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True) 
        try:
            result = plan_trip(resolve(query.validated_data["start"]),
                               resolve(query.validated_data["finish"]))
        except tuple(ERROR_STATUS) as exc:
            return Response({"error": str(exc)}, status=ERROR_STATUS[type(exc)])
        result["elapsed_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        return Response(result)