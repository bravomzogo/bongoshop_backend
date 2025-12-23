# accounts/views.py
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from .models import User
# IMPORT ALL SERIALIZERS
from .serializers import RegisterSerializer, UserSerializer, UserUpdateSerializer, LoginSerializer
from .utils import generate_code, send_verification_email, send_support_email

CODE_TTL = 60 * 15  # 15 minutes


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        code = generate_code()
        cache.set(f'verify_code_{user.email}', code, CODE_TTL)
        send_verification_email(user.email, code)

    def create(self, request, *args, **kwargs):
        # Handle FormData for file uploads
        if request.content_type.startswith('multipart/form-data'):
            # Extract data from FormData
            data = request.POST.copy()
            files = request.FILES
        else:
            data = request.data
            files = None
        
        # Merge files into data
        if files and 'profile_picture' in files:
            data['profile_picture'] = files['profile_picture']
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response({
            'detail': 'User created. Verification code sent to email.',
            'email': serializer.validated_data['email']
        }, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        
        if not email or not code:
            return Response({'detail': 'email and code required'}, status=400)

        stored = cache.get(f'verify_code_{email}')
        if stored and stored == code:
            user = get_object_or_404(User, email=email)
            user.is_email_verified = True
            user.save()
            cache.delete(f'verify_code_{email}')
            return Response({'detail': 'Email verified successfully'})

        return Response({'detail': 'Invalid or expired code'}, status=400)


class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({'detail': 'Email and password required'}, status=400)
        
        user = authenticate(request, email=email, password=password)

        if user:
            if not user.is_email_verified:
                return Response({'detail': 'Email not verified. Please verify your email first.'}, status=403)
            
            refresh = RefreshToken.for_user(user)
            
            # Get full profile picture URL
            user_data = UserSerializer(user).data
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': user_data
            })

        return Response({'detail': 'Invalid credentials'}, status=401)


class PasswordResetRequestView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'detail': 'Email is required'}, status=400)

        try:
            user = User.objects.get(email=email)
            code = generate_code()
            cache.set(f'pwreset_{email}', code, CODE_TTL)
            send_verification_email(email, code)
        except User.DoesNotExist:
            pass  # Don't reveal if email exists
        
        return Response({'detail': 'If that email exists, we sent reset instructions.'})


class PasswordResetConfirmView(APIView):
    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        new_password = request.data.get('new_password')

        if not (email and code and new_password):
            return Response({'detail': 'Email, code and new_password required'}, status=400)

        stored = cache.get(f'pwreset_{email}')
        if stored and stored == code:
            try:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                cache.delete(f'pwreset_{email}')
                return Response({'detail': 'Password reset successful'})
            except User.DoesNotExist:
                pass

        return Response({'detail': 'Invalid or expired code'}, status=400)


class SupportContactView(APIView):
    def post(self, request):
        name = request.data.get('name', '')
        phone = request.data.get('phone', '')
        message = request.data.get('message', '')

        if not message:
            return Response({'detail': 'Message is required'}, status=400)

        subj = f'Support request from {name or phone or "anonymous"}'
        body = f'Phone: {phone}\nName: {name}\nMessage:\n{message}'
        send_support_email(subj, body)

        return Response({'detail': 'Support request received. Our team will contact you.'})


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        user = request.user
        
        # Handle file upload separately
        if request.content_type.startswith('multipart/form-data'):
            data = request.POST.copy()
            files = request.FILES
        else:
            data = request.data
            files = None
        
        # Merge files into data
        if files and 'profile_picture' in files:
            data['profile_picture'] = files['profile_picture']
        
        # Use UserUpdateSerializer for profile updates
        serializer = UserUpdateSerializer(user, data=data, partial=True)
        
        if serializer.is_valid():
            try:
                serializer.save()
                # Return updated user data
                updated_user = UserSerializer(user).data
                return Response({
                    'detail': 'Profile updated successfully',
                    'user': updated_user
                })
            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserSettingsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        user = request.user
        
        # Handle file upload separately
        if request.content_type.startswith('multipart/form-data'):
            data = request.POST.copy()
            files = request.FILES
        else:
            data = request.data
            files = None
        
        # Merge files into data
        if files and 'profile_picture' in files:
            data['profile_picture'] = files['profile_picture']
        
        serializer = UserUpdateSerializer(user, data=data, partial=True)
        
        if serializer.is_valid():
            try:
                serializer.save()
                # Return updated user data
                updated_user = UserSerializer(user).data
                return Response({
                    'detail': 'Profile updated successfully',
                    'user': updated_user
                })
            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)