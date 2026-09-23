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



from .models import Hostel, Community


from django.db.models import Q

def browse_hostels(request):
    base_queryset = Hostel.objects.filter(is_active=True, status=Hostel.Status.ACTIVE)
    hostels = base_queryset

    # 1. Search Query
    q = request.GET.get('q', '').strip()
    if q:
        hostels = hostels.filter(Q(name__icontains=q) | Q(location__icontains=q) | Q(description__icontains=q))

    # 2. Rental Category filter
    rental_type = request.GET.get('rental_type', 'all')
    if rental_type and rental_type != 'all':
        hostels = hostels.filter(rental_type=rental_type)

    # 3. Billing Cycle filter
    billing_cycle = request.GET.get('billing_cycle', 'all')
    if billing_cycle and billing_cycle != 'all':
        hostels = hostels.filter(billing_cycle=billing_cycle)

    # 4. Community / Hub Scope Filter
    comm_param = request.GET.get('community')
    scope_param = request.GET.get('scope')

    if comm_param == 'all' or scope_param == 'all':
        pass  # Nationwide
    elif comm_param:
        hostels = hostels.filter(community__slug=comm_param)
    else:
        session = getattr(request, 'session', {})
        session_scope = session.get('community_scope', 'community') if hasattr(session, 'get') else 'community'
        if session_scope == 'community':
            comm_slug = session.get('community_slug') if hasattr(session, 'get') else None
            active_comm = None
            if comm_slug:
                active_comm = Community.objects.filter(slug=comm_slug, is_active=True).first()
            if not active_comm:
                active_comm = Community.objects.filter(slug='bugema-university', is_active=True).first() or Community.objects.first()
            if active_comm:
                hostels = hostels.filter(community=active_comm)

    # 5. Price Filters
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if min_price:
        try:
            hostels = hostels.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            hostels = hostels.filter(price__lte=float(max_price))
        except ValueError:
            pass

    # 6. Universal Amenity Filters
    if request.GET.get('self_contained') == '1':
        hostels = hostels.filter(is_self_contained=True)
    if request.GET.get('yaka') == '1':
        hostels = hostels.filter(has_yaka_meter=True)
    if request.GET.get('water') == '1':
        hostels = hostels.filter(has_water_reserve=True)
    if request.GET.get('security') == '1':
        hostels = hostels.filter(has_security=True)
    if request.GET.get('parking') == '1':
        hostels = hostels.filter(has_parking=True)

    # Category counts for tabs
    rental_counts = {
        'all': base_queryset.count(),
        'HOSTEL': base_queryset.filter(rental_type=Hostel.RentalType.HOSTEL).count(),
        'BEDSITTER': base_queryset.filter(rental_type=Hostel.RentalType.BEDSITTER).count(),
        'RESIDENTIAL': base_queryset.filter(rental_type=Hostel.RentalType.RESIDENTIAL).count(),
        'COMMERCIAL': base_queryset.filter(rental_type=Hostel.RentalType.COMMERCIAL).count(),
    }

    return render(request, 'marketplace/hostel_list.html', {
        'hostels': hostels,
        'q': q,
        'rental_type': rental_type,
        'billing_cycle': billing_cycle,
        'min_price': min_price,
        'max_price': max_price,
        'rental_counts': rental_counts,
        'selected_self_contained': request.GET.get('self_contained') == '1',
        'selected_yaka': request.GET.get('yaka') == '1',
        'selected_water': request.GET.get('water') == '1',
        'selected_security': request.GET.get('security') == '1',
        'selected_parking': request.GET.get('parking') == '1',
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
