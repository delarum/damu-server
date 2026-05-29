from rest_framework import serializers
from .models import HospitalProfile

class HospitalProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = HospitalProfile
        fields = '__all__'