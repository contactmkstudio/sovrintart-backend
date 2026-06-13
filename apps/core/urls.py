from django.urls import path
from apps.core import views

urlpatterns = [
    path('announcement/', views.AnnouncementView.as_view(), name='announcement'),
    path('dashboard-stats/', views.DashboardStatsView.as_view(), name='dashboard-stats'),
    path('faqs/', views.FAQListView.as_view(), name='faqs'),
    path('<int:faq_id>/delete-faq/' , views.FAQDeleteView.as_view(), name='delete-faq'),
    path('send-email/' , views.SendEmailView.as_view() , name='send-email'),
    path('banner-images/', views.UploadBannerImages.as_view(), name='banner-images'),
    path('email-subscription/', views.EmailSubscriptionView.as_view(), name='email-subscription'),
]