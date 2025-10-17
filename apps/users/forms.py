from django import forms
from django.core.exceptions import ValidationError


class CustomSignupAddonForm(forms.Form):
    """
    This is an add-on form for the signup process, as documented by
    the ACCOUNT_SIGNUP_FORM_CLASS setting. It handles any fields
    beyond what the default allauth form handles.
    """

    role = forms.CharField(max_length=15, required=False)

    def clean_role(self):
        ROLES = {"admin", "manager", "member"}

        role = self.cleaned_data.get("role")
        if role not in ROLES:
            raise ValidationError("Invalid Role")

        return role

    # Override clean method to assign default value to role
    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data.get("role"):
            cleaned_data["role"] = "member"

        return cleaned_data

    def signup(self, request, user):
        """
        This method is called after the user is created by the main form.
        We are passed the new user instance and can now save our
        additional data to it.
        """
        user.role = self.cleaned_data["role"]
        user.save()
        return user
