from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import DonorProfile
from .serializers import DonorProfileSerializer

class DonorProfileViewSet(viewsets.ModelViewSet):
    queryset = DonorProfile.objects.all()
    serializer_class = DonorProfileSerializer
    permission_classes = [IsAuthenticated]