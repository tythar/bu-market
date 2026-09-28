from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from marketplace.models import Listing, Hostel
from accounts.models import User


class Command(BaseCommand):
    help = (
        "Suspends listings/hostels whose owner has no active plan, reactivates renewed owners, "
        "and deletes long-suspended items and expired Quick Sale items."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Show what would change without changing anything.",
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()
        grace_cutoff = now - timedelta(days=70)

        suspended = 0
        reactivated = 0

        for seller in User.objects.filter(role=User.Role.SELLER):
            # Regular listings follow the Basic/Silver/Gold plans.
            # Quick Sale listings are excluded: they follow their own expiry.
            if seller.has_active_subscription:
                qs = Listing.objects.filter(seller=seller, is_quick_sale=False, status=Listing.Status.SUSPENDED)
                reactivated += qs.count() if dry_run else qs.update(status=Listing.Status.ACTIVE, suspended_at=None)
            else:
                qs = Listing.objects.filter(seller=seller, is_quick_sale=False, status=Listing.Status.ACTIVE)
                suspended += qs.count() if dry_run else qs.update(status=Listing.Status.SUSPENDED, suspended_at=now)

            # Hostels follow the separate Hostel plan.
            if seller.has_active_hostel_subscription:
                qs = Hostel.objects.filter(owner=seller, status=Hostel.Status.SUSPENDED)
                reactivated += qs.count() if dry_run else qs.update(status=Hostel.Status.ACTIVE, suspended_at=None)
            else:
                qs = Hostel.objects.filter(owner=seller, status=Hostel.Status.ACTIVE)
                suspended += qs.count() if dry_run else qs.update(status=Hostel.Status.SUSPENDED, suspended_at=now)

        old_listings = Listing.objects.filter(status=Listing.Status.SUSPENDED, suspended_at__lt=grace_cutoff)
        old_hostels = Hostel.objects.filter(status=Hostel.Status.SUSPENDED, suspended_at__lt=grace_cutoff)
        expired_quick = Listing.objects.filter(is_quick_sale=True, quick_sale_expires_at__lt=now)

        deleted_grace = old_listings.count() + old_hostels.count()
        deleted_quick = expired_quick.count()

        if not dry_run:
            old_listings.delete()
            old_hostels.delete()
            expired_quick.delete()

        prefix = "[DRY RUN - nothing changed] " if dry_run else ""
        self.stdout.write(self.style.SUCCESS(
            f"{prefix}Suspended: {suspended}, Reactivated: {reactivated}, "
            f"Deleted (70-day grace expired): {deleted_grace}, "
            f"Deleted (Quick Sale expired): {deleted_quick}"
        ))