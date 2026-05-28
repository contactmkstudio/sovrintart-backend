from django.urls import path , include
from apps.core import views

urlpatterns = [
    path('faqs/', views.FAQListView.as_view(), name='faqs'),
    path('faqs', views.FAQListView.as_view(), name='faqs-no-slash'),  # Support both
]