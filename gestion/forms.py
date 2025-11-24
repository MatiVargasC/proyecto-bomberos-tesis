from django import forms
from django.contrib.auth.models import User
from .models import Bombero


class BomberoCreationForm(forms.Form):
    username = forms.CharField(max_length=150, label='Usuario (username)',
                               widget=forms.TextInput(attrs={'class':'form-control'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control'}), label='Contraseña')
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control'}), label='Confirmar contraseña')
    email = forms.EmailField(required=False, label='Correo electrónico',
                             widget=forms.EmailInput(attrs={'class':'form-control'}))
    rut = forms.CharField(max_length=12, label='RUT', widget=forms.TextInput(attrs={'class':'form-control'}))
    nombre = forms.CharField(max_length=100, label='Nombre completo', widget=forms.TextInput(attrs={'class':'form-control'}))
    rol = forms.ChoiceField(choices=Bombero._meta.get_field('rol').choices, label='Rol',
                            widget=forms.Select(attrs={'class':'form-select'}))

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('El nombre de usuario ya existe.')
        return username

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned

    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        if Bombero.objects.filter(rut=rut).exists():
            raise forms.ValidationError('El RUT ya está registrado.')
        return rut


class GuardiaForm(forms.ModelForm):
    class Meta:
        from .models import Guardia
        model = Guardia
        fields = ['fecha', 'tipo', 'hora_inicio', 'hora_fin', 'herramientas', 'apoyo_externo', 'lugar']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'tipo': forms.TextInput(attrs={'class': 'form-control'}),
            'herramientas': forms.TextInput(attrs={'class': 'form-control'}),
            'apoyo_externo': forms.TextInput(attrs={'class': 'form-control'}),
            'lugar': forms.TextInput(attrs={'class': 'form-control'}),
        }
