from django.urls import path
from apps.products import views

urlpatterns = [
    path('get-product/<int:pk>/', views.GetProductById.as_view(), name='get-product-by-id'),
    path('add-products/' , views.AddProduct.as_view() , name='add-products'),
    path('get-products/', views.GetProducts.as_view(), name='get-products'),
    path('delete-product/<int:pk>/', views.DeleteProduct.as_view(), name='delete-products'),
    path('get-products-by-category/<str:category>/', views.GetProductsByCategory.as_view(), name='get-products-by-category'),
]