# posture_detection/urls.py
from django.contrib import admin
from django.urls import path
from webcam import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('video_feed/', views.video_feed, name='video_feed'),
    path('get_posture_status/', views.get_posture_status, name='get_posture_status'),
]