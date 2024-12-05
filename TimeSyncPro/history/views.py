from django.contrib.auth import get_user_model
from django.shortcuts import render
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from itertools import chain
from operator import attrgetter

from TimeSyncPro.accounts.models import Profile
from TimeSyncPro.common.views_mixins import SmallPagination
from TimeSyncPro.companies.models import Team, Shift, Department
from TimeSyncPro.history.models import History
from TimeSyncPro.history.serializers import HistorySerializer

UserModel = get_user_model()


# Create your views here.
class TeamHistoryAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = HistorySerializer
    pagination_class = SmallPagination

    def get_queryset(self):
        team_id = self.kwargs['pk']
        return History.get_for_object(
            Team.objects.get(id=team_id)
        ).select_related('changed_by')


class ShiftHistoryAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = HistorySerializer
    pagination_class = SmallPagination

    def get_queryset(self):
        shift_id = self.kwargs['pk']
        return History.get_for_object(
            Shift.objects.get(id=shift_id)
        ).select_related('changed_by')


class DepartmentHistoryAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = HistorySerializer
    pagination_class = SmallPagination

    def get_queryset(self):
        department_id = self.kwargs['pk']
        return History.get_for_object(
            Department.objects.get(id=department_id)
        ).select_related('changed_by')


class EmployeeHistoryAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = HistorySerializer
    pagination_class = SmallPagination

    def get_queryset(self):
        employee_pk = self.kwargs['pk']
        user = UserModel.objects.get(pk=employee_pk)

        # Get both histories
        user_history = History.get_for_object(user).select_related(
            'content_type',
            'changed_by'
        )
        profile_history = History.get_for_object(user.profile).select_related(
            'content_type',
            'changed_by'
        )

        # Combine and sort
        return sorted(
            chain(user_history, profile_history),
            key=attrgetter('timestamp'),
            reverse=True
        )

    # def get_queryset(self):
    #     employee_pk = self.kwargs['pk']
    #     return History.get_for_object(
    #         UserModel.objects.get(pk=employee_pk)
    #     ).select_related('changed_by')


