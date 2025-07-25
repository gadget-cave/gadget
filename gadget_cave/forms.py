from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, Product, Cart, Order # Corrected import
import re # For phone number validation

class CartAddProductForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, initial=1,
                                  widget=forms.NumberInput(attrs={'class': 'form-control'}))
    override = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'house_shop_no', 'address', 'landmark', 'city',
            'district', 'state', 'postal_code'
        ]
        # നിങ്ങൾക്ക് field order മാറ്റണമെങ്കിൽ, fields ടപ്പിൾ ഉപയോഗിക്കാം
        # fields = ('first_name', 'last_name', 'email', 'phone',
        #           'address', 'house_shop_no', 'landmark', 'city',
        #           'district', 'state', 'postal_code')

        labels = { # ഫോമിൽ കാണിക്കേണ്ട ലേബലുകൾ മാറ്റാൻ
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email',
            'phone': 'Phone Number',
            'house_shop_no': 'House No. / Shop No.',
            'address': 'Street Address',
            'landmark': 'Landmark',
            'city': 'City',
            'district': 'District',
            'state': 'State',
            'postal_code': 'Pincode',
        }
        widgets = { # ആവശ്യമെങ്കിൽ ഇൻപുട്ട് ഫീൽഡുകളുടെ ടൈപ്പ് മാറ്റാൻ
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        # Fields to display: username, phone_number, password, password2
        # UserCreationForm.Meta.fields already includes 'username', 'password', 'password2'.
        # We explicitly add 'phone_number'.
        fields = ('username', 'phone_number',) + UserCreationForm.Meta.fields[2:]

        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mobile Number'}),
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        if CustomUser.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError("This phone number is already registered.")
        
        # Basic regex validation for 10-digit Indian mobile numbers starting with 6, 7, 8, or 9
        if not re.fullmatch(r"^[6-9]\d{9}$", phone_number):
            raise forms.ValidationError("Enter a valid 10-digit Indian mobile number.")
        return phone_number

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = UserChangeForm.Meta.fields