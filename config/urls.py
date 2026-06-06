
from django.contrib import admin
from django.urls import path , include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/core/' , include('apps.core.urls')),
    path('api/accounts/' , include('apps.accounts.urls')),
    path('api/carts/' , include('apps.carts.urls')),
    path('api/products/' , include('apps.products.urls')),
    path('api/create-order/' , include('apps.orders.urls')),
    path('api/verify-payment/' , include('apps.orders.urls')),
    path('api/paypal/', include('apps.orders.paypal_urls')),
    path('api/get-orders/', include('apps.orders.urls')),
]
