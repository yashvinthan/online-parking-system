from django.urls import path
from . import views

app_name = 'manet'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/run/', views.run_simulation, name='run_simulation'),
]
