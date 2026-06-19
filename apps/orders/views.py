
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.conf import settings
from decimal import Decimal
import json
import os
import razorpay
import requests as http_requests
from django.conf import settings as django_settings
import logging
from apps.orders.tasks import send_order_confirmation_email_task

logger = logging.getLogger(__name__)


def send_order_confirmation_email(order):
    """
    Trigger async email sending task.
    This function is now deprecated - use send_order_confirmation_email_task.delay() instead.
    """
    logger.info(f"Queuing async email task for order #{order.id}")
    send_order_confirmation_email_task.delay(order.id)
    return 'pending'


# The actual async implementation is in apps/orders/tasks.py

from apps.orders.serializer import (
    CreateOrderSerializer, VerifyPaymentSerializer,
    CreatePayPalOrderSerializer, CapturePayPalOrderSerializer,
)
from apps.orders.models import Order, OrderItem
from apps.accounts.models import User
from apps.products.models import Product
from apps.orders import paypal_client

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


@method_decorator(csrf_exempt, name='dispatch')
class CreateOrderView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            serializer = CreateOrderSerializer(data=data)

            if serializer.is_valid():
                user_email = serializer.validated_data['user_email']
                user = User.objects.get(email=user_email)
                items_data = serializer.validated_data['items']

                # Calculate total price
                total_price = sum(
                    Decimal(str(item['price'])) * item['quantity']
                    for item in items_data
                )

                order = Order.objects.create(
                    user=user,
                    currency=serializer.validated_data['currency'],
                    total_price=total_price,
                    payment_gateway='razorpay',
                )

                # Create order items
                order_items = []
                for item in items_data:
                    order_item = OrderItem.objects.create(
                        order=order,
                        product_name=item['product_name'],
                        size=item['size'],
                        quantity=item['quantity'],
                        price=item['price'],
                    )
                    order_items.append({
                        "product_name": order_item.product_name,
                        "size": order_item.size,
                        "quantity": order_item.quantity,
                        "price": str(order_item.price),
                    })

                # Create Razorpay order (amount in paise/cents)
                razorpay_amount = int(total_price * 100)
                razorpay_order = razorpay_client.order.create({
                    "amount": razorpay_amount,
                    "currency": order.currency,
                    "receipt": f"order_{order.id}",
                })

                # Store razorpay order id
                order.razorpay_order_id = razorpay_order["id"]
                order.save()

                return JsonResponse({
                    "message": "Order created successfully",
                    "data": {
                        "order_id": order.id,
                        "total_price": str(order.total_price),
                        "currency": order.currency,
                        "status": order.status,
                        "items": order_items,
                        "razorpay_order_id": razorpay_order["id"],
                        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
                        "created_at": order.created_at.isoformat(),
                    }
                }, status=201)

            return JsonResponse({"errors": serializer.errors}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)


@method_decorator(csrf_exempt, name='dispatch')
class VerifyPaymentView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            serializer = VerifyPaymentSerializer(data=data)

            if serializer.is_valid():
                razorpay_order_id = serializer.validated_data['razorpay_order_id']
                razorpay_payment_id = serializer.validated_data['razorpay_payment_id']
                razorpay_signature = serializer.validated_data['razorpay_signature']

                # Verify signature
                razorpay_client.utility.verify_payment_signature({
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': razorpay_signature,
                })

                # Signature valid — mark order as paid
                order = Order.objects.get(razorpay_order_id=razorpay_order_id)
                order.status = 'paid'
                order.razorpay_payment_id = razorpay_payment_id
                order.razorpay_signature = razorpay_signature
                order.save()

                # Queue async email task
                send_order_confirmation_email_task.delay(order.id)
                logger.info(f"Email task queued for order #{order.id}")

                return JsonResponse({
                    "message": "Payment verified successfully",
                    "data": {
                        "order_id": order.id,
                        "status": order.status,
                    }
                })

            return JsonResponse({"errors": serializer.errors}, status=400)

        except razorpay.errors.SignatureVerificationError:
            # Signature invalid — mark order as failed
            try:
                order = Order.objects.get(razorpay_order_id=data.get('razorpay_order_id'))
                order.status = 'failed'
                order.save()
            except Order.DoesNotExist:
                pass
            return JsonResponse({"error": "Payment verification failed"}, status=400)
        except Order.DoesNotExist:
            return JsonResponse({"error": "Order not found"}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class RazorpayWebhookView(View):
    def post(self, request):
        try:
            webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
            webhook_signature = request.headers.get('X-Razorpay-Signature', '')
            webhook_body = request.body.decode('utf-8')

            # Verify webhook signature
            razorpay_client.utility.verify_webhook_signature(
                webhook_body, webhook_signature, webhook_secret
            )

            payload = json.loads(webhook_body)
            event = payload.get('event')

            if event == 'payment.captured':
                payment_entity = payload['payload']['payment']['entity']
                razorpay_order_id = payment_entity.get('order_id')
                razorpay_payment_id = payment_entity.get('id')

                try:
                    order = Order.objects.get(razorpay_order_id=razorpay_order_id)
                    if order.status != 'paid':
                        order.status = 'paid'
                        order.razorpay_payment_id = razorpay_payment_id
                        order.save()
                        # Queue async email task
                        send_order_confirmation_email_task.delay(order.id)
                        logger.info(f"Email task queued for order #{order.id}")
                except Order.DoesNotExist:
                    pass

            elif event == 'payment.failed':
                payment_entity = payload['payload']['payment']['entity']
                razorpay_order_id = payment_entity.get('order_id')

                try:
                    order = Order.objects.get(razorpay_order_id=razorpay_order_id)
                    if order.status == 'pending':
                        order.status = 'failed'
                        order.save()
                except Order.DoesNotExist:
                    pass

            return JsonResponse({"status": "ok"})

        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({"error": "Invalid webhook signature"}, status=400)
        except Exception:
            return JsonResponse({"error": "Webhook processing failed"}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class CreatePayPalOrderView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            serializer = CreatePayPalOrderSerializer(data=data)

            if serializer.is_valid():
                user_email = serializer.validated_data['user_email']
                user = User.objects.get(email=user_email)
                items_data = serializer.validated_data['items']

                total_price = sum(
                    Decimal(str(item['price'])) * item['quantity']
                    for item in items_data
                )

                order = Order.objects.create(
                    user=user,
                    currency=serializer.validated_data['currency'],
                    total_price=total_price,
                    payment_gateway='paypal',
                )

                order_items = []
                for item in items_data:
                    order_item = OrderItem.objects.create(
                        order=order,
                        product_name=item['product_name'],
                        size=item['size'],
                        quantity=item['quantity'],
                        price=item['price'],
                    )
                    order_items.append({
                        "product_name": order_item.product_name,
                        "size": order_item.size,
                        "quantity": order_item.quantity,
                        "price": str(order_item.price),
                    })


                paypal_order = paypal_client.create_order(
                    amount=total_price,
                    currency=order.currency,
                    order_id=order.id,
                    return_url=serializer.validated_data['return_url'],
                    cancel_url=serializer.validated_data['cancel_url'],
                )

                order.paypal_order_id = paypal_order['id']
                order.save()

                approval_url = next(
                    (link['href'] for link in paypal_order.get('links', []) if link['rel'] == 'approve'),
                    None
                )

                return JsonResponse({
                    "message": "PayPal order created successfully",
                    "data": {
                        "order_id": order.id,
                        "total_price": str(order.total_price),
                        "currency": order.currency,
                        "status": order.status,
                        "items": order_items,
                        "paypal_order_id": paypal_order['id'],
                        "approval_url": approval_url,
                        "created_at": order.created_at.isoformat(),
                    }
                }, status=201)

            return JsonResponse({"errors": serializer.errors}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except http_requests.HTTPError as e:
            return JsonResponse({"error": f"PayPal error: {e.response.text}"}, status=502)


@method_decorator(csrf_exempt, name='dispatch')
class CapturePayPalOrderView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            serializer = CapturePayPalOrderSerializer(data=data)

            if serializer.is_valid():
                paypal_order_id = serializer.validated_data['paypal_order_id']

                capture = paypal_client.capture_order(paypal_order_id)

                if capture.get('status') != 'COMPLETED':
                    return JsonResponse({"error": "Payment not completed"}, status=400)

                capture_id = capture['purchase_units'][0]['payments']['captures'][0]['id']

                order = Order.objects.get(paypal_order_id=paypal_order_id)
                order.status = 'paid'
                order.paypal_payment_id = capture_id
                order.save()

                # Queue async email task
                send_order_confirmation_email_task.delay(order.id)
                logger.info(f"Email task queued for order #{order.id}")

                return JsonResponse({
                    "message": "Payment captured successfully",
                    "data": {
                        "order_id": order.id,
                        "status": order.status,
                        "paypal_payment_id": capture_id,
                    }
                })

            return JsonResponse({"errors": serializer.errors}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Order.DoesNotExist:
            return JsonResponse({"error": "Order not found"}, status=404)
        except http_requests.HTTPError as e:
            return JsonResponse({"error": f"PayPal error: {e.response.text}"}, status=502)


@method_decorator(csrf_exempt, name='dispatch')
class GetOrdersView(View):
    def get(self, request):
        user_email = request.GET.get('user_email')

        if not user_email:
            return JsonResponse({"error": "user_email query param is required"}, status=400)

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)

        orders = Order.objects.filter(user=user).order_by('-created_at')

        data = []
        for order in orders:
            items = []
            for item in order.items.all():
                product = Product.objects.filter(name=item.product_name).first()
                items.append({
                    "product_name": item.product_name,
                    "size": item.size,
                    "quantity": item.quantity,
                    "price": str(item.price),
                    "image": product.image if product else None,
                })
            data.append({
                "order_id": order.id,
                "total_price": str(order.total_price),
                "currency": order.currency,
                "status": order.status,
                "payment_gateway": order.payment_gateway,
                "emailsent": order.emailsent,
                "items": items,
                "created_at": order.created_at.isoformat(),
            })

        return JsonResponse({"orders": data})



class GetPaidOrdersView(View):
    def get(self, request):
        try:
            orders = Order.objects.filter(status='paid').order_by('-created_at')
        except Order.DoesNotExist:
            return JsonResponse({"error": "No paid orders found"}, status=404)

        data = []
        for order in orders:
            items = []
            for item in order.items.all():
                product = Product.objects.filter(name=item.product_name).first()
                items.append({
                    "product_name": item.product_name,
                    "size": item.size,
                    "quantity": item.quantity,
                    "price": str(item.price),
                    "image": product.image if product else None,
                })
            data.append({
                "order_id": order.id,
                "total_price": str(order.total_price),
                "currency": order.currency,
                "status": order.status,
                "payment_gateway": order.payment_gateway,
                "emailsent": order.emailsent,
                "items": items,
                "created_at": order.created_at.isoformat(),
                "email": order.user.email,
            })

        return JsonResponse({"orders": data})