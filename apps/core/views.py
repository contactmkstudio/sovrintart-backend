from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from apps.core.models import FAQ, Announcement, BannerImages
import json
import base64
from .serializer import ContactEmailSerializer, FAQSerializer, AnnouncementSerializer
import os
from django.core.mail import send_mail
from django.conf import settings as django_settings
from apps.products.models import Product
from apps.orders.models import Order
from apps.accounts.models import User


@method_decorator(csrf_exempt, name='dispatch')
class UploadBannerImages(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            images = data.get('images', [])

            if not images or not isinstance(images, list):
                return JsonResponse({"error": "Provide 'images' as a list of objects with an 'image' key"}, status=400)

            if len(images) > 5:
                return JsonResponse({"error": "Maximum 5 images allowed"}, status=400)

            image_data = {}
            for i, item in enumerate(images, start=1):
                image_value = item.get('image', '').strip()
                if image_value:
                    image_data[f'image_{i}'] = image_value

            if not image_data:
                return JsonResponse({"error": "No valid images provided"}, status=400)

            banner = BannerImages.objects.create(**image_data)

            return JsonResponse({
                "message": "Images uploaded successfully",
                "id": banner.pk,
                "data": image_data
            }, status=201)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            print(f"Exception: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    def get(self, request):
        try:
            banner = BannerImages.objects.last()
            if not banner:
                return JsonResponse({"message": "No banner images found"}, status=404)
            images = [
                {"image": getattr(banner, f"image_{i}")}
                for i in range(1, 6)
                if getattr(banner, f"image_{i}")
            ]
            return JsonResponse({"message": "Banner images retrieved", "data": {"id": banner.pk, "images": images}}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


# Create your views here.
@method_decorator(csrf_exempt, name='dispatch')
class DashboardStatsView(View):
    def get(self, request):
        try:
            stats = {
                "total_products": Product.objects.count(),
                "orders": {
                    "paid": Order.objects.filter(status='paid').count(),
                    "pending": Order.objects.filter(status='pending').count(),
                    "failed": Order.objects.filter(status='failed').count(),
                },
                "total_users": User.objects.count(),
                "logged_in_users": User.objects.filter(last_login__isnull=False).count(),
            }
            return JsonResponse({"message": "Stats retrieved successfully", "data": stats}, status=200)
        except Exception as e:
            print(f"Exception: {e}")
            return JsonResponse({"error": str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AnnouncementView(View):
    def get(self, request):
        try:
            announcement = Announcement.objects.filter(is_active=True).last()
            if not announcement:
                return JsonResponse({"message": "No active announcement"}, status=404)
            serializer = AnnouncementSerializer(announcement)
            return JsonResponse({"data": serializer.data}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def post(self, request):
        try:
            data = json.loads(request.body)
            serializer = AnnouncementSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({"message": "Announcement created", "data": serializer.data}, status=201)
            return JsonResponse(serializer.errors, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class FAQListView(View):

    # Get FAQs API
    def get(self, request):
        try:
            faqs = FAQ.objects.all()
            if not faqs.exists():
                return JsonResponse({"message" : "No FAQs Found"} , status=404)
            serializer = FAQSerializer(faqs, many=True)
            return JsonResponse(serializer.data, safe=False)
        except Exception as e:
            print(f"Error fetching FAQs: {e}")
            return JsonResponse({"error": str(e)}, status=500)

  
    # Create FAQ API
    def post(self, request):
        try:
            data = json.loads(request.body)

            serializer = FAQSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({
                "message": "FAQ created successfully",
                "data": serializer.data
                }, status=201)
            return JsonResponse(serializer.errors, status=400)
        except json.JSONDecodeError as e:
            print(f"JSON Error: {e}")
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            print(f"Error creating FAQ: {e}")
            return JsonResponse({"error": str(e)}, status=400)
        


# send email API        
@method_decorator(csrf_exempt, name='dispatch')
class SendEmailView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            serializer = ContactEmailSerializer(data=data)
            if serializer.is_valid():
                name = serializer.validated_data['name']
                email = serializer.validated_data['email']
                message = serializer.validated_data['message']

                resend_api_key = os.getenv('RESEND_API_KEY')
                send_mail(
                    subject=f"Contact Form - {name}",
                    message=f"Name: {name}\nEmail: {email}\nMessage: {message}",
                    from_email=django_settings.DEFAULT_FROM_EMAIL,
                    recipient_list=["contact.mkstudio@protonmail.com"],
                    fail_silently=False,
                )
                return JsonResponse({"message": "Email sent successfully"}, status=200)
            return JsonResponse(serializer.errors, status=400)
        except json.JSONDecodeError as e:
            print(f"JSON Error: {e}")
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            print(f"Error sending email: {e}")
            return JsonResponse({"error": str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class FAQDeleteView(View):
    def delete(self, request, faq_id):
        try:
            faq = FAQ.objects.filter(id=faq_id)
            if not faq.exists():
                return JsonResponse({"message": "FAQ Not Found"}, status=404)
            faq.delete()
            return JsonResponse({"message": "FAQ Deleted Successfully"}, status=200)
        except Exception as e:
            print(f"Error deleting FAQ: {e}")
            return JsonResponse({"error": str(e)}, status=400)
      