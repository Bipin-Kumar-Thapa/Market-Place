from django.urls import path
from . import views


urlpatterns = [
    path('login/', views.user_login, name='user_login'),
    path('register/', views.user_register, name='user_register'),
    path('logout/', views.user_logout, name='user_logout'),
    
    path('activate/<uidb64>/<token>/', views.account_activate, name="account_activate"),
    
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path("my-products/", views.my_products, name="my_products"),
    path("product/<int:product_id>/edit/", views.edit_product, name="edit_product"),
    path("product/<int:product_id>/delete/", views.delete_product, name="delete_product"),
    path("add-product/", views.add_product, name="add_product"),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('change-password/', views.change_password, name='change_password'),
]
