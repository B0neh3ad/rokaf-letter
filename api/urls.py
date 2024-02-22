from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api import views

router = DefaultRouter()
router.register(r'trainees', views.TraineeViewSet, basename='trainee')
router.register(r'letters', views.LetterViewSet, basename='letter_list')

urlpatterns = [
    path('gpt/test/', views.gpt_test, name='gpt_test'),
    path('trainees/search/', views.search_trainee, name='search_trainee'),
    path('', include(router.urls)),
]