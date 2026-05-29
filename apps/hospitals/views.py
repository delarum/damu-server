from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import HospitalProfile
from .serializers import HospitalProfileSerializer

class HospitalProfileViewSet(viewsets.ModelViewSet):
    queryset = HospitalProfile.objects.all()
    serializer_class = HospitalProfileSerializer
    permission_classes = [IsAuthenticated]