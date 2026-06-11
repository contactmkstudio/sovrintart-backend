from rest_framework import serializers


class OrderItemSerializer(serializers.Serializer):
    product_name = serializers.CharField(max_length=255)
    size = serializers.CharField(max_length=100)
    quantity = serializers.IntegerField(min_value=1)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)


class CreateOrderSerializer(serializers.Serializer):
    user_email = serializers.EmailField()
    currency = serializers.ChoiceField(choices=['INR', 'USD'])
    items = OrderItemSerializer(many=True)


class VerifyPaymentSerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField(max_length=255)
    razorpay_payment_id = serializers.CharField(max_length=255)
    razorpay_signature = serializers.CharField(max_length=255)


class CreatePayPalOrderSerializer(serializers.Serializer):
    user_email = serializers.EmailField()
    currency = serializers.ChoiceField(choices=['USD'])
    items = OrderItemSerializer(many=True)
    return_url = serializers.URLField()
    cancel_url = serializers.URLField()


class CapturePayPalOrderSerializer(serializers.Serializer):
    paypal_order_id = serializers.CharField(max_length=255)
