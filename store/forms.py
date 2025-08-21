# products/forms.py
from django import forms
from .models import Product, Review, Variation

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ("owner", "is_approved", "slug")  # admin controls approval
        widgets = {
            # Keep FileInput as we don't want "Currently... Clear"
            "images": forms.FileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        # Make image optional on UPDATE
        if self.instance and self.instance.pk:
            self.fields["images"].required = False
            
        for f in self.fields.values():
            existing = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (existing + " form-control").strip()

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price
    
    def clean_images(self):
        """
        If no new image uploaded on edit, keep the existing one.
        """
        image = self.cleaned_data.get("images")
        if not image and self.instance and self.instance.pk:
            return self.instance.images
        return image

    def clean_stock(self):
        stock = self.cleaned_data.get("stock")
        if stock is not None and stock < 0:
            raise forms.ValidationError("Stock cannot be negative.")
        return stock
    
    def clean_discount_price(self):
        discount_price = self.cleaned_data.get("discount_price")
        price = self.cleaned_data.get("price")

        if discount_price is not None:
            if discount_price < 0:
                raise forms.ValidationError("Discount price cannot be negative.")
            if price is not None and discount_price >= price:
                raise forms.ValidationError("Discount price cannot be greater than or equal to the original price.")

        return discount_price
    
class ContactSellerForm(forms.Form):
    subject = forms.CharField(max_length=120, widget=forms.TextInput(attrs={
        "class": "form-control",
        "placeholder": "Subject",
    }))
    message = forms.CharField(widget=forms.Textarea(attrs={
        "class": "form-control",
        "rows": 5,
        "placeholder": "Write your message…",
    }))

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'review_text', 'review_image']  # Fields for review
    
    rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Rate this product (1-5)"}),
        label="Rating (1-5)"
    )
    review_text = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Write your review here..."}),
        required=False,
        label="Comment"
    )
    review_image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-control-file"}),
        label="Upload Image (optional)"
    )

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating is None or rating < 1 or rating > 5:
            raise forms.ValidationError("Please provide a rating between 1 and 5.")
        return rating  # Corrected typo here
