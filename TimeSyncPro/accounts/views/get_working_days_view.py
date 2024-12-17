import logging
from datetime import datetime
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.status import HTTP_400_BAD_REQUEST
from TimeSyncPro.accounts.models import Profile

logger = logging.getLogger(__name__)

UserModel = get_user_model()


def get_working_days(request):
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    profile_id = request.GET.get("profile_id")

    if start_date and end_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        profile = get_object_or_404(Profile, id=profile_id)
        working_days = profile.get_count_of_working_days_by_period(start_date, end_date)
        remaining_days = profile.remaining_leave_days

        return JsonResponse(
            {"working_days": working_days, "remaining_days": remaining_days}
        )

    return JsonResponse({"error": "Invalid input"}, status=HTTP_400_BAD_REQUEST)
