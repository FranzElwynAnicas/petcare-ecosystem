from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import UserProfile, ContactMessage 
from .models import AdoptionApplication


# Custom user registration form that extends Django's built-in UserCreationForm
# Adds additional fields for user profile information
class CustomUserCreationForm(UserCreationForm):
    name = forms.CharField(max_length=100, required=True)
    role = forms.ChoiceField(choices=[
        ('adopter', 'Pet Adopter'),
        ('shelter', 'Shelter Staff'),
        ('vet', 'Veterinarian')
    ], required=True)
    gender = forms.ChoiceField(choices=[
        ('', 'Select Gender'),
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], required=False)
    job = forms.CharField(max_length=100, required=False)
    phone = forms.CharField(max_length=20, required=False)
    address = forms.CharField(widget=forms.Textarea, required=True)
    barangay = forms.CharField(max_length=100, required=True)
    city = forms.CharField(max_length=100, required=True)
    province = forms.CharField(max_length=100, required=True)
    zip_code = forms.CharField(max_length=10, required=True)
    country = forms.CharField(max_length=100, required=True, initial='Philippines')
    
    class Meta:
        model = User
        fields = ('username', 'name', 'password1', 'password2', 'role', 'gender', 'job', 'phone', 
                  'address', 'barangay', 'city', 'province', 'zip_code', 'country')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize form field labels and attributes
        self.fields['username'].label = 'Email Address'
        self.fields['country'].widget.attrs['readonly'] = True
    
    def clean_username(self):
        # Validate that username is a valid email address
        username = self.cleaned_data.get('username')
        if username and not '@' in username:
            raise forms.ValidationError('Please enter a valid email address.')
        return username
    
    def save(self, commit=True):
        # Save user data and set email, first name from form data
        user = super().save(commit=False)
        user.email = self.cleaned_data['username']
        user.first_name = self.cleaned_data['name'].split()[0] if self.cleaned_data['name'] else ''
        if commit:
            user.save()
        return user

# Form for editing user profile information
# Handles both User model fields and UserProfile model fields
class EditProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'gender', 'job', 'phone', 'address', 'barangay', 'city', 'province', 'zip_code', 'country']
    
    def __init__(self, *args, **kwargs):
        # Extract user instance from kwargs and set initial values
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set initial values for first_name and last_name from User model
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
    
    def save(self, commit=True):
        # Save both User and UserProfile data
        profile = super().save(commit=False)
        
        # Update User model fields
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            if commit:
                self.user.save()
        
        if commit:
            profile.save()
        
        return profile

# Custom password change form that adds Bootstrap styling
class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all form fields for consistent styling
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

# Contact form
class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['first_name', 'last_name', 'email', 'phone', 'subject', 'message', 'newsletter_subscription']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Tell us how we can help you...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all fields
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class AdoptionApplicationForm(forms.ModelForm):
    class Meta:
        model = AdoptionApplication
        fields = [
            'applicant_name', 'applicant_email', 'applicant_phone', 'applicant_address',
            'family_members', 'previous_pets', 'home_type', 'yard_info', 
            'work_schedule', 'pet_alone_time', 'vet_contact', 'references', 'message'
        ]
        widgets = {
            'applicant_address': forms.Textarea(attrs={'rows': 3}),
            'family_members': forms.Textarea(attrs={'rows': 2}),
            'previous_pets': forms.Textarea(attrs={'rows': 3}),
            'yard_info': forms.Textarea(attrs={'rows': 2}),
            'work_schedule': forms.Textarea(attrs={'rows': 2}),
            'pet_alone_time': forms.Textarea(attrs={'rows': 2}),
            'vet_contact': forms.Textarea(attrs={'rows': 2}),
            'references': forms.Textarea(attrs={'rows': 3}),
            'message': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'applicant_name': 'Full Name',
            'applicant_email': 'Email Address',
            'applicant_phone': 'Phone Number',
            'applicant_address': 'Complete Address',
            'family_members': 'Family/Household Members',
            'previous_pets': 'Previous Pet Experience',
            'home_type': 'Type of Home',
            'yard_info': 'Yard/Outdoor Space',
            'work_schedule': 'Work Schedule',
            'pet_alone_time': 'Daily Alone Time for Pet',
            'vet_contact': 'Veterinarian Information',
            'references': 'Personal References',
            'message': 'Why do you want to adopt this pet?',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all fields
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})