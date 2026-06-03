from rest_framework import serializers
from .models import Product, ProductSize, ProductImage, ProductDetail


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ['size', 'price_rs', 'price_usd']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image']


class ProductDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductDetail
        fields = ['detail']


class ProductSerializer(serializers.ModelSerializer):
    sizes = ProductSizeSerializer(many=True, write_only=True, required=False)
    other_images = ProductImageSerializer(many=True, write_only=True, required=False)
    details = ProductDetailSerializer(many=True, write_only=True, required=False)
    
    # For reading (GET)
    sizes_read = ProductSizeSerializer(source='sizes', many=True, read_only=True)
    other_images_read = ProductImageSerializer(source='other_images', many=True, read_only=True)
    details_read = ProductDetailSerializer(source='details', many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price_rs', 'price_usd', 'image', 'details', 'details_read', 'sizes', 'sizes_read', 'other_images', 'other_images_read', 'created_at', 'updated_at']

    def create(self, validated_data):
        sizes_data = validated_data.pop('sizes', [])
        details_data = validated_data.pop('details', [])
        images_data = validated_data.pop('other_images', [])
        
        # Create product
        product = Product.objects.create(**validated_data)
        
        # Create sizes
        for size in sizes_data:
            ProductSize.objects.create(product=product, **size)
        
        # Create details
        for detail in details_data:
            ProductDetail.objects.create(product=product, **detail)
        
        # Create images
        for image in images_data:
            ProductImage.objects.create(product=product, **image)
        
        return product