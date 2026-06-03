from django.urls import path,include
from apps.carts import views

urlpatterns = [  
    path('add-to-cart/', views.AddToCart.as_view(), name='add-to-cart'),
    path('get-cart-item/', views.GetCart.as_view(), name='get-cart'),
]