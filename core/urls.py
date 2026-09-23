from django.urls import path
from . import views
from marketplace import views as marketplace_views


app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('browse/', views.BrowseView.as_view(), name='browse'),
    path('listing/<slug:slug>/', views.ListingDetailView.as_view(), name='listing_detail'),
    path('listing/<slug:slug>/mark-sold/', views.mark_as_sold, name='mark_as_sold'),
    path('seller/<str:username>/', views.seller_profile, name='seller_profile'),
    path('hostels/', marketplace_views.browse_hostels, name='hostel_list'),
    path('hostels/<slug:slug>/', marketplace_views.hostel_detail, name='hostel_detail'),
    path('quick-sale/', marketplace_views.quick_sale_list, name='quick_sale_list'),
]
