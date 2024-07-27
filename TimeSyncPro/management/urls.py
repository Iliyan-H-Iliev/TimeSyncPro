from django.urls import path
from .views import ShiftPatternCreateView, ShiftPatternListView, TeamCreateView, TeamListView, ShiftPatternDetailView, \
    TeamEditView, ShiftPatternEditView, ShiftPatternDeleteView, TeamDeleteView

urlpatterns = [
    path('shiftpatterns/', ShiftPatternListView.as_view(), name='shiftpattern list'),
    path('shiftpatterns/new/', ShiftPatternCreateView.as_view(), name='shiftpattern create'),
    path('shiftpatterns/<int:pk>/', ShiftPatternDetailView.as_view(), name='shiftpattern detail'),
    path('shiftpatterns/<int:pk>/edit/', ShiftPatternEditView.as_view(), name='shiftpattern edit'),
    path('shiftpatterns/<int:pk>/delete/', ShiftPatternDeleteView.as_view(), name='shiftpattern delete'),
    path('teams/', TeamListView.as_view(), name='team list'),
    path('teams/new/', TeamCreateView.as_view(), name='team create'),
    # path('teams/<int:pk>/', TeamDetailView.as_view(), name='team detail'),
    path('teams/<int:pk>/edit/', TeamEditView.as_view(), name='team edit'),
    path('teams/<int:pk>/delete/', TeamDeleteView.as_view(), name='team delete'),
]