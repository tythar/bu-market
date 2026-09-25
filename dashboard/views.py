from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from subscriptions.models import SellerSubscription, SubscriptionPlan
from accounts.models import User
from marketplace.models import Listing, Category, Hostel, HostelImage
from datetime import timedelta
from marketplace.forms import ListingForm, HostelForm, QuickSaleForm


# Role verification decorators
def role_required(allowed_roles):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            if request.user.is_superuser or request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("You do not have permission to access this page.")
        return _wrapped_view
    return decorator

@login_required
def dashboard_home(request):
    user = request.user
    if user.is_superuser or user.role == User.Role.ADMIN:
        return redirect('dashboard:admin_dashboard')
    elif user.role == User.Role.ACCOUNTANT:
        return redirect('dashboard:accountant_dashboard')
    elif user.role == User.Role.MODERATOR:
        return redirect('dashboard:moderator_dashboard')
    elif user.role == User.Role.SELLER:
        return redirect('dashboard:seller_dashboard')
    elif user.role == User.Role.BUYER:
        # Buyers don't have a dashboard — redirect to marketplace home
        return redirect('core:home')
    return redirect('core:home')


@login_required
@role_required([User.Role.SELLER])
def seller_dashboard(request):
    user = request.user
    listings = Listing.objects.filter(seller=user).order_by('-created_at')
    
    # Calculate counts and sums
    from django.db.models import Sum
    active_listings_count = listings.filter(status=Listing.Status.ACTIVE).count()
    total_views = listings.aggregate(Sum('views_count'))['views_count__sum'] or 0
    
    # Active subscription check
    active_sub = user.active_subscription
    
    # Subscription history
    history = SellerSubscription.objects.filter(seller=user).order_by('-submitted_at')
    
    context = {
        'listings': listings,
        'active_listings_count': active_listings_count,
        'total_views': total_views,
        'active_sub': active_sub,
        'history': history,
        'plans': SubscriptionPlan.objects.all(),
    }
    return render(request, 'dashboard/seller_dashboard.html', context)



@login_required
@role_required([User.Role.SELLER])
def seller_listings(request):
    listings = Listing.objects.filter(seller=request.user).order_by('-created_at')
    return render(request, 'dashboard/seller_listings.html', {'listings': listings})


@login_required
@role_required([User.Role.SELLER])
def create_listing(request):
    # Quick pre-check for active subscription
    if not request.user.has_active_subscription:
        messages.error(request, "You must have an active approved subscription to post listings.")
        return redirect('dashboard:seller_dashboard')

    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.seller = request.user
            messages.success(request, f'Listing "{listing.title}" created successfully and is now live!')
            return redirect('dashboard:seller_listings')
    else:
        form = ListingForm(user=request.user)
    
    return render(request, 'dashboard/listing_form.html', {'form': form, 'title': 'Create Listing'})

@login_required
@role_required([User.Role.SELLER])
def create_hostel(request):
    if not request.user.has_active_subscription:
        messages.error(request, "You must have an active approved subscription to post a hostel.")
        return redirect('dashboard:seller_dashboard')

    if request.method == 'POST':
        form = HostelForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            hostel = form.save(commit=False)
            hostel.owner = request.user
            hostel.save()

            for field_name in ['image_1', 'image_2', 'image_3', 'image_4']:
                uploaded_image = form.cleaned_data.get(field_name)
                if uploaded_image:
                    HostelImage.objects.create(hostel=hostel, image=uploaded_image)

            messages.success(request, f'Hostel "{hostel.name}" posted successfully!')
            return redirect('dashboard:seller_dashboard')
    else:
        form = HostelForm(user=request.user)

    return render(request, 'dashboard/hostel_form.html', {'form': form, 'title': 'Post Housing & Rental Unit'})



@login_required
@role_required([User.Role.SELLER])
def edit_listing(request, slug):
    listing = get_object_or_404(Listing, slug=slug, seller=request.user)
    
    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES, instance=listing, user=request.user)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.seller = request.user
            listing.save()
            messages.success(request, f'Listing "{listing.title}" created successfully and is now live!')
            return redirect('dashboard:seller_listings')
    else:
        form = ListingForm(instance=listing, user=request.user)
        
    return render(request, 'dashboard/listing_form.html', {'form': form, 'title': f'Edit "{listing.title}"'})


# buyer_dashboard removed — buyers browse anonymously without an account.


@login_required
@role_required([User.Role.ACCOUNTANT])
def accountant_dashboard(request):
    pending_subs = SellerSubscription.objects.filter(
        status=SellerSubscription.Status.PENDING
    ).order_by('submitted_at')

    context = {
        'pending_subs': pending_subs,
    }
    return render(request, 'dashboard/accountant_dashboard.html', context)


@login_required
@role_required([User.Role.MODERATOR])
def moderator_dashboard(request):
    pending_listings = Listing.objects.filter(status=Listing.Status.PENDING).order_by('created_at')
    pending_hostels = Hostel.objects.filter(status=Hostel.Status.PENDING).order_by('created_at')
    context = {
        'pending_listings': pending_listings,
        'pending_hostels': pending_hostels,
    }
    return render(request, 'dashboard/moderator_dashboard.html', context)


@login_required
@role_required([User.Role.ADMIN])
def admin_dashboard(request):
    total_listings = Listing.objects.count()
    active_listings = Listing.objects.filter(status=Listing.Status.ACTIVE).count()
    pending_listings = Listing.objects.filter(status=Listing.Status.PENDING).count()
    
    total_sellers = User.objects.filter(role=User.Role.SELLER).count()
    active_subscriptions = SellerSubscription.objects.filter(
        status=SellerSubscription.Status.APPROVED, 
        expires_at__gt=timezone.now()
    ).count()
    
    pending_payments = (
        SellerSubscription.objects.filter(status=SellerSubscription.Status.PENDING).count() + 
        BuyerMembership.objects.filter(status=BuyerMembership.Status.PENDING).count()
    )
    
    context = {
        'total_listings': total_listings,
        'active_listings': active_listings,
        'pending_listings': pending_listings,
        'total_sellers': total_sellers,
        'active_subscriptions': active_subscriptions,
        'pending_payments': pending_payments,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
@role_required([User.Role.SELLER])
def create_quick_sale(request):
    active_sub = request.user.active_quick_sale_subscription
    if not active_sub:
        messages.error(request, "You need an active Quick Sale subscription to post here.")
        return redirect('dashboard:seller_dashboard')

    if request.method == 'POST':
        form = QuickSaleForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.seller = request.user
            listing.is_quick_sale = True
            listing.quick_sale_expires_at = timezone.now() + timedelta(days=active_sub.plan.duration_days)
            listing.save()
            messages.success(request, f'"{listing.title}" posted as Quick Sale!')
            return redirect('dashboard:seller_dashboard')
    else:
        form = QuickSaleForm(user=request.user)

    return render(request, 'dashboard/quick_sale_form.html', {'form': form, 'title': 'Post Quick Sale Item'})