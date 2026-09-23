from django import forms
from .models import Listing, Hostel, HostelImage, Community


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['category', 'community', 'title', 'description', 'price', 'condition', 'location', 'image', 'is_promoted', 'phone_number', 'whatsapp_number']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['community'].queryset = Community.objects.filter(is_active=True).order_by('order', 'name')
        self.fields['community'].empty_label = "Select Campus or Town Hub"

    def clean(self):
        cleaned_data = super().clean()
        if self.user:
            self.instance.seller = self.user
        self.instance.clean()
        return cleaned_data


class HostelForm(forms.ModelForm):
    image_1 = forms.ImageField(required=True, label="Main Cover Photo")
    image_2 = forms.ImageField(required=False, label="Photo 2 (Interior / Washroom)")
    image_3 = forms.ImageField(required=False, label="Photo 3 (Compound / Kitchen)")
    image_4 = forms.ImageField(required=False, label="Photo 4 (Surroundings)")

    class Meta:
        model = Hostel
        fields = [
            'name', 'rental_type', 'billing_cycle', 'community', 'location',
            'price', 'description', 'is_self_contained', 'has_yaka_meter',
            'has_water_reserve', 'has_security', 'has_parking',
            'phone_number', 'whatsapp_number'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe the property, water access, security, terms, and neighborhood...'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['community'].queryset = Community.objects.filter(is_active=True).order_by('order', 'name')
        self.fields['community'].empty_label = "Select Campus or Town Hub"

    def clean(self):
        cleaned_data = super().clean()
        if self.user:
            self.instance.owner = self.user
        self.instance.clean()
        return cleaned_data


class QuickSaleForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['category', 'community', 'title', 'description', 'price', 'location', 'image', 'phone_number', 'whatsapp_number']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['community'].queryset = Community.objects.filter(is_active=True).order_by('order', 'name')
        self.fields['community'].empty_label = "Select Campus or Town Hub"

    def clean(self):
        cleaned_data = super().clean()
        if self.user:
            self.instance.seller = self.user
        self.instance.is_quick_sale = True
        self.instance.clean()
        return cleaned_data