from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Category
from .serializers import CategorySerializer


def _admin_required(request):
    if not request.user.is_authenticated or request.user.role != "admin":
        return Response({"detail": "Admin only."}, status=403)
    return None


class AdminCategoryListCreateView(generics.ListCreateAPIView):
    """GET list all categories (incl. inactive). POST create a new category."""
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Category.objects.all()

    def list(self, request, *args, **kwargs):
        err = _admin_required(request)
        if err:
            return err
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        err = _admin_required(request)
        if err:
            return err
        return super().create(request, *args, **kwargs)


class AdminCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET / PATCH / DELETE a single category."""
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    queryset = Category.objects.all()

    def retrieve(self, request, *args, **kwargs):
        err = _admin_required(request)
        if err:
            return err
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        err = _admin_required(request)
        if err:
            return err
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        err = _admin_required(request)
        if err:
            return err
        category = self.get_object()
        if category.products.exists():
            return Response(
                {"detail": "Cannot delete a category that has products. Deactivate it instead."},
                status=status.HTTP_409_CONFLICT,
            )
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
