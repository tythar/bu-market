from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from marketplace.models import Listing
from accounts.models import User


class Command(BaseCommand):
    help = "Suspends listings for sellers without an active subscription, reactivates renewed sellers, and deletes long-suspended or expired Quick Sale items."

    def handle(self, *args, **kwargs):
        now = timezone.now()

        sellers = User.objects.filter(role=User.Role.SELLER)
        suspended_count = 0
        reactivated_count = 0

        for seller in sellers:
            if seller.has_active_subscription:
                to_reactivate = Listing.objects.filter(seller=seller, status=Listing.Status.SUSPENDED)
                count = to_reactivate.update(status=Listing.Status.ACTIVE, suspended_at=None)
                reactivated_count += count
            else:
                to_suspend = Listing.objects.filter(seller=seller, status=Listing.Status.ACTIVE)
                count = to_suspend.update(status=Listing.Status.SUSPENDED, suspended_at=now)
                suspended_count += count

        grace_cutoff = now - timedelta(days=70)
        expired_suspended = Listing.objects.filter(
            status=Listing.Status.SUSPENDED,
            suspended_at__lt=grace_cutoff
        )
        deleted_grace_count = expired_suspended.count()
        expired_suspended.delete()

        expired_quick_sales = Listing.objects.filter(
            is_quick_sale=True,
            quick_sale_expires_at__lt=now
        )
        deleted_quick_sale_count = expired_quick_sales.count()
        expired_quick_sales.delete()

        self.stdout.write(self.style.SUCCESS(
            f"Suspended: {suspended_count}, Reactivated: {reactivated_count}, "
            f"Deleted (70-day grace expired): {deleted_grace_count}, "
            f"Deleted (Quick Sale expired): {deleted_quick_sale_count}"
        ))