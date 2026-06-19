
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
from django.core.mail import send_mail
from django.conf import settings as django_settings
import logging

logger = logging.getLogger(__name__)


def send_order_confirmation_email(order):
    """
    Send order confirmation emails to customer and seller.
    Returns: 'success' if emails sent successfully, 'failure' if any error occurs
    """
    user_email = order.user.email
    order_id = order.id
    amount = f"{order.total_price:,.2f}"
    currency = order.currency
    items = order.items.all()

    print(f"[EMAIL] Preparing to send order confirmation to: {user_email}")
    try:
        print(f"[EMAIL] Attempting to send order confirmation to: {user_email}")

        # Build item rows for customer email
        item_rows = ""
        item_rows_seller = ""
        for item in items:
            item_rows += f"""
                      <tr>
                        <td style="padding:8px 0;border-bottom:1px solid #d6e5cc;">
                          <span style="color:#2d3a25;font-size:13px;">{item.product_name}</span>
                          <span style="color:#888888;font-size:12px;"> &nbsp;— Size: {item.size} &nbsp;× {item.quantity}</span>
                        </td>
                        <td align="right" style="padding:8px 0;border-bottom:1px solid #d6e5cc;">
                          <span style="color:#546B41;font-size:13px;font-weight:bold;">{currency} {float(item.price * item.quantity):,.2f}</span>
                        </td>
                      </tr>"""
            item_rows_seller += f"\n  • {item.product_name} | Size: {item.size} | Qty: {item.quantity} | {currency} {float(item.price * item.quantity):,.2f}"

        html_message = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Order Confirmation</title>
</head>
<body style="margin:0;padding:0;background-color:#f0f4ed;font-family:'Georgia',serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f0f4ed;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:4px;overflow:hidden;box-shadow:0 2px 12px rgba(84,107,65,0.15);">

          <!-- Header -->
          <tr>
            <td style="background-color:#546B41;padding:36px 40px;text-align:center;">
              <h1 style="margin:0;color:#ffffff;font-family:'Georgia',serif;font-size:28px;letter-spacing:4px;text-transform:uppercase;">MK Atelier</h1>
              <p style="margin:8px 0 0;color:#c8d9bb;font-size:12px;letter-spacing:2px;text-transform:uppercase;">Fine Art &amp; Collectibles</p>
            </td>
          </tr>

          <!-- Success Banner -->
          <tr>
            <td style="background-color:#99AD7A;padding:16px 40px;text-align:center;">
              <p style="margin:0;color:#ffffff;font-size:13px;letter-spacing:2px;text-transform:uppercase;font-weight:bold;">&#10003;&nbsp; Order Confirmed</p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:40px 40px 24px;">
              <p style="margin:0 0 16px;color:#2d3a25;font-size:16px;line-height:1.6;">Dear Valued Customer,</p>
              <p style="margin:0 0 28px;color:#555555;font-size:15px;line-height:1.8;">
                Thank you for your purchase from <strong style="color:#546B41;">MK Atelier</strong>. Your order has been confirmed and is now being prepared with care.
              </p>

              <!-- Order Details Box -->
              <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f8f1;border-left:3px solid #546B41;border-radius:2px;margin-bottom:28px;">
                <tr>
                  <td style="padding:24px 28px;">
                    <p style="margin:0 0 16px;color:#546B41;font-size:13px;letter-spacing:2px;text-transform:uppercase;font-weight:bold;">Order Summary</p>
                    <table width="100%" cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="padding:8px 0;border-bottom:1px solid #d6e5cc;">
                          <span style="color:#888888;font-size:13px;">Order ID</span>
                        </td>
                        <td align="right" style="padding:8px 0;border-bottom:1px solid #d6e5cc;">
                          <span style="color:#2d3a25;font-size:13px;font-weight:bold;">#{order_id}</span>
                        </td>
                      </tr>
                      {item_rows}
                      <tr>
                        <td style="padding:10px 0;border-top:2px solid #546B41;margin-top:4px;">
                          <span style="color:#2d3a25;font-size:14px;font-weight:bold;">Total Paid</span>
                        </td>
                        <td align="right" style="padding:10px 0;border-top:2px solid #546B41;">
                          <span style="color:#546B41;font-size:16px;font-weight:bold;">{currency} {amount}</span>
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:8px 0;">
                          <span style="color:#888888;font-size:13px;">Payment Status</span>
                        </td>
                        <td align="right" style="padding:8px 0;">
                          <span style="background-color:#99AD7A;color:#ffffff;font-size:12px;padding:3px 12px;border-radius:20px;">Paid</span>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- Delivery Info -->
              <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f8f1;border-radius:2px;margin-bottom:28px;">
                <tr>
                  <td style="padding:24px 28px;">
                    <p style="margin:0 0 14px;color:#546B41;font-size:13px;letter-spacing:2px;text-transform:uppercase;font-weight:bold;">&#128666; Delivery Information</p>
                    <table width="100%" cellpadding="0" cellspacing="0">
                      <tr>
                        <td width="50%" style="padding:6px 12px 6px 0;vertical-align:top;">
                          <p style="margin:0 0 4px;color:#546B41;font-size:12px;letter-spacing:1px;text-transform:uppercase;font-weight:bold;">India</p>
                          <p style="margin:0;color:#555555;font-size:14px;">2 – 3 Business Days</p>
                        </td>
                        <td width="50%" style="padding:6px 0 6px 12px;vertical-align:top;border-left:1px solid #d6e5cc;">
                          <p style="margin:0 0 4px;color:#546B41;font-size:12px;letter-spacing:1px;text-transform:uppercase;font-weight:bold;">International</p>
                          <p style="margin:0;color:#555555;font-size:14px;">2 – 3 Weeks</p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <p style="margin:0 0 28px;color:#555555;font-size:14px;line-height:1.8;">
                We will notify you once your order has been dispatched. For any questions or assistance, feel free to reach out to us directly on WhatsApp.
              </p>

              <!-- WhatsApp CTA -->
              <table cellpadding="0" cellspacing="0" style="margin-bottom:32px;">
                <tr>
                  <td style="background-color:#25d366;border-radius:4px;">
                    <a href="https://wa.link/ma9cum" target="_blank" style="display:inline-block;padding:13px 26px;color:#ffffff;text-decoration:none;font-size:14px;font-weight:bold;letter-spacing:0.5px;">
                      &#128172; Chat with us on WhatsApp
                    </a>
                  </td>
                </tr>
              </table>

            </td>
          </tr>

          <!-- Divider -->
          <tr>
            <td style="padding:0 40px;">
              <hr style="border:none;border-top:1px solid #d6e5cc;margin:0;" />
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:24px 40px;text-align:center;">
              <p style="margin:0 0 8px;color:#546B41;font-size:13px;letter-spacing:2px;text-transform:uppercase;">MK Atelier</p>
              <p style="margin:0 0 8px;color:#888888;font-size:12px;">Fine Art &amp; Collectibles</p>
              <p style="margin:0;color:#aaaaaa;font-size:11px;">
                &copy; 2025 MK Atelier. All rights reserved.<br/>
                <a href="https://mkkatelier.vercel.app" style="color:#546B41;text-decoration:none;">mkkatelier.vercel.app</a>
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
        """

        # Send confirmation to customer
        send_mail(
            subject=f"Your MK Atelier Order #{order_id} is Confirmed!",
            message=f"Thank you for your purchase!\nOrder ID: #{order_id}\nItems:{item_rows_seller}\nTotal Paid: {currency} {amount}\n\nDelivery: 2-3 days (India) | 2-3 weeks (International)\n\nNeed help? Chat with us: https://wa.link/ma9cum",
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"[EMAIL] Order confirmation sent successfully to: {user_email}")
        logger.info(f"Order confirmation sent successfully to: {user_email}")

        # Notify seller
        seller_html = f"""
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"/><title>New Order</title></head>
<body style="margin:0;padding:0;background-color:#f0f4ed;font-family:'Georgia',serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f0f4ed;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:4px;overflow:hidden;box-shadow:0 2px 12px rgba(84,107,65,0.15);">
          <tr>
            <td style="background-color:#546B41;padding:28px 36px;text-align:center;">
              <h1 style="margin:0;color:#ffffff;font-family:'Georgia',serif;font-size:24px;letter-spacing:3px;text-transform:uppercase;">MK Atelier</h1>
              <p style="margin:6px 0 0;color:#c8d9bb;font-size:11px;letter-spacing:2px;text-transform:uppercase;">Seller Notification</p>
            </td>
          </tr>
          <tr>
            <td style="background-color:#99AD7A;padding:14px 36px;text-align:center;">
              <p style="margin:0;color:#ffffff;font-size:13px;letter-spacing:2px;text-transform:uppercase;font-weight:bold;">&#128276;&nbsp; New Order Received!</p>
            </td>
          </tr>
          <tr>
            <td style="padding:32px 36px;">
              <p style="margin:0 0 20px;color:#2d3a25;font-size:15px;line-height:1.7;">You have received a new order. Here are the details:</p>
              <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f8f1;border-left:3px solid #546B41;border-radius:2px;margin-bottom:24px;">
                <tr>
                  <td style="padding:20px 24px;">
                    <p style="margin:0 0 14px;color:#546B41;font-size:12px;letter-spacing:2px;text-transform:uppercase;font-weight:bold;">Order Details</p>
                    <table width="100%" cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="padding:7px 0;border-bottom:1px solid #d6e5cc;"><span style="color:#888888;font-size:13px;">Order ID</span></td>
                        <td align="right" style="padding:7px 0;border-bottom:1px solid #d6e5cc;"><span style="color:#2d3a25;font-size:13px;font-weight:bold;">#{order_id}</span></td>
                      </tr>
                      <tr>
                        <td style="padding:7px 0;border-bottom:1px solid #d6e5cc;"><span style="color:#888888;font-size:13px;">Customer Email</span></td>
                        <td align="right" style="padding:7px 0;border-bottom:1px solid #d6e5cc;"><span style="color:#2d3a25;font-size:13px;">{user_email}</span></td>
                      </tr>
                      {item_rows}
                      <tr>
                        <td style="padding:7px 0;border-top:2px solid #546B41;"><span style="color:#2d3a25;font-size:14px;font-weight:bold;">Total</span></td>
                        <td align="right" style="padding:7px 0;border-top:2px solid #546B41;"><span style="color:#546B41;font-size:15px;font-weight:bold;">{currency} {amount}</span></td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
              <p style="margin:0;color:#555555;font-size:13px;line-height:1.7;">Please process and dispatch this order at the earliest. Log in to your dashboard to view full order details.</p>
            </td>
          </tr>
          <tr>
            <td style="padding:0 36px;"><hr style="border:none;border-top:1px solid #d6e5cc;margin:0;"/></td>
          </tr>
          <tr>
            <td style="padding:20px 36px;text-align:center;">
              <p style="margin:0;color:#aaaaaa;font-size:11px;">&copy; 2025 MK Atelier &nbsp;|&nbsp; <a href="https://mkkatelier.vercel.app" style="color:#546B41;text-decoration:none;">mkkatelier.vercel.app</a></p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
        """
        send_mail(
            subject=f"New Order #{order_id} — {currency} {amount}",
            message=f"New order received!\nOrder ID: #{order_id}\nCustomer: {user_email}\nItems:{item_rows_seller}\nTotal: {currency} {amount}",
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            recipient_list=['contact.mkstudio@protonmail.com'],
            html_message=seller_html,
            fail_silently=False,
        )
        print(f"[EMAIL] Seller notification sent for order #{order_id}")
        logger.info(f"Seller notification sent for order #{order_id}")
        return 'success'
    except Exception as e:
        error_msg = f"Failed to send order confirmation email to {user_email}: {str(e)}"
        print(f"[EMAIL] {error_msg}")
        logger.error(error_msg, exc_info=True)
        return 'failure'

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

                email_status = send_order_confirmation_email(order)
                order.emailsent = email_status
                order.save()

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
                        email_status = send_order_confirmation_email(order)
                        order.emailsent = email_status
                        order.save()
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

                email_status = send_order_confirmation_email(order)
                order.emailsent = email_status
                order.save()

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