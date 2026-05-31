from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from apps.core.models import FAQ
import json
from .serializer import ContactEmailSerializer, FAQSerializer

from django.core.mail import send_mail
from django.conf import settings


# Create your views here.
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

                send_mail(
                    subject=f"Contact Form - {name}",
                    message=f"""
                    Name: {name}
                    Email: {email}
                    Message:{message}
                    """,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[settings.EMAIL_HOST_USER],
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
      