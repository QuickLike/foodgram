from django.contrib import admin
from django.urls import path, include

from api.views import ReceiptShortLinkView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<int:receipt_id>/', ReceiptShortLinkView.as_view(),
         name='receipt-short-link'),
]
