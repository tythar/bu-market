from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.db.models import Q
from marketplace.models import Category, Listing
from accounts.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages as django_messages
from messaging.models import Conversation


class HomeView(ListView):
    model = Listing
    template_name = 'core/home.html'
    context_object_name = 'listings'

    def get_queryset(self):
        # We only show ACTIVE listings
        return Listing.objects.filter(status=Listing.Status.ACTIVE).order_by('-is_promoted', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['promoted_listings'] = Listing.objects.filter(
            status=Listing.Status.ACTIVE,
            is_promoted=True
        ).order_by('-created_at')[:4]
        context['quick_sale_items'] = Listing.objects.filter(
            status=Listing.Status.ACTIVE,
            is_quick_sale=True,
            quick_sale_expires_at__gt=timezone.now()
        ).order_by('-created_at')[:10]
        return context


class BrowseView(ListView):
    model = Listing
    template_name = 'core/browse.html'
    context_object_name = 'listings'
    paginate_by = 12

    def get_queryset(self):
        queryset = Listing.objects.filter(status=Listing.Status.ACTIVE)

        # Apply filters
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(Q(title__icontains=q) | Q(description__icontains=q))

        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)


        location = self.request.GET.get('location')
        if location:
            queryset = queryset.filter(location__icontains=location)


        min_price = self.request.GET.get('min_price')
        if min_price:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except ValueError:
                pass

        max_price = self.request.GET.get('max_price')
        if max_price:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except ValueError:
                pass

        condition = self.request.GET.get('condition')
        if condition in [Listing.Condition.NEW, Listing.Condition.USED]:
            queryset = queryset.filter(condition=condition)

        sort_option = self.request.GET.get('sort', '')
        if sort_option == 'price_asc':
            ordering = ['-is_promoted', 'price', '-created_at']
        elif sort_option == 'price_desc':
            ordering = ['-is_promoted', '-price', '-created_at']
        elif sort_option == 'oldest':
            ordering = ['-is_promoted', 'created_at']
        else:
            ordering = ['-is_promoted', '-created_at']

        return queryset.order_by(*ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        # Preserve filters in pagination
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            query_params.pop('page')
        context['query_string'] = query_params.urlencode()
        return context


class ListingDetailView(DetailView):
    model = Listing
    template_name = 'core/listing_detail.html'
    context_object_name = 'listing'

    def get_object(self, queryset=None):
        # Allow owner, moderator, or admin to view non-active listings
        listing = get_object_or_404(Listing, slug=self.kwargs.get('slug'))
        user = self.request.user

        if listing.status != Listing.Status.ACTIVE:
            is_authorized = (
                user.is_authenticated and (
                    user == listing.seller or
                    user.is_moderator or
                    user.is_admin_role or
                    user.is_accountant
                )
            )
            if not is_authorized:
                from django.http import Http404
                raise Http404("Listing not found or pending moderation.")

        # Increment view count
        listing.views_count += 1
        listing.save(update_fields=['views_count'])

        # Track recently viewed listings in session
        recently_viewed = self.request.session.get('recently_viewed', [])
        if listing.id in recently_viewed:
            recently_viewed.remove(listing.id)
        recently_viewed.insert(0, listing.id)
        self.request.session['recently_viewed'] = recently_viewed[:5]

        return listing


def seller_profile(request, username):
    seller = get_object_or_404(User, username=username, role=User.Role.SELLER)
    listings = Listing.objects.filter(seller=seller, status=Listing.Status.ACTIVE).order_by('-is_promoted')

    # Get active subscription badge
    active_sub = seller.active_subscription
    badge = active_sub.plan.badge if active_sub else 'none'

    context = {
        'seller': seller,
        'listings': listings,
        'badge': badge,
    }
    return render(request, 'core/seller_profile.html', context)


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