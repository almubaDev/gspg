from django import forms
from gspg.models import ActaReunion

class ActaReunionForm(forms.ModelForm):
    class Meta:
        model = ActaReunion
        fields = ["archivo"]