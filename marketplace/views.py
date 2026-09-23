from django.shortcuts import render

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages as django_messages
from .models import Listing
from messaging.models import Conversation
from django.utils import timezone



@login_required
def mark_as_sold(request, slug):
    listing = get_object_or_404(Listing, slug=slug)

    if request.user != listing.seller:
        django_messages.error(request, "You can only mark your own listings as sold.")
        return redirect('core:listing_detail', slug=listing.slug)

    if request.method == 'POST':
        listing.status = Listing.Status.SOLD
        listing.sold_at = timezone.now()
        listing.save(update_fields=['status', 'sold_at'])

        Conversation.objects.filter(listing=listing).delete()

        django_messages.success(request, f"'{listing.title}' marked as sold.")
        return redirect('core:listing_detail', slug=listing.slug)

    return redirect('core:listing_detail', slug=listing.slug)



from .models import Hostel


def browse_hostels(request):
    hostels = Hostel.objects.filter(is_active=True, status=Hostel.Status.ACTIVE)

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if min_price:
        hostels = hostels.filter(price__gte=min_price)
    if max_price:
        hostels = hostels.filter(price__lte=max_price)

    return render(request, 'marketplace/hostel_list.html', {
        'hostels': hostels,
        'min_price': min_price,
        'max_price': max_price,
    })


def hostel_detail(request, slug):
    hostel = get_object_or_404(Hostel, slug=slug, is_active=True, status=Hostel.Status.ACTIVE)
    return render(request, 'marketplace/hostel_detail.html', {
        'hostel': hostel,
    })
# this is for the quick sale

def quick_sale_list(request):
    listings = Listing.objects.filter(
        is_quick_sale=True,
        status=Listing.Status.ACTIVE,
        quick_sale_expires_at__gt=timezone.now()
    ).order_by('-created_at')

    return render(request, 'marketplace/quick_sale_list.html', {
        'listings': listings,
    })
