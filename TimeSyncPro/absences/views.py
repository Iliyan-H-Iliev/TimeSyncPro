from django.views import generic as views
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages

from .forms import RequestHolidayForm, ReviewHolidayForm
from .models import Absence, Holiday


class MyHolidaysView(LoginRequiredMixin, views.ListView):
    template_name = 'absences/my_holidays.html'

    def get_queryset(self):
        return Holiday.objects.filter(requester=self.request.user.profile)


class DetailsHolidayView(LoginRequiredMixin, views.DetailView):
    model = Holiday
    template_name = 'absences/details_holiday.html'

    def get_queryset(self):
        return Holiday.objects.filter(pk=self.kwargs['pk'], requester=self.request.user.profile)


class RequestHolidayView(LoginRequiredMixin, views.CreateView):
    model = Holiday
    form_class = RequestHolidayForm
    template_name = 'absences/request_holiday.html'

    def get_success_url(self):
        return reverse_lazy('my_holidays')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class AllHolidaysView(LoginRequiredMixin, views.ListView):
    template_name = 'absences/all_holidays.html'

    def get_queryset(self):
        return Holiday.objects.filter(user__company=self.request.user.company)


class CancelHolidayView(LoginRequiredMixin, views.UpdateView):
    model = Holiday
    template_name = 'absences/cancel_holiday.html'

    def dispatch(self, request, *args, **kwargs):
        holiday = get_object_or_404(Holiday, pk=kwargs['pk'])
        if holiday.user != request.user:
            messages.error(request, 'You cannot cancel someone else\'s holiday request.')
            return redirect('my_holidays')

    def get_queryset(self):
        return Holiday.objects.filter(pk=self.kwargs['pk'], user=self.request.user.profile)

    def get_success_url(self):
        return reverse_lazy('my_holidays')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['holiday'] = self.object
        return context

    def post(self, request, *args, **kwargs):
        holiday = self.get_object()
        holiday.status = self.model.StatusChoices.CANCELLED
        holiday.save()
        messages.success(request, 'Holiday request cancelled.')
        return redirect('my_holidays')


class ReviewHolidayView(LoginRequiredMixin, PermissionRequiredMixin, views.UpdateView):
    # permission_required = 'absences.can_review_absence'
    # raise_exception = True
    model = Holiday
    form_class = ReviewHolidayForm
    template_name = 'absences/review_holiday.html'

    def get_success_url(self):
        return reverse_lazy('absence_list')

    def form_valid(self, form):
        action = self.request.POST.get('action')
        if action not in [form.instance.StatusChoices.APPROVED, form.instance.StatusChoices.DENIED]:
            return self.form_invalid(form)

        form.instance.status = action
        form.instance.reviewed_by = self.request.user.profile
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid action.')
        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['action'] = self.request.POST.get('action')
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['holiday'] = self.object
        return context





    # def post(self, request, absence_id):
    #     absence = get_object_or_404(Absence, id=absence_id)
    #     action = request.POST.get('action')
    #     review_reason = request.POST.get('review_reason', '')
    #
    #     if action == 'approve':
    #         absence.status = 'approved'
    #         message = 'Absence request approved.'
    #     elif action == 'deny':
    #         absence.status = 'denied'
    #         message = 'Absence request denied.'
    #     else:
    #         messages.error(request, 'Invalid action.')
    #         return redirect('absence_list')
    #
    #     absence.reviewed_by = request.user
    #     absence.review_reason = review_reason
    #     absence.save()
    #
    #     messages.success(request, message)
    #     return redirect('absence_list')
    #
    # def get(self, request, absence_id):
    #     # If someone tries to access via GET, redirect to the absence list
    #     return redirect('absence_list')