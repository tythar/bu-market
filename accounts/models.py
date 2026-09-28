from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        BUYER = 'BUYER', 'Buyer'
        SELLER = 'SELLER', 'Seller'
        ACCOUNTANT = 'ACCOUNTANT', 'Accountant'
        MODERATOR = 'MODERATOR', 'Moderator'
        ADMIN = 'ADMIN', 'Admin'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.BUYER
    )

    @property
    def is_buyer(self):
        return self.role == self.Role.BUYER

    @property
    def is_seller(self):
        return self.role == self.Role.SELLER

    @property
    def is_accountant(self):
        return self.role == self.Role.ACCOUNTANT

    @property
    def is_moderator(self):
        return self.role == self.Role.MODERATOR

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN or self.is_superuser


    def get_active_subscription(self, plan_type=None):
        from subscriptions.models import SellerSubscription
        from django.utils import timezone
        qs = SellerSubscription.objects.filter(
            seller=self,
            status=SellerSubscription.Status.APPROVED,
            expires_at__gt=timezone.now()
        )
        if plan_type:
            qs = qs.filter(plan__name=plan_type)
        return qs.order_by('-approved_at').first()

    @property
    def active_subscription(self):
        from subscriptions.models import SellerSubscription, SubscriptionPlan
        from django.utils import timezone
        return SellerSubscription.objects.filter(
            seller=self,
            status=SellerSubscription.Status.APPROVED,
            expires_at__gt=timezone.now(),
            plan__name__in=[
                SubscriptionPlan.PlanType.BASIC,
                SubscriptionPlan.PlanType.SILVER,
                SubscriptionPlan.PlanType.GOLD,
            ],
        ).order_by('-approved_at').first()

    @property
    def active_quick_sale_subscription(self):
        return self.get_active_subscription(plan_type='QUICK_SALE')

    @property
    def has_active_quick_sale_subscription(self):
        return self.active_quick_sale_subscription is not None

    @property
    def active_hostel_subscription(self):
        return self.get_active_subscription(plan_type='HOSTEL')

    @property
    def has_active_hostel_subscription(self):
        return self.active_hostel_subscription is not None

    @property
    def has_active_subscription(self):
        from subscriptions.models import SubscriptionPlan
        regular_plans = [
            SubscriptionPlan.PlanType.BASIC,
            SubscriptionPlan.PlanType.SILVER,
            SubscriptionPlan.PlanType.GOLD,
        ]
        for plan_type in regular_plans:
            if self.get_active_subscription(plan_type=plan_type):
                return True
        return False

    @property
    def max_allowed_active_listings(self):
        sub = self.active_subscription
        if sub:
            return sub.plan.max_active_listings
        return 0

    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Phone number for calls (e.g. +256700000000)"
    )
    whatsapp_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="WhatsApp number (e.g. +256700000000)"
    )

    @property
    def whatsapp_url(self):
        if not self.whatsapp_number:
            return None
        cleaned = "".join(c for c in self.whatsapp_number if c.isdigit())
        if cleaned.startswith('0'):
            cleaned = '256' + cleaned[1:]
        return f"https://wa.me/{cleaned}"

    @property
    def tel_url(self):
        if not self.phone_number:
            return None
        cleaned = "".join(c for c in self.phone_number if c.isdigit() or c == '+')
        return f"tel:{cleaned}"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


