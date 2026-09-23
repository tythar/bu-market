from django import forms
from .models import Listing, Hostel, HostelImage

class ListingForm(forms.ModelForm):
    class Meta:
            model = Listing
            fields = ['category', 'title', 'description', 'price', 'condition', 'location', 'image', 'is_promoted', 'phone_number', 'whatsapp_number']
            widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if self.user:
            # Temporarily attach the seller instance to run validation
            self.instance.seller = self.user
        
        # Call model clean() to run limits/subscriptions checks
        self.instance.clean()
        return cleaned_data


class HostelForm(forms.ModelForm):
    image_1 = forms.ImageField(required=True)
    image_2 = forms.ImageField(required=False)
    image_3 = forms.ImageField(required=False)
    image_4 = forms.ImageField(required=False)

    class Meta:
        model = Hostel
        fields = ['name', 'location', 'price', 'description', 'phone_number', 'whatsapp_number']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if self.user:
            self.instance.owner = self.user
        self.instance.clean()
        return cleaned_data

# this is for the quick sale input

class QuickSaleForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['category', 'title', 'description', 'price', 'location', 'image', 'phone_number', 'whatsapp_number']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if self.user:
            self.instance.seller = self.user
        self.instance.is_quick_sale = True
        self.instance.clean()
        return cleaned_data
