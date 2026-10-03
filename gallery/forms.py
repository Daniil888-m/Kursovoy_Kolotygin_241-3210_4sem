from django import forms

from .models import ContactRequest


class ContactRequestForm(forms.ModelForm):
    class Meta:
        model = ContactRequest
        fields = ["name", "email", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ваше имя"}),
            "email": forms.EmailInput(attrs={"placeholder": "name@example.com"}),
            "message": forms.Textarea(attrs={"rows": 6, "placeholder": "Ваше сообщение"}),
        }
