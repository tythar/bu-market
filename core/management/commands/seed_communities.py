from django.core.management.base import BaseCommand
from marketplace.models import Community, Listing, Hostel


class Command(BaseCommand):
    help = "Seeds initial university campuses and towns, and maps existing listings to their communities"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=== Seeding Initial Communities & Campus Hubs ==="))

        communities_data = [
            # Campuses
            {
                'name': 'Bugema University',
                'slug': 'bugema-university',
                'hub_type': Community.HubType.CAMPUS,
                'region': 'Central / Luweero',
                'icon': 'bi-mortarboard-fill',
                'order': 1,
            },
            {
                'name': 'Makerere University (MUK)',
                'slug': 'makerere-university',
                'hub_type': Community.HubType.CAMPUS,
                'region': 'Kampala',
                'icon': 'bi-mortarboard-fill',
                'order': 2,
            },
            {
                'name': 'Kyambogo University (KYU)',
                'slug': 'kyambogo-university',
                'hub_type': Community.HubType.CAMPUS,
                'region': 'Kampala',
                'icon': 'bi-mortarboard-fill',
                'order': 3,
            },
            {
                'name': 'Uganda Christian University (UCU)',
                'slug': 'ucu-mukono',
                'hub_type': Community.HubType.CAMPUS,
                'region': 'Mukono',
                'icon': 'bi-mortarboard-fill',
                'order': 4,
            },
            {
                'name': 'Mbarara University (MUST)',
                'slug': 'must-mbarara',
                'hub_type': Community.HubType.CAMPUS,
                'region': 'Western / Mbarara',
                'icon': 'bi-mortarboard-fill',
                'order': 5,
            },
            {
                'name': 'Kampala International University (KIU)',
                'slug': 'kiu-kansanga',
                'hub_type': Community.HubType.CAMPUS,
                'region': 'Kampala',
                'icon': 'bi-mortarboard-fill',
                'order': 6,
            },
            {
                'name': 'Gulu University',
                'slug': 'gulu-university',
                'hub_type': Community.HubType.CAMPUS,
                'region': 'Northern / Gulu',
                'icon': 'bi-mortarboard-fill',
                'order': 7,
            },

            # Towns & Commercial Centers
            {
                'name': 'Gayaza Town',
                'slug': 'gayaza-town',
                'hub_type': Community.HubType.TOWN,
                'region': 'Wakiso',
                'icon': 'bi-shop',
                'order': 10,
            },
            {
                'name': 'Kiwenda',
                'slug': 'kiwenda',
                'hub_type': Community.HubType.TOWN,
                'region': 'Wakiso',
                'icon': 'bi-shop',
                'order': 11,
            },
            {
                'name': 'Busiika Town',
                'slug': 'busiika-town',
                'hub_type': Community.HubType.TOWN,
                'region': 'Luweero',
                'icon': 'bi-shop',
                'order': 12,
            },
            {
                'name': 'Kasangati',
                'slug': 'kasangati',
                'hub_type': Community.HubType.TOWN,
                'region': 'Wakiso',
                'icon': 'bi-buildings-fill',
                'order': 13,
            },
            {
                'name': 'Mukono Town',
                'slug': 'mukono-town',
                'hub_type': Community.HubType.TOWN,
                'region': 'Mukono',
                'icon': 'bi-buildings-fill',
                'order': 14,
            },
            {
                'name': 'Kampala Central',
                'slug': 'kampala-central',
                'hub_type': Community.HubType.TOWN,
                'region': 'Kampala',
                'icon': 'bi-building',
                'order': 15,
            },
            {
                'name': 'Mbarara City',
                'slug': 'mbarara-city',
                'hub_type': Community.HubType.TOWN,
                'region': 'Mbarara',
                'icon': 'bi-buildings-fill',
                'order': 16,
            },
        ]

        comm_map = {}
        for cdata in communities_data:
            community, created = Community.objects.update_or_create(
                slug=cdata['slug'],
                defaults=cdata
            )
            comm_map[cdata['slug']] = community
            action = "Created" if created else "Updated"
            self.stdout.write(f"  [{action}] {community.name} ({community.get_hub_type_display()})")

        bugema = comm_map['bugema-university']
        gayaza = comm_map['gayaza-town']
        kiwenda = comm_map['kiwenda']
        busiika = comm_map['busiika-town']

        # Map existing listings
        self.stdout.write(self.style.NOTICE("\nMapping existing Listings to Communities..."))
        for listing in Listing.objects.all():
            loc_lower = (listing.location or '').lower()
            if 'gayaza' in loc_lower:
                listing.community = gayaza
            elif 'kiwenda' in loc_lower:
                listing.community = kiwenda
            elif 'busiika' in loc_lower:
                listing.community = busiika
            else:
                listing.community = bugema
            listing.save(update_fields=['community'])
            self.stdout.write(f"  Listing '{listing.title[:30]}...' -> {listing.community.name}")

        # Map existing Hostels
        self.stdout.write(self.style.NOTICE("\nMapping existing Hostels to Communities..."))
        for hostel in Hostel.objects.all():
            loc_lower = (hostel.location or '').lower()
            if 'kiwenda' in loc_lower:
                hostel.community = kiwenda
            elif 'gayaza' in loc_lower:
                hostel.community = gayaza
            elif 'busiika' in loc_lower:
                hostel.community = busiika
            else:
                hostel.community = bugema
            hostel.save(update_fields=['community'])
            self.stdout.write(f"  Hostel '{hostel.name}' -> {hostel.community.name}")

        self.stdout.write(self.style.SUCCESS("\nSuccessfully seeded communities and mapped all existing data!"))
