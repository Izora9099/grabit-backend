from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class MarkAllReadView(APIView):
    def post(self, request):
        Notification.objects.filter(user=request.user, read=False).update(read=True)
        return Response({"detail": "All notifications marked as read."})


class NotificationDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
