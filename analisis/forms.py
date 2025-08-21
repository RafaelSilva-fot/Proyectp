
from django import forms
from .models import TextoAnalizado

class TextoAnalizadoForm(forms.ModelForm):
    class Meta:
        model = TextoAnalizado
        fields = ['titulo', 'archivo']

    def clean_archivo(self):
        f = self.cleaned_data['archivo']
        if not f.name.lower().endswith('.txt'):
            raise forms.ValidationError('Solo se permiten archivos .txt.')
        return f
