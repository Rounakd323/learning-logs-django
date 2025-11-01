from django.urls import path
from . import views

urlpatterns = [
    # path('test/', views.test_view, name='test_view'),
    path('add_topic/', views.add_topic, name='add_topic'),
    path('topics/', views.get_topics, name='get_topics'),

    path('add_entry/', views.add_entry, name='add_entry'),
    path('entries/', views.get_entries, name='get_entries'),
    path('', views.topics_page, name='topics_page'),          # Home -> topics.html
    path('entries_page/', views.entries_page, name='entries_page'),
    path('topics_page/', views.topics_page, name='topics_page'),

    path('register/', views.register_user, name='register_user'),
    path('login/', views.login_user, name='login_user'),
    path('logout/', views.logout_user, name='logout_user'),
    path('login_page/', views.login_page, name='login_page'),
    path('register_page/', views.register_page, name='register_page'),
       path('', views.home, name='home'),

    path('add_topic/', views.add_topic, name='add_topic'),
    path('topics/', views.get_topics, name='get_topics'),
    path('add_entry/', views.add_entry, name='add_entry'),
    path('entries/', views.get_entries, name='get_entries'),

    path('topics_page/', views.topics_page, name='topics_page'),
    path('entries_page/', views.entries_page, name='entries_page'),

    path('login_page/', views.login_page, name='login_page'),
    path('register_page/', views.register_page, name='register_page'),
    path('login_user/', views.login_user, name='login_user'),
    path('register_user/', views.register_user, name='register_user'),
    path('logout_user/', views.logout_user, name='logout_user'),

    path('activity/', views.activity_view, name='activity'),

]
