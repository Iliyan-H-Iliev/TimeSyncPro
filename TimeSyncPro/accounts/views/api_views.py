import logging
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import logout, get_user_model
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from TimeSyncPro.accounts.models import Profile
from TimeSyncPro.accounts.serializers import EmployeeSerializer
from TimeSyncPro.common.views_mixins import SmallPagination

logger = logging.getLogger(__name__)

UserModel = get_user_model()


class TeamEmployeesAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = EmployeeSerializer
    pagination_class = SmallPagination

    def get_queryset(self):
        return (
            Profile.objects.filter(
                team_id=self.kwargs["pk"],
                team__company__slug=self.kwargs["company_slug"],
            )
            .select_related("user")
            .order_by("first_name")
        )


class ShiftEmployeesAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = EmployeeSerializer
    pagination_class = SmallPagination

    def get_queryset(self):
        return (
            Profile.objects.filter(
                shift_id=self.kwargs["pk"],
                shift__company__slug=self.kwargs["company_slug"],
            )
            .select_related("user")
            .order_by("first_name")
        )


class DepartmentEmployeesAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = EmployeeSerializer
    pagination_class = SmallPagination

    def get_queryset(self):
        return (
            Profile.objects.filter(
                department_id=self.kwargs["pk"],
                department__company__slug=self.kwargs["company_slug"],
            )
            .select_related("user")
            .order_by("first_name")
        )


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            logout(request)

            return Response(
                {"message": "Successfully logged out."}, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": "Failed to logout. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
