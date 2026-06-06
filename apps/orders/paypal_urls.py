from django.urls import path
from apps.orders.views import CreatePayPalOrderView, CapturePayPalOrderView

urlpatterns = [
    path('create/', CreatePayPalOrderView.as_view(), name='paypal-create-order'),
    path('capture/', CapturePayPalOrderView.as_view(), name='paypal-capture-order'),
]
