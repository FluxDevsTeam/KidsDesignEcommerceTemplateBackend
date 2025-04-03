from django.urls import path, include


urlpatterns = [
    path('cart/', include('apps.cart.urls')),
    path('orders/', include(('apps.orders.urls', 'orders'), namespace='orders')),
    # path('payment/', include(('apps.payment.urls', 'payment'), namespace='payment')),
    path('product/', include('apps.products.urls')),
    path('wishlist/', include('apps.wishlist.urls')),
]
