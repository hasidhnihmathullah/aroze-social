from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('post/create/', views.create_post, name='create_post'),
    path('post/<int:post_id>/like/', views.toggle_like, name='toggle_like'),
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('user/<int:user_id>/follow/', views.toggle_follow, name='toggle_follow'),
    path('logout/', views.user_logout, name='logout'),
]