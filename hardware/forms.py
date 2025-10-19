from __future__ import annotations

from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(label="Nume", max_length=120)
    email = forms.EmailField(label="Email")
    message = forms.CharField(label="Mesaj", widget=forms.Textarea)
