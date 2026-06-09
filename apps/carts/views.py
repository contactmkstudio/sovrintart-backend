from django.shortcuts import render
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
import json

from apps.carts.serializer import AddToCartSerializer, CartSerializer, AddToFavouriteSerializer, FavouriteSerializer
from apps.carts.models import Cart, CartItem, Favourite, FavouriteItem
from apps.accounts.models import User
from apps.products.models import Product


@method_decorator(csrf_exempt, name='dispatch')
class AddToCart(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            serializer = AddToCartSerializer(data=data)
            
            if serializer.is_valid():
                user_email = serializer.validated_data['user_email']
                product_id = serializer.validated_data['product_id']
                
                user = User.objects.get(email=user_email)
                product = Product.objects.get(id=product_id)
                
                # Get or create cart
                cart, created = Cart.objects.get_or_create(user=user)
                
                # Add item (only one per product)
                cart_item, item_created = CartItem.objects.get_or_create(
                    cart=cart,
                    product=product
                )
                
                return JsonResponse({
                    "message": "Product added to cart successfully",
                    "data": {
                        "product_id": product_id
                    }
                }, status=201)
            print(f"Serializer errors: {serializer.errors}")
            return JsonResponse(serializer.errors, status=400)
        except json.JSONDecodeError as e:
            return JsonResponse({"error": "Invalid JSON"}, status=400)    
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except Product.DoesNotExist:
            return JsonResponse({"error": "Product not found"}, status=404)
        except Exception as e:
            print(f"Exception: {e}")
            return JsonResponse({"error": str(e)}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class GetCart(View):
    def get(self, request):
        try:
            user_email = request.GET.get('email')
            if not user_email:
                return JsonResponse({"error": "Email parameter required"}, status=400)
            
            cart = Cart.objects.get(user__email=user_email)
            serializer = CartSerializer(cart)
            return JsonResponse({
                "message": "Cart fetched successfully",
                "data": serializer.data
            }, status=200)
        except Cart.DoesNotExist:
            return JsonResponse({"error": "Cart not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class AddToFavourite(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            serializer = AddToFavouriteSerializer(data=data)

            if serializer.is_valid():
                user_email = serializer.validated_data['user_email']
                product_id = serializer.validated_data['product_id']

                user = User.objects.get(email=user_email)
                product = Product.objects.get(id=product_id)

                favourite, _ = Favourite.objects.get_or_create(user=user)
                _, item_created = FavouriteItem.objects.get_or_create(
                    favourite=favourite,
                    product=product
                )

                return JsonResponse({
                    "message": "Product added to favourites successfully",
                    "data": {"product_id": product_id}
                }, status=201)
            return JsonResponse(serializer.errors, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except Product.DoesNotExist:
            return JsonResponse({"error": "Product not found"}, status=404)
        except Exception as e:
            print(f"Exception: {e}")
            return JsonResponse({"error": str(e)}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class GetFavourites(View):
    def get(self, request):
        try:
            user_email = request.GET.get('email')
            if not user_email:
                return JsonResponse({"error": "Email parameter required"}, status=400)

            favourite = Favourite.objects.get(user__email=user_email)
            serializer = FavouriteSerializer(favourite)
            return JsonResponse({
                "message": "Favourites fetched successfully",
                "data": serializer.data
            }, status=200)
        except Favourite.DoesNotExist:
            return JsonResponse({"error": "No favourites found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
