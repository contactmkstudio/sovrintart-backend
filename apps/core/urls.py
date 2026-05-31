from django.urls import path
from apps.core import views

urlpatterns = [
    path('faqs/', views.FAQListView.as_view(), name='faqs'),
    path('send-email/' , views.SendEmailView.as_view() , name='send-email')
]