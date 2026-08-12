from django import forms
from .models import Participant

class ParticipantRegistrationForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ['name', 'email', 'roll_number']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Rahul Sharma',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. rahul@college.edu',
                'required': True,
            }),
            'roll_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 23CSE101',
                'required': True,
            }),
        }

    def clean_roll_number(self):
        roll_number = self.cleaned_data.get('roll_number', '').strip().upper()
        if not roll_number:
            raise forms.ValidationError("Roll number is required.")

        # Check for duplicate roll number (case-insensitive check)
        instance_pk = self.instance.pk if self.instance else None
        existing = Participant.objects.filter(roll_number__iexact=roll_number)
        if instance_pk:
            existing = existing.exclude(pk=instance_pk)

        if existing.exists():
            raise forms.ValidationError("A participant with this Roll Number is already registered.")
            
        return roll_number

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError("Name is required.")
        return name

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise forms.ValidationError("Email is required.")
        return email
