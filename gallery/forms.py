from django import forms

from .models import Comment, ContactRequest, Review


class ContactRequestForm(forms.ModelForm):
    class Meta:
        model = ContactRequest
        fields = ["name", "email", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ваше имя"}),
            "email": forms.EmailInput(attrs={"placeholder": "name@example.com"}),
            "message": forms.Textarea(attrs={"rows": 6, "placeholder": "Ваше сообщение"}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "text"]
        widgets = {
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5}),
            "text": forms.Textarea(attrs={"rows": 5}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]
        widgets = {"text": forms.Textarea(attrs={"rows": 5})}
