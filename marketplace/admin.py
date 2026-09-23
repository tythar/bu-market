from django import forms
from django.contrib import admin
from django.forms import BaseInlineFormSet
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from .models import Category, Listing, Hostel, HostelImage, Community, Offer

@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ['name', 'hub_type', 'region', 'order', 'is_active']
    list_filter = ['hub_type', 'region', 'is_active']
    search_fields = ['name', 'region']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order', 'is_active']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


class RemovalReasonForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea, label="Reason for removal")


@admin.action(description="Remove selected listings with a reason")
def remove_with_reason(modeladmin, request, queryset):
    if 'apply' in request.POST:
        form = RemovalReasonForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data['reason']
            for listing in queryset:
                listing.status = Listing.Status.REMOVED
                listing.removal_reason = reason
                listing.save()
                send_mail(
                    subject=f"Your listing '{listing.title}' was removed",
                    message=f"Your product '{listing.title}' was removed by an admin.\n\nReason: {reason}",
                    from_email=None,
                    recipient_list=[listing.seller.email],
                )
            return redirect(request.get_full_path())
    else:
        form = RemovalReasonForm()

    return render(request, 'admin/removal_reason_form.html', {
        'listings': queryset,
        'form': form,
    })


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ['title', 'seller', 'category', 'price', 'condition', 'status', 'is_promoted', 'is_quick_sale', 'quick_sale_expires_at']
    list_filter = ['status', 'is_promoted', 'is_quick_sale', 'condition', 'category']
    search_fields = ['title', 'description', 'seller__username']
    prepopulated_fields = {'slug': ('title',)}
    actions = [remove_with_reason]


class HostelImageFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        count = 0
        for form in self.forms:
            if not form.cleaned_data:
                continue
            if form.cleaned_data.get('DELETE'):
                continue
            if form.cleaned_data.get('image'):
                count += 1
        if count > 4:
            raise ValidationError("A hostel can have a maximum of 4 images.")


class HostelImageInline(admin.TabularInline):
    model = HostelImage
    extra = 1
    formset = HostelImageFormSet


@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    list_display = ['name', 'rental_type', 'billing_cycle', 'price', 'community', 'location', 'is_self_contained', 'has_yaka_meter', 'is_active', 'status']
    list_filter = ['rental_type', 'billing_cycle', 'community', 'is_self_contained', 'has_yaka_meter', 'has_security', 'status', 'is_active']
    search_fields = ['name', 'location', 'owner__username', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [HostelImageInline]


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ['id', 'listing', 'buyer', 'seller', 'original_price', 'offered_price', 'counter_price', 'status', 'deal_code', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['listing__title', 'buyer__username', 'seller__username', 'deal_code']
    readonly_fields = ['created_at', 'updated_at']