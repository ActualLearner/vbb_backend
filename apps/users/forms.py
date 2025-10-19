from django import forms
from django.contrib.auth import get_user_model

from .models import Facility

User = get_user_model()


class CustomSignupAddonForm(forms.Form):
    """
    This is the add-on form for the django-allauth signup process,
    as specified by the ACCOUNT_SIGNUP_FORM_CLASS setting. It handles
    the custom 'role' field.
    """

    # Use a ChoiceField that gets its options directly from the User model.
    # This is more robust than a hardcoded list.
    role = forms.ChoiceField(choices=User.Role.choices, required=False)
    facility = forms.ModelChoiceField(
        queryset=Facility.objects.all(),
        required=True,
        error_messages={
            "required": "You must select a facility.",
            "invalid_choice": "The selected facility does not exist.",
        },
    )
    # We don't need a custom clean_role method anymore because
    # the ChoiceField handles the validation for us.

    def clean(self):
        """
        Override the clean method to assign a default value to the role
        if one isn't provided.
        """
        cleaned_data = super().clean()
        if not cleaned_data.get("role"):
            # Set the default role if none was selected.
            cleaned_data["role"] = (
                User.Role.FACILITY_REPRESENTATIVE
            )  # Or whichever you prefer as default
        return cleaned_data

    def signup(self, request, user):
        """
        This method is called after the user is created by the main allauth form.
        We are passed the new user instance and can now save our
        additional data to it.
        """
        user.role = self.cleaned_data["role"]
        user.facility = self.cleaned_data["facility"]
        user.save()
        return user
