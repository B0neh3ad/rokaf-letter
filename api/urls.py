from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api import views

router = DefaultRouter()
router.register(r'trainees', views.TraineeViewSet, basename='trainee')
router.register(r'letters', views.LetterViewSet, basename='letter_list')

urlpatterns = [
    path('gpt/test/', views.GptTest.as_view(), name='gpt_test'),
    path('trainees/search/', views.TraineeSearchView.as_view(), name='search_trainee'),
    path('', include(router.urls)),
]