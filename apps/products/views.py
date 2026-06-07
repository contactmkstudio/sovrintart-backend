import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from apps.products.models import Product
from apps.products.serializer import ProductSerializer

@method_decorator(csrf_exempt, name='dispatch')
class AddProduct(View):
    def post(self , request):
        try:
            data = json.loads(request.body)

            serializer = ProductSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({
                    "message": "Product created successfully",
                    "data": serializer.data
                }, status=201)
            print(f"Serializer errors: {serializer.errors}")
            return JsonResponse(serializer.errors, status=400)
        except json.JSONDecodeError as e:
            return JsonResponse({"error": "Invalid JSON"}, status=400)    
        except Exception as e:
            print(f"Exception: {e}")
            return JsonResponse({"error": str(e)}, status=400)  

@method_decorator(csrf_exempt, name='dispatch')
class GetProducts(View):
    def get(self , request):
        try:
            products = Product.objects.all()
            serializer = ProductSerializer(products, many=True)
            return JsonResponse({
                "message": "Products retrieved successfully",
                "data": serializer.data
            }, status=200)
        except Exception as e:
            print(f"Exception: {e}")
            return JsonResponse({"error": str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class GetProductById(View):
    def get(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
            serializer = ProductSerializer(product)
            return JsonResponse({
                "message": "Product retrieved successfully",
                "data": serializer.data
            }, status=200)
        except Product.DoesNotExist:
            return JsonResponse({"error": "Product not found"}, status=404)
        except Exception as e:
            print(f"Exception: {e}")
            return JsonResponse({"error": str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class DeleteProduct(View):
    def delete(self , request , pk):
        try:
            product = Product.objects.get(pk=pk)
            product.delete()
            return JsonResponse({
                "message": "Product deleted successfully"
            }, status=200)
        except Product.DoesNotExist:
            return JsonResponse({"error": "Product not found"}, status=404)
        except Exception as e:
            print(f"Exception: {e}")
            return JsonResponse({"error": str(e)}, status=400)          