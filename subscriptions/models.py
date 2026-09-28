from django.db import models
from django.conf import settings
from core.validators import validate_file_size
from django.utils import timezone

class SubscriptionPlan(models.Model):
    class PlanType(models.TextChoices):
        BASIC = 'BASIC', 'Basic'
        SILVER = 'SILVER', 'Silver'
        GOLD = 'GOLD', 'Gold'
        QUICK_SALE = 'QUICK_SALE', 'Quick Sale'
        HOSTEL = 'HOSTEL', 'Hostel'

    class BadgeType(models.TextChoices):
        NONE = 'none', 'None'
        SILVER = 'SILVER', 'Silver'
        GOLD = 'GOLD', 'Gold'

    name = models.CharField(
        max_length=10,
        choices=PlanType.choices,
        unique=True
    )
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField(default=30)
    max_active_listings = models.PositiveIntegerField()
    badge = models.CharField(
        max_length=10,
        choices=BadgeType.choices,
        default=BadgeType.NONE
    )
    has_promoted_ads = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_name_display()} Plan ({self.max_active_listings} listings)"


class SellerSubscription(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='seller_subscriptions'
    )
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    receipt_image = models.ImageField(
        upload_to='receipts/seller/',
        validators=[validate_file_size]
    )
    payment_reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_seller_subscriptions'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.seller.username} - {self.plan.name} ({self.get_status_display()})"


class BuyerMembership(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACTIVE = 'ACTIVE', 'Active'
        EXPIRED = 'EXPIRED', 'Expired'

    buyer = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='buyer_membership'
    )
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=20000.00)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    receipt_image = models.ImageField(
        upload_to='receipts/buyer/',
        validators=[validate_file_size]
    )
    payment_reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_buyer_memberships'
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.buyer.username} - Buyer ({self.get_status_display()})"