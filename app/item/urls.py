from django.urls import path
from .views import ItemListCreateAPIView, ItemRetriveUpdateDestroyAPIView

app_name = 'item'
urlpatterns = [
    path('', ItemListCreateAPIView.as_view()),
    path('<int:pk>/', ItemRetriveUpdateDestroyAPIView.as_view()),
]
