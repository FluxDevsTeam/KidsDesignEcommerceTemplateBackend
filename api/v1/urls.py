from django.urls import path, include


urlpatterns = [
    path('cart/', include(('apps.cart.urls', 'flightapp'), namespace='flightapp')),
    path('orders/', include(('apps.orders.urls', 'route'), namespace='route')),
    path('payment/', include(('apps.payment.urls', 'route'), namespace='route')),
    path('products/', include(('apps.products.urls', 'route'), namespace='route')),
]
