import asyncio
import logging
from datetime import datetime, timedelta
from asgiref.sync import sync_to_async
from django.views import generic as views

from django.contrib.auth import get_user_model

from django.http import JsonResponse
from TimeSyncPro.absences.models import Holiday, Absence

logger = logging.getLogger(__name__)

UserModel = get_user_model()


class CalendarEventsView(views.View):
    @sync_to_async
    def get_profile(self, user):
        return getattr(user, "profile", None)

    @sync_to_async
    def get_holidays(self, profile, start, end):
        return list(
            Holiday.objects.filter(
                requester=profile, start_date__range=[start, end], status="approved"
            )
        )

    @sync_to_async
    def get_absences(self, profile, start, end):
        return list(
            Absence.objects.filter(start_date__range=[start, end], absentee=profile)
        )

    @sync_to_async
    def get_working_days_and_time(self, profile, start, end):
        return profile.get_working_days_with_time(start, end)

    @sync_to_async
    def get_days_off(self, profile, start, end):
        return list(profile.get_days_off(start, end))

    def generate_date_range(self, start_date, end_date):
        days = []
        current = start_date
        while current <= end_date:
            days.append(current)
            current += timedelta(days=1)
        return days

    async def get(self, request, *args, **kwargs):
        start_str = request.GET.get("start")
        end_str = request.GET.get("end")
        event_type = request.GET.get("type")

        try:

            def clean_date(date_str):
                if not date_str:
                    return None
                if "T" in date_str:
                    date_str = date_str.split("T")[0]
                return date_str

            start = datetime.strptime(clean_date(start_str), "%Y-%m-%d").date()
            end = datetime.strptime(clean_date(end_str), "%Y-%m-%d").date()

        except (ValueError, TypeError, AttributeError) as e:
            print(f"Error parsing dates: {e}")
            return JsonResponse({"error": "Invalid date format"}, status=400)

        profile = await self.get_profile(request.user)
        if not profile:
            return JsonResponse({"error": "Profile not found for user"}, status=404)

        args = (profile, start, end)

        working_days_and_time, holidays, absences, days_off = await asyncio.gather(
            self.get_working_days_and_time(*args),
            self.get_holidays(*args),
            self.get_absences(*args),
            self.get_days_off(*args),
        )

        formatted_working_days = [
            {
                "date": date.isoformat(),
                "start_time": times["start_time"].strftime("%H:%M"),
                "end_time": times["end_time"].strftime("%H:%M"),
            }
            for date, times in working_days_and_time.items()
        ]

        holiday_events = []
        for holiday in holidays:
            date_range = self.generate_date_range(holiday.start_date, holiday.end_date)
            for date in date_range:
                holiday_events.append(
                    {
                        "date": date.isoformat(),
                        "title": f"Holiday: {holiday.reason}",
                        "days": (holiday.end_date - holiday.start_date).days + 1,
                    }
                )

        absence_events = []
        for absence in absences:
            date_range = self.generate_date_range(absence.start_date, absence.end_date)
            for date in date_range:
                absence_events.append(
                    {
                        "date": date.isoformat(),
                        "title": f"Absence: {absence.reason}",
                        "days": (absence.end_date - absence.start_date).days + 1,
                    }
                )

        response_data = {
            "workingDays": formatted_working_days,
            "holidays": holiday_events,
            "absences": absence_events,
            "daysOff": [d.isoformat() for d in days_off],
        }

        return JsonResponse(response_data)
