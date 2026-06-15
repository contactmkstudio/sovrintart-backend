from django.urls import path
from apps.orders.views import CreateOrderView, VerifyPaymentView, RazorpayWebhookView, GetOrdersView , GetPaidOrdersView


# // Define URL patterns for the orders app

urlpatterns = [
    path('create/', CreateOrderView.as_view(), name='create-order'),
    path('verify/', VerifyPaymentView.as_view(), name='verify-payment'),
    path('webhook/', RazorpayWebhookView.as_view(), name='razorpay-webhook'),
    path('orders/', GetOrdersView.as_view(), name='get-orders'),
    path('paid-orders/', GetPaidOrdersView.as_view(), name='get-paid-orders')
]
