from django.urls import path
from . import views

urlpatterns = [
    path('place_order/', views.place_order, name="place_order"),
    # path('payments/', views.payments, name="payments"),
    path('esewa/start/<int:order_id>/', views.esewa_start, name="esewa_start"),
    path('esewa/return/<int:order_id>/', views.esewa_return, name="esewa_return"),
    path('order_complete/', views.order_complete, name="order_complete"),

]
