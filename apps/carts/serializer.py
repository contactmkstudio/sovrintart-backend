from rest_framework import serializers
from .models import Cart, CartItem, Favourite, FavouriteItem
from apps.products.models import Product
from apps.products.serializer import ProductSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_details', 'created_at']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'created_at', 'updated_at']


class AddToCartSerializer(serializers.Serializer):
    user_email = serializers.EmailField()
    product_id = serializers.IntegerField()

    def validate(self, data):
        product_id = data.get('product_id')
        if not Product.objects.filter(id=product_id).exists():
            raise serializers.ValidationError("Product does not exist")
        return data


class FavouriteItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = FavouriteItem
        fields = ['id', 'product', 'product_details', 'created_at']


class FavouriteSerializer(serializers.ModelSerializer):
    items = FavouriteItemSerializer(many=True, read_only=True)

    class Meta:
        model = Favourite
        fields = ['id', 'user', 'items', 'created_at', 'updated_at']


class AddToFavouriteSerializer(serializers.Serializer):
    user_email = serializers.EmailField()
    product_id = serializers.IntegerField()

    def validate(self, data):
        product_id = data.get('product_id')
        if not Product.objects.filter(id=product_id).exists():
            raise serializers.ValidationError("Product does not exist")
        return data
