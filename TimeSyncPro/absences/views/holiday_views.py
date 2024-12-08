from django.contrib.auth import get_user_model
from django.db.models import Q
from django.views import generic as views
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..forms import RequestHolidayForm, ReviewHolidayForm
from ..models import Absence, Holiday
from ..serializers import HolidayStatusUpdateSerializer
from ...accounts.view_mixins import CRUDUrlsMixin
from ...common.views_mixins import CompanyAccessMixin

User_Model = get_user_model()


class AllHolidaysBaseView(LoginRequiredMixin, views.ListView):
    model = Holiday
    template_name = 'absences/holiday_requests.html'
    paginate_by = 10
    context_object_name = 'objects'
    ordering = ['-start_date']

    def get_queryset(self):
        query = self.request.GET.get('search', '')
        status_filter = self.request.GET.get('status', None)

        queryset = (Holiday.objects.select_related(
            'requester',
            'reviewer',
            'reviewed_by',
            "requester__team",
        ).filter(requester__company=self.request.user.profile.company)).order_by('start_date')

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if query:
            queryset = queryset.filter(
                Q(requester__first_name__icontains=query) |
                Q(requester__last_name__icontains=query) |
                Q(requester__user__email__icontains=query) |
                Q(reviewer__first_name__icontains=query) |
                Q(reviewer__last_name__icontains=query) |
                Q(reviewer__user__email__icontains=query) |
                Q(start_date__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Holiday Requests'
        context['search_value'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


class AllHolidaysView(CompanyAccessMixin, AllHolidaysBaseView):
    pass


class MyHolidaysView(AllHolidaysBaseView):
    template_name = 'absences/my_holidays.html'

    def dispatch(self, request, *args, **kwargs):
        target_requester = None
        if 'slug' in kwargs:
            target_requester = get_object_or_404(User_Model, slug=kwargs['slug'])

        if target_requester and target_requester != request.user:
            messages.error(request, 'You cannot view someone else\'s holiday requests.')
            return redirect("profile", slug=request.user.slug)

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(requester=self.request.user.profile)


class RequestHolidayView(LoginRequiredMixin, views.CreateView):
    model = Holiday
    form_class = RequestHolidayForm
    template_name = 'absences/request_holiday.html'

    def get_success_url(self):
        return reverse('my_holidays', kwargs={'slug': self.request.user.slug})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.requester = self.request.user.profile
        messages.success(self.request, 'Holiday request submitted.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request,
                       'There was an error with your holiday request. Please review the form and try again.')
        return super().form_invalid(form)


# class ReviewHolidayView(LoginRequiredMixin, views.DetailView):
#     model = Holiday
#     form_class = ReviewHolidayForm
#     template_name = 'absences/review_holiday.html'
#
#     def dispatch(self, request, *args, **kwargs):
#         holiday = self.get_object()
#         if (holiday.reviewer != request.user.profile and
#                 not request.user.has_perm('absences.can_update_holiday_status')):
#             raise PermissionDenied('You do not have permission to review this holiday request.')
#         return super().dispatch(request, *args, **kwargs)
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         holiday = self.get_object()
#         requester_team = holiday.requester.get_team()
#         if requester_team:
#             team_members_in_holiday = requester_team.get_team_members_at_holiday(holiday.start_date, holiday.end_date)
#             context['requester_team'] = requester_team
#             context['team_members_in_holiday'] = team_members_in_holiday
#             context['team_members_in_holiday_count'] = requester_team.get_numbers_of_team_members_holiday_days_by_queryset(team_members_in_holiday)
#         context['form'] = self.form_class()
#         return context

class ReviewHolidayView(LoginRequiredMixin, views.DetailView):
    model = Holiday
    form_class = ReviewHolidayForm
    template_name = 'absences/review_holiday.html'

    def get_queryset(self):
        return Holiday.objects.select_related(
            'requester',
            'requester__team',
            'reviewer'
        )

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if (self.object.reviewer != request.user.profile and
                not request.user.has_perm('absences.can_update_holiday_status')):
            raise PermissionDenied('You do not have permission to review this holiday request.')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        holiday = self.object
        requester_team = holiday.requester.get_team()
        if requester_team:
            team_members_in_holiday = (
                requester_team.get_team_members_at_holiday(
                    holiday.start_date,
                    holiday.end_date
                ))

            context.update({
                'requester_team': requester_team,
                'team_members_in_holiday': team_members_in_holiday,
                'team_members_in_holiday_count': requester_team.get_numbers_of_team_members_holiday_days_by_queryset(
                    team_members_in_holiday
                )
            })

        context['form'] = self.form_class()
        return context


class HolidayRequestStatusUpdateView(UpdateAPIView):
    queryset = Holiday.objects.all()
    serializer_class = HolidayStatusUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        holiday = super().get_object()

        if self.request.user.profile == holiday.requester:
            if self.request.data.get('status') != holiday.StatusChoices.CANCELLED:
                raise PermissionDenied('You can only cancel your own holiday requests.')
        elif (self.request.user.profile == holiday.reviewer or
              self.request.user.profile.has_perm('absences.can_update_holiday_status')):
            pass
        else:
            raise PermissionDenied('You do not have permission to update this holiday request.')

        return holiday

    def perform_update(self, serializer):
        holiday = serializer.get_object()

        if serializer.validated_data['status'] in (holiday.StatusChoices.APPROVED, holiday.StatusChoices.DENIED):
            holiday.reviewed_by = self.request.user.profile
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        try:
            holiday = self.get_object()
            serializer = self.get_serializer(holiday, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            new_status = serializer.validated_data['status']
            serializer.save()
            return Response({"message": f"Holiday request {new_status} successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )





