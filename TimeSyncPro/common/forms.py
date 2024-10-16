from django import forms

from TimeSyncPro.common.models import Address


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ["house_number_or_name", "line1", "line2", "street", "city", "postcode", "country"]
        labels = {
            "house_number_or_name": "House number or name",
            "line1": "Line 1",
            "line2": "Line 2",
            "street": "Street",
            "city": "City",
            "postcode": "Postcode",
            "country": "Country",
        }


