from django.urls import path
from .views import ShiftPatternCreateViewNot, ShiftPatternListViewNot, TeamCreateViewNot, TeamListViewNot, ShiftPatternDetailViewNot, \
    TeamEditViewNot, ShiftPatternEditViewNot, ShiftPatternDeleteViewNot, TeamDeleteViewNot

urlpatterns = [
    path('shiftpatterns/', ShiftPatternListViewNot.as_view(), name='shiftpattern list'),
    path('shiftpatterns/new/', ShiftPatternCreateViewNot.as_view(), name='shiftpattern create'),
    path('shiftpatterns/<int:pk>/', ShiftPatternDetailViewNot.as_view(), name='shiftpattern detail'),
    path('shiftpatterns/<int:pk>/edit/', ShiftPatternEditViewNot.as_view(), name='shiftpattern edit'),
    path('shiftpatterns/<int:pk>/delete/', ShiftPatternDeleteViewNot.as_view(), name='shiftpattern delete'),
    path('teams/', TeamListViewNot.as_view(), name='team list'),
    path('teams/new/', TeamCreateViewNot.as_view(), name='team create'),
    # path('teams/<int:pk>/', TeamDetailView.as_view(), name='team detail'),
    path('teams/<int:pk>/edit/', TeamEditViewNot.as_view(), name='team edit'),
    path('teams/<int:pk>/delete/', TeamDeleteViewNot.as_view(), name='team delete'),
]