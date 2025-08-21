from django import forms
from .models import Account
from django.contrib.auth.forms import PasswordChangeForm


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
        'placeholder': 'Enter Password',
        'class': 'form-control',
        'autocomplete': 'new-password',
        'spellcheck': 'false',
        'autocapitalize': 'off',
        'autocorrect': 'off',
        'inputmode': 'text',
    }),
    strip=False,  # ← IMPORTANT: do not strip passwords
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm Password',
            'class': 'form-control',
            'autocomplete': 'new-password',
            'spellcheck': 'false',
            'autocapitalize': 'off',
            'autocorrect': 'off',
            'inputmode': 'text',
        }),
        strip=False,  # ← IMPORTANT
    )
    
    class Meta:
        model = Account
        fields = [
            'first_name',
            'last_name',
            'phone_number',
            'email',
            'password',
        ]
    
    # Assigns class form-control to all classes
    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['placeholder'] = 'Enter First Name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Enter Last Name'
        self.fields['phone_number'].widget.attrs['placeholder'] = 'Enter Phone Number'
        self.fields['email'].widget.attrs['placeholder'] = 'Enter Email Address'
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
            
            
    def clean(self):
        # We use super class to modify default actions
        cleaned_data = super(RegistrationForm, self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError(
                "Password does not match!"
            )
        return cleaned_data
    
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ["first_name", "last_name","email", "phone_number", "gender", "profile_picture", "payment_qr"]
        # widgets = {
        #     "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "First name"}),
        #     "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Last name"}),
        #     "phone_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone number"}),
        #     "gender": forms.Select(attrs={"class": "form-control"}),
        # }
        
        # Override default widget for profile_picture:
        # - By default, Django uses ClearableFileInput, which shows:
        #   "Currently: <file path>" and a "Clear" checkbox.
        # - We replace it with FileInput to hide that text/checkbox
        #   because we already display a custom image preview in the template.
        widgets = {
            "profile_picture": forms.FileInput(attrs={"class": "form-control"}),
            "payment_qr": forms.ClearableFileInput(attrs={"class": "form-control-file"}),
        }

    def __init__(self, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        # Loop through all fields and add Bootstrap's form-control class for styling
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
            

class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Customizable password change form:
    - Bootstrap-ready widgets
    - Clear labels/placeholders
    - Friendly error messages
    - Shows password rules (from AUTH_PASSWORD_VALIDATORS)
    """

    # Optional: override default messages
    error_messages = {
        "password_incorrect": "Your current password is incorrect.",
        "password_mismatch": "The two new passwords didn’t match.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add Bootstrap classes & placeholders
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter current password'
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter new password'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })


    # If you want additional custom validation, you can extend clean():
    # def clean(self):
    #     cleaned = super().clean()
    #     # Example: block passwords that contain the username/email
    #     if self.user and self.user.email:
    #         if self.cleaned_data.get("new_password1") and self.user.email.split("@")[0].lower() in self.cleaned_data["new_password1"].lower():
    #             self.add_error("new_password1", "New password should not contain parts of your email.")
    #     return cleaned