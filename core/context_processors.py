from marketplace.models import Listing, Community


def recently_viewed(request):
    ids = request.session.get('recently_viewed', [])
    listings = []
    if ids:
        listings_by_id = Listing.objects.in_bulk(ids)
        listings = [listings_by_id[i] for i in ids if i in listings_by_id]
    return {'recently_viewed_listings': listings}


def community_context(request):
    community_slug = request.session.get('community_slug')
    scope = request.session.get('community_scope', 'community')

    active_community = None
    if community_slug:
        active_community = Community.objects.filter(slug=community_slug, is_active=True).first()

    if not active_community:
        # Default to Bugema University, or first active campus
        active_community = Community.objects.filter(slug='bugema-university', is_active=True).first()
        if not active_community:
            active_community = Community.objects.filter(is_active=True).first()

    campus_communities = Community.objects.filter(is_active=True, hub_type=Community.HubType.CAMPUS).order_by('order', 'name')
    town_communities = Community.objects.filter(is_active=True, hub_type=Community.HubType.TOWN).order_by('order', 'name')

    return {
        'active_community': active_community,
        'community_scope': scope,  # 'community' or 'all'
        'campus_communities': campus_communities,
        'town_communities': town_communities,
    }