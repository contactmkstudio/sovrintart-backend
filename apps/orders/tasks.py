from celery import shared_task
from django.conf import settings as django_settings
import logging
import os
import requests as http_requests

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_order_confirmation_email_task(self, order_id):
    """
    Async task to send order confirmation emails.
    Retries up to 3 times on failure with exponential backoff.
    """
    from apps.orders.models import Order
    
    try:
        order = Order.objects.get(id=order_id)
        user_email = order.user.email
        amount = f"{order.total_price:,.2f}"
        currency = order.currency
        items = order.items.all()

        logger.info(f"[ASYNC-EMAIL] Starting to send order confirmation for order #{order_id}")

        # Build item rows
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

        # Customer email HTML
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

        # Send to customer
        brevo_response = http_requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers={
                'api-key': os.getenv('BREVO_API_KEY'),
                'Content-Type': 'application/json',
            },
            json={
                'sender': {'name': 'MK Atelier', 'email': 'sovrinart@gmail.com'},
                'to': [{'email': user_email}],
                'subject': f'Your MK Atelier Order #{order_id} is Confirmed!',
                'htmlContent': html_message,
            },
            timeout=15,
        )
        brevo_response.raise_for_status()
        logger.info(f"[ASYNC-EMAIL] Customer email sent to {user_email}")

        # Seller notification HTML
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

        # Send to seller
        brevo_seller = http_requests.post(
            'https://api.brevo.com/v3/smtp/email',
            headers={
                'api-key': os.getenv('BREVO_API_KEY'),
                'Content-Type': 'application/json',
            },
            json={
                'sender': {'name': 'MK Atelier', 'email': 'sovrinart@gmail.com'},
                'to': [{'email': 'contact.mkstudio@protonmail.com'}],
                'subject': f'New Order #{order_id} — {currency} {amount}',
                'htmlContent': seller_html,
            },
            timeout=15,
        )
        brevo_seller.raise_for_status()
        logger.info(f"[ASYNC-EMAIL] Seller notification sent for order #{order_id}")

        # Update order status
        order.emailsent = 'success'
        order.save()
        logger.info(f"[ASYNC-EMAIL] Order #{order_id} marked as email sent successfully")
        return f"Emails sent successfully for order {order_id}"

    except Order.DoesNotExist:
        error_msg = f"Order {order_id} not found"
        logger.error(f"[ASYNC-EMAIL] {error_msg}")
        return error_msg

    except Exception as exc:
        error_msg = f"Failed to send emails for order {order_id}: {str(exc)}"
        logger.error(f"[ASYNC-EMAIL] {error_msg}", exc_info=True)
        
        # Update order status to failure
        try:
            order = Order.objects.get(id=order_id)
            order.emailsent = 'failure'
            order.save()
        except:
            pass
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
