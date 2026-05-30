from django.http import JsonResponse
from django.views import View
import json
from .serializer import LoginSerializer, UserSerializer
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(View):
    def post(self , request):
        try:
            data = json.loads(request.body)
            serializer = UserSerializer(data=data)
            
            if serializer.is_valid():
                serializer.save()
                return JsonResponse({
                    "message": "User registered successfully",
                    "data": serializer.data,
                    "status": 201
                }, status=201)
            return JsonResponse(serializer.errors, status=400)
        except json.JSONDecodeError as e:
            print(f"JSON Error: {e}")
            return JsonResponse({"error": "Invalid JSON"}, status=400)      
        except Exception as e:
            print(f"Error registering user: {e}")
            return JsonResponse({"error": str(e)}, status=400)
        
@method_decorator(csrf_exempt, name='dispatch')
class LoginView(View):
    def post(self , request):
        try:
            data = json.loads(request.body)
            serializer = LoginSerializer(data=data)
            if serializer.is_valid():
                serializer.validated_data["user"]
                return JsonResponse({
                    "message": "Login successful",
                    "data": serializer.data,
                    "status": 200
                }, status=200)
        except json.JSONDecodeError as e:   
            print(f"JSON Error: {e}")
            return JsonResponse({"error": "Invalid JSON"}, status=400)  
        except Exception as e:
            print(f"Error during login: {e}")
            return JsonResponse({"error": str(e)}, status=400)      
        

# @method_decorator(csrf_exempt, name='dispatch')
# class ForgotPasswordViews(View):
#     def post(self , request):
