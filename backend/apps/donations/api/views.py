from math import asin, cos, radians, sin, sqrt

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import DonationCenter
from .serializers import DonationCenterSerializer

EARTH_RADIUS_KM = 6371.0


def _haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km between two lat/long points."""
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


class DonationCenterViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Read-only directory of blood donation centers (SRS 3.2.4).

    Visible to every authenticated user regardless of role (SDS permission
    matrix: "View Donation Centers" = Yes/Yes).
    """

    queryset = DonationCenter.objects.all()
    serializer_class = DonationCenterSerializer

    @action(detail=False, methods=["get"])
    def nearby(self, request):
        """Return centers ordered by proximity to ?lat=&lng=.

        Falls back to alphabetical order when coordinates are missing or
        invalid (SRS VBB-ERR-DCM-001).
        """
        centers = list(self.get_queryset())
        try:
            lat = float(request.query_params["lat"])
            lng = float(request.query_params["lng"])
        except (KeyError, TypeError, ValueError):
            data = self.get_serializer(centers, many=True).data
            return Response(
                {"detail": "Provide lat and lng to sort by proximity.", "results": data}
            )

        locatable, unlocatable = [], []
        for center in centers:
            if center.latitude is not None and center.longitude is not None:
                center.distance_km = round(
                    _haversine_km(
                        lat, lng, float(center.latitude), float(center.longitude)
                    ),
                    2,
                )
                locatable.append(center)
            else:
                unlocatable.append(center)

        locatable.sort(key=lambda c: c.distance_km)
        ordered = locatable + unlocatable
        return Response(self.get_serializer(ordered, many=True).data)
