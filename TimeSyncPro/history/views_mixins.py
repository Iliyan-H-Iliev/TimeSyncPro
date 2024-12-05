from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator

from TimeSyncPro.history.models import History


class HistoryViewMixin:
    history_paginate_by = 3  # Default value, can be overridden in views

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        history = (
            History.objects.filter(
                content_type=ContentType.objects.get_for_model(self.object),
                object_id=self.object.id).select_related(
                'changed_by',
                'content_type'
            ).prefetch_related('content_object').order_by('-timestamp'))

        # Handle pagination
        page = self.request.GET.get('history_page', 1)
        paginator = Paginator(history, self.history_paginate_by)
        context['history'] = paginator.get_page(page)

        return context
