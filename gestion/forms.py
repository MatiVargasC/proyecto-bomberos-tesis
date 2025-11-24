from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Bombero  # Asegúrate de que tu modelo se llame Bombero

class RegistroBomberoForm(UserCreationForm):
    rut = forms.CharField(
        max_length=12,
        required=True,
        label="RUT",
        help_text="Ejemplo: 12.345.678-9"
    )
    nombre_completo = forms.CharField(
        max_length=100,
        required=True,
        label="Nombre completo"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'rut', 'nombre_completo']
        labels = {
            'username': 'Usuario',
            'email': 'Correo electrónico (opcional)',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email', '')
        if commit:
            user.save()
            # Crea o actualiza el perfil del bombero
            Bombero.objects.update_or_create(
                user=user,
                defaults={
                    'rut': self.cleaned_data['rut'],
                    'nombre_completo': self.cleaned_data['nombre_completo'],
                }
            )
        return user
