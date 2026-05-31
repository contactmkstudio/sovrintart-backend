from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from apps.core.models import FAQ
import json
from .serializer import ContactEmailSerializer, FAQSerializer
import os
import resend


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

                resend_api_key = os.getenv('RESEND_API_KEY')
                resend.api_key = resend_api_key
                response = resend.Emails.send(
                    {
                        "from": "onboarding@resend.dev",
                        "to": ["contact.mkstudio@protonmail.com"],
                        "subject": f"Contact Form - {name}",
                        "text": f"Name: {name}\nEmail: {email}\nMessage: {message}"
                    }
                )
                if response.get('error'):
                    return JsonResponse({"error": response['error']}, status=400)
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
      