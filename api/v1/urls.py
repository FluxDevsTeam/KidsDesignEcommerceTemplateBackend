from django.urls import path, include


urlpatterns = [
    path('admin/', include('apps.ecommerce_admin.urls')),
    path('blog/', include('apps.blog.urls')),
    path('cart/', include('apps.cart.urls')),
    path('consultation/', include('apps.consultation.urls')),
    path('newsletter/', include('apps.newsletter.urls')),
    path('orders/', include(('apps.orders.urls', 'orders'), namespace='orders')),
    path('packages/', include('apps.packages.urls')),
    path('past_projects/', include('apps.past_projects.urls')),
    path('payment/', include(('apps.payment.urls', 'payment'), namespace='payment')),
    path('product/', include('apps.products.urls')),
    path('wishlist/', include('apps.wishlist.urls')),
]
