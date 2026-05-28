from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from apps.core.models import FAQ
import json

# Create your views here.
@method_decorator(csrf_exempt, name='dispatch')
class FAQListView(View):
    def get(self, request):
        faqs = FAQ.objects.all()
        data = [
            {
                "id": faq.id,
                "question": faq.question,
                "answer": faq.answer,
                "created_at": faq.created_at.isoformat()
            }
            for faq in faqs
        ]
        return JsonResponse(data , safe=False)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            print("Received data:", data)
            
            # Create FAQ
            faq = FAQ.objects.create(
                question=data.get('question'),
                answer=data.get('answer')
            )
            
            return JsonResponse({
                "message": "FAQ created successfully",
                "id": faq.id,
                "question": faq.question,
                "answer": faq.answer
            }, status=201)
        except json.JSONDecodeError as e:
            print(f"JSON Error: {e}")
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            print(f"Error creating FAQ: {e}")
            return JsonResponse({"error": str(e)}, status=400)