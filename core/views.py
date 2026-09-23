from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
import decimal
from marketplace.models import Category, Listing, Community, Offer
from accounts.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages as django_messages
from messaging.models import Conversation, Message


def switch_community(request, slug):
    """
    Switches the active community or scope in the user session,
    then redirects back to the previous page.
    """
    if slug == 'all':
        request.session['community_scope'] = 'all'
    else:
        community = get_object_or_404(Community, slug=slug, is_active=True)
        request.session['community_slug'] = community.slug
        request.session['community_scope'] = 'community'

    scope_param = request.GET.get('scope')
    if scope_param in ['community', 'all']:
        request.session['community_scope'] = scope_param

    referer = request.META.get('HTTP_REFERER')
    if referer and referer.startswith(request.build_absolute_uri('/')[:-1]):
        return redirect(referer)
    return redirect('core:home')


class HomeView(ListView):
    model = Listing
    template_name = 'core/home.html'
    context_object_name = 'listings'

    def get_queryset(self):
        queryset = Listing.objects.filter(status=Listing.Status.ACTIVE)
        scope = self.request.session.get('community_scope', 'community')
        comm_slug = self.request.session.get('community_slug')

        if scope == 'community':
            active_comm = None
            if comm_slug:
                active_comm = Community.objects.filter(slug=comm_slug, is_active=True).first()
            if not active_comm:
                active_comm = Community.objects.filter(slug='bugema-university', is_active=True).first() or Community.objects.first()
            if active_comm:
                queryset = queryset.filter(community=active_comm)

        return queryset.order_by('-is_promoted', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)

        scope = self.request.session.get('community_scope', 'community')
        comm_slug = self.request.session.get('community_slug')

        promoted_qs = Listing.objects.filter(status=Listing.Status.ACTIVE, is_promoted=True)
        if scope == 'community':
            active_comm = None
            if comm_slug:
                active_comm = Community.objects.filter(slug=comm_slug, is_active=True).first()
            if not active_comm:
                active_comm = Community.objects.filter(slug='bugema-university', is_active=True).first() or Community.objects.first()
            if active_comm:
                promoted_qs = promoted_qs.filter(community=active_comm)

        context['promoted_listings'] = promoted_qs.order_by('-created_at')[:4]

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

        # Apply search query
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(Q(title__icontains=q) | Q(description__icontains=q))

        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        # Community & Scope Filter
        comm_param = self.request.GET.get('community')
        scope_param = self.request.GET.get('scope')

        if comm_param == 'all' or scope_param == 'all':
            pass  # Nationwide / All Communities
        elif comm_param:
            queryset = queryset.filter(community__slug=comm_param)
        else:
            session_scope = self.request.session.get('community_scope', 'community')
            if session_scope == 'community':
                comm_slug = self.request.session.get('community_slug')
                active_comm = None
                if comm_slug:
                    active_comm = Community.objects.filter(slug=comm_slug, is_active=True).first()
                if not active_comm:
                    active_comm = Community.objects.filter(slug='bugema-university', is_active=True).first() or Community.objects.first()
                if active_comm:
                    queryset = queryset.filter(community=active_comm)

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

        listing.views_count += 1
        listing.save(update_fields=['views_count'])

        recently_viewed = self.request.session.get('recently_viewed', [])
        if listing.id in recently_viewed:
            recently_viewed.remove(listing.id)
        recently_viewed.insert(0, listing.id)
        self.request.session['recently_viewed'] = recently_viewed[:5]

        return listing

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        listing = self.object
        if user.is_authenticated:
            if user != listing.seller:
                context['buyer_active_offer'] = listing.offers.filter(buyer=user).first()
            else:
                context['incoming_offers'] = listing.offers.all().order_by('-created_at')
        return context


def seller_profile(request, username):
    seller = get_object_or_404(User, username=username, role=User.Role.SELLER)
    listings = Listing.objects.filter(seller=seller, status=Listing.Status.ACTIVE).order_by('-is_promoted')

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


@login_required
def make_offer(request, slug):
    listing = get_object_or_404(Listing, slug=slug)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.user == listing.seller:
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': "You cannot make an offer on your own listing."}, status=400)
        django_messages.error(request, "You cannot make an offer on your own listing.")
        return redirect('core:listing_detail', slug=slug)

    if listing.status != Listing.Status.ACTIVE:
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': "This item is no longer active for offers."}, status=400)
        django_messages.error(request, "This item is no longer active.")
        return redirect('core:listing_detail', slug=slug)

    if request.method == 'POST':
        raw_price = request.POST.get('offered_price', '0').replace(',', '').strip()
        try:
            offered_price = decimal.Decimal(raw_price)
        except (ValueError, decimal.InvalidOperation):
            offered_price = decimal.Decimal('0')

        if offered_price <= 0:
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': "Please enter a valid offer amount in UGX."}, status=400)
            django_messages.error(request, "Please enter a valid offer amount in UGX.")
            return redirect('core:listing_detail', slug=slug)

        buyer_note = request.POST.get('buyer_note', '').strip()[:255]

        offer, created = Offer.objects.get_or_create(
            listing=listing,
            buyer=request.user,
            seller=listing.seller,
            defaults={
                'original_price': listing.price,
                'offered_price': offered_price,
                'buyer_note': buyer_note,
                'status': Offer.Status.PENDING,
            }
        )
        if not created:
            offer.original_price = listing.price
            offer.offered_price = offered_price
            offer.counter_price = None
            offer.buyer_note = buyer_note
            offer.seller_note = ''
            offer.status = Offer.Status.PENDING
            offer.save()

        try:
            conversation, _ = Conversation.objects.get_or_create(
                listing=listing,
                buyer=request.user,
                seller=listing.seller,
            )
            msg_text = f"🤝 Bargain Offer: {offered_price:,.0f} UGX (Original Price: {listing.price:,.0f} UGX)."
            if buyer_note:
                msg_text += f" Message: \"{buyer_note}\""
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                body=msg_text
            )
        except Exception:
            pass

        if is_ajax:
            return JsonResponse({
                'status': 'success',
                'message': f"🚀 Your offer of {offered_price:,.0f} UGX was sent to {listing.seller.username}!",
                'offer_id': offer.id,
                'offered_price': f"{offered_price:,.0f} UGX",
            })

        django_messages.success(request, f"🚀 Your offer of {offered_price:,.0f} UGX was sent to {listing.seller.username}!")
        return redirect('core:listing_detail', slug=slug)

    return redirect('core:listing_detail', slug=slug)


@login_required
def respond_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    user = request.user
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if user not in [offer.seller, offer.buyer]:
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': "Permission denied."}, status=403)
        django_messages.error(request, "Permission denied.")
        return redirect('core:home')

    if request.method == 'POST':
        action = request.POST.get('action')
        note = request.POST.get('note', '').strip()[:255]

        if action == 'accept':
            offer.status = Offer.Status.ACCEPTED
            offer.generate_deal_code()
            if user == offer.seller:
                offer.seller_note = note or "Offer accepted! Deal locked 🎉"
            else:
                offer.buyer_note = note or "Counter offer accepted! Deal locked 🎉"
            offer.save()

            try:
                conv = Conversation.objects.filter(listing=offer.listing, buyer=offer.buyer, seller=offer.seller).first()
                if conv:
                    Message.objects.create(
                        conversation=conv,
                        sender=user,
                        body=f"🎉 Deal Confirmed! Agreed price: {offer.final_price:,.0f} UGX (Deal Code: {offer.deal_code})."
                    )
            except Exception:
                pass

            receipt_url = reverse('core:deal_receipt', kwargs={'offer_id': offer.id})
            if is_ajax:
                return JsonResponse({
                    'status': 'success',
                    'message': 'Offer accepted! Deal pass generated.',
                    'deal_code': offer.deal_code,
                    'receipt_url': receipt_url
                })

            django_messages.success(request, f"🎉 Deal confirmed at {offer.final_price:,.0f} UGX! Deal Pass generated.")
            return redirect('core:deal_receipt', offer_id=offer.id)

        elif action == 'counter':
            raw_counter = request.POST.get('counter_price', '0').replace(',', '').strip()
            try:
                counter_price = decimal.Decimal(raw_counter)
            except (ValueError, decimal.InvalidOperation):
                counter_price = decimal.Decimal('0')

            if counter_price <= 0:
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': "Please enter a valid counter price in UGX."}, status=400)
                django_messages.error(request, "Please enter a valid counter price in UGX.")
                return redirect(request.META.get('HTTP_REFERER', 'core:my_offers'))

            offer.counter_price = counter_price
            offer.status = Offer.Status.COUNTERED
            if user == offer.seller:
                offer.seller_note = note or f"Seller countered: {counter_price:,.0f} UGX"
            else:
                offer.buyer_note = note or f"Buyer countered: {counter_price:,.0f} UGX"
            offer.save()

            try:
                conv = Conversation.objects.filter(listing=offer.listing, buyer=offer.buyer, seller=offer.seller).first()
                if conv:
                    Message.objects.create(
                        conversation=conv,
                        sender=user,
                        body=f"⚡ Counter Offer: {counter_price:,.0f} UGX. Note: \"{note}\""
                    )
            except Exception:
                pass

            if is_ajax:
                return JsonResponse({
                    'status': 'success',
                    'message': f"⚡ Counter offer of {counter_price:,.0f} UGX sent!",
                    'counter_price': f"{counter_price:,.0f} UGX"
                })

            django_messages.success(request, f"⚡ Counter offer of {counter_price:,.0f} UGX sent!")
            return redirect(request.META.get('HTTP_REFERER', 'core:my_offers'))

        elif action == 'decline':
            offer.status = Offer.Status.DECLINED
            if user == offer.seller:
                offer.seller_note = note or "Offer declined."
            else:
                offer.buyer_note = note or "Counter offer declined."
            offer.save()

            if is_ajax:
                return JsonResponse({'status': 'success', 'message': "Offer declined."})

            django_messages.info(request, "Offer has been declined.")
            return redirect(request.META.get('HTTP_REFERER', 'core:my_offers'))

    return redirect('core:my_offers')


@login_required
def deal_receipt(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id, status=Offer.Status.ACCEPTED)
    if request.user not in [offer.buyer, offer.seller] and not request.user.is_staff:
        django_messages.error(request, "You do not have permission to view this deal receipt.")
        return redirect('core:home')

    is_buyer = request.user == offer.buyer
    whatsapp_deal_url = offer.get_whatsapp_url(recipient_role='seller' if is_buyer else 'buyer')

    context = {
        'offer': offer,
        'listing': offer.listing,
        'is_buyer': is_buyer,
        'other_party': offer.seller if is_buyer else offer.buyer,
        'whatsapp_deal_url': whatsapp_deal_url,
    }
    return render(request, 'marketplace/deal_receipt.html', context)


@login_required
def my_offers(request):
    user = request.user
    offers_made = Offer.objects.filter(buyer=user).select_related('listing', 'seller', 'listing__community').order_by('-updated_at')
    offers_received = Offer.objects.filter(seller=user).select_related('listing', 'buyer', 'listing__community').order_by('-updated_at')

    context = {
        'offers_made': offers_made,
        'offers_received': offers_received,
        'pending_received_count': offers_received.filter(status=Offer.Status.PENDING).count(),
        'active_bargains_count': offers_made.filter(status__in=[Offer.Status.PENDING, Offer.Status.COUNTERED]).count(),
    }
    return render(request, 'marketplace/deal_receipt.html', context)