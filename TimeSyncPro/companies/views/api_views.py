from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from TimeSyncPro.common.views_mixins import SmallPagination
from TimeSyncPro.companies.models import Team
from TimeSyncPro.companies.serializers import ShiftTeamsSerializer


class ShiftTeamsApiView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = ShiftTeamsSerializer
    pagination_class = SmallPagination

    def get_queryset(self):
        shift_id = self.kwargs['pk']
        company_slug = self.kwargs['company_slug']
        return Team.objects.filter(
            shift__id=shift_id,
            shift__company__slug=company_slug
        ).select_related('company').order_by('name')
