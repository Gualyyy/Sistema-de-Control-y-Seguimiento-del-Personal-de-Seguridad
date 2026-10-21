from django.contrib import admin, messages
from django import forms
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from .models import usuarios, contacto, credenciales, directiva_nacional, encargados_administrativos, supervisores_encargados, personal_limpieza, despachadores, vigilantes

class UsuariosForm(forms.ModelForm):

    nacionalidad = forms.ChoiceField(
        label="Nacionalidad",
        choices=[
            ("", "N"),
            ("V", "V"),
            ("E", "E"),
        ],
        required=True
    )

    class Meta:
        model = usuarios
        fields = "__all__"

        widgets = {
            "nombres": forms.TextInput(
                attrs={
                    "placeholder": "Ingrese los nombres",
                    "minlength": "3",
                    "maxlength": "20",
                    "required": True,
                }
            ),

            "apellidos": forms.TextInput(
                attrs={
                    "placeholder": "Ingrese los apellidos",
                    "minlength": "3",
                    "maxlength": "20",
                    "required": True,
                }
            ),

            "genero": forms.Select(
                choices=[
                    ("", "Genero"),
                    ("Masculino", "Masculino"),
                    ("Femenino", "Femenino"),
                ],
                attrs={
                    "required": True,
                }
            ),

            "estado_civil": forms.Select(
                choices=[
                    ("", "Estado Civil"),
                    ("Soltero", "Soltero"),
                    ("Casado", "Casado"),
                    ("Divorciado", "Divorciado"),
                    ("Viudo", "Viudo"),
                ],
                attrs={
                    "required": True,
                }
            ),

            "cedula_identidad": forms.TextInput(
                attrs={
                    "id": "id_cedula_identidad",
                    "placeholder": "Ingrese la cédula",
                    "required": True,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.cedula_identidad:

            cedula = self.instance.cedula_identidad

            if "-" in cedula:
                nacionalidad, numero = cedula.split("-", 1)

                self.fields["nacionalidad"].initial = nacionalidad
                self.initial["nacionalidad"] = nacionalidad
                self.initial["cedula_identidad"] = numero

@admin.register(usuarios)
class UsuariosAdmin(admin.ModelAdmin):

    form = UsuariosForm

    fieldsets = (
        ("Información personal", {
            "fields": (
                "nombres",
                "apellidos",
                ("nacionalidad", "cedula_identidad"),
                "genero",
                "estado_civil",
            )
        }),
    )

    list_display = (
        "id_usuario",
        "nombres",
        "apellidos",
        "cedula_identidad",
        "genero",
        "estado_civil",
        "mostrar_usuario",
    )

    def mostrar_usuario(self, obj):
        try:
            return obj.credenciales.nombre_usuario
        except credenciales.DoesNotExist:
            return "Sin credenciales"

    mostrar_usuario.short_description = "Usuario"

    def save_model(self, request, obj, form, change):

        nacionalidad = form.cleaned_data.get("nacionalidad")
        cedula = form.cleaned_data.get("cedula_identidad")

        if nacionalidad and cedula:
            obj.cedula_identidad = f"{nacionalidad}-{cedula}"

        super().save_model(request, obj, form, change)

        if change:
            messages.success(
                request,
                "Usuario actualizado correctamente."
            )
        else:
            messages.success(
                request,
                "Usuario registrado correctamente."
            )

class CredencialesForm(forms.ModelForm):

    class Meta:
        model = credenciales
        fields = (
            "nombre_usuario",
            "clave",
        )

        widgets = {
            "nombre_usuario": forms.TextInput(
                attrs={
                    "placeholder": "Ingrese el usuario",
                    "minlength": "3",
                    "maxlength": "10",
                    "required": True,
                }
            ),

            "clave": forms.PasswordInput(
                attrs={
                    "id": "id_clave",
                    "placeholder": "Ingrese la contraseña",
                    "minlength": "3",
                    "maxlength": "10",
                    "required": True,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["nombre_usuario"].required = True
        self.fields["clave"].required = True

    def save(self, commit=True):
        obj = super().save(commit=False)

        if self.cleaned_data["clave"]:
            obj.clave = make_password(self.cleaned_data["clave"])

        if commit:
            obj.save()

        return obj

@admin.register(credenciales)
class CredencialesAdmin(admin.ModelAdmin):

    form = CredencialesForm

    fieldsets = (
        ("Credenciales de acceso", {
            "fields": (
                "id_usuario",
                "nombre_usuario",
                "clave",
            )
        }),
    )

    list_display = (
        "id_credenciales",
        "nombre_usuario",
        "id_usuario",
    )

    search_fields = (
        "nombre_usuario",
        "id_usuario__nombres",
        "id_usuario__apellidos",
        "id_usuario__cedula_identidad",
    )

class TelefonoWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        widgets = [
            forms.Select(
                choices=[
                    ("", "TLF"),
                    ("0414", "0414"),
                    ("0424", "0424"),
                    ("0416", "0416"),
                    ("0426", "0426"),
                    ("0412", "0412"),
                    ("0422", "0422"),
                ],
                attrs={
                    "class": "prefijo-telefono"
                }
            ),

            forms.TextInput(
                attrs={
                    "class": "numero-telefono",
                    "placeholder": "Seleccione primero el prefijo",
                    "maxlength": "7",
                    "minlength": "7",
                    "disabled": "disabled"
                }
            )
        ]

        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [
                value[:4],
                value[4:]
            ]

        return [
            "",
            ""
        ]

class CorreoWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        widgets = [
            forms.TextInput(
                attrs={
                    "placeholder": "Correo",
                    "maxlength": "20",
                    "minlength": "10",
                }
            ),
            forms.Select(
                choices=[
                    ("", "DOMINIO"),
                    ("@gmail.com", "@gmail.com"),
                    ("@outlook.com", "@outlook.com"),
                    ("@yahoo.com", "@yahoo.com"),
                ]
            )
        ]
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            correo, dominio = value.split("@")
            return [
                correo,
                "@" + dominio
            ]
        return [
            "",
            ""
        ]

class ContactoAdminForm(forms.ModelForm):
    telefono_principal = forms.MultiValueField(
        fields=[
            forms.CharField(),
            forms.CharField(max_length=7, min_length=7)
        ],
        widget=TelefonoWidget()
    )

    telefono_secundario = forms.MultiValueField(
        fields=[
            forms.CharField(),
            forms.CharField(max_length=7, min_length=7)
        ],
        required=False,
        widget=TelefonoWidget()
    )

    correo_principal = forms.MultiValueField(
        fields=[
            forms.CharField(max_length=20, min_length=10),
            forms.CharField()
        ],
        widget=CorreoWidget()
    )

    correo_secundario = forms.MultiValueField(
        fields=[
            forms.CharField(max_length=20, min_length=10, required=False),
            forms.CharField()
        ],
        required=False,
        widget=CorreoWidget()
    )

    class Meta:
        model = contacto
        fields = [
            "id_usuario",
            "telefono_principal",
            "telefono_secundario",
            "correo_principal",
            "correo_secundario",
        ]

@admin.register(contacto)
class ContactoAdmin(admin.ModelAdmin):
    form = ContactoAdminForm

    list_display = (
        "id_contacto",
        "id_usuario",
        "telefono_principal",
        "telefono_secundario",
        "correo_principal",
        "correo_secundario",
    )

    fieldsets = (
        (
            "Información del usuario",
            {
                "fields": (
                    "id_usuario",
                )
            }
        ),
        (
            "Teléfonos",
            {
                "fields": (
                    "telefono_principal",
                    "telefono_secundario",
                )
            }
        ),

        (
            "Correos electrónicos",
            {
                "fields": (
                    "correo_principal",
                    "correo_secundario",
                )
            }
        ),
    )


# Register your models here.
admin.site.register(directiva_nacional)
admin.site.register(encargados_administrativos)
admin.site.register(supervisores_encargados)
admin.site.register(personal_limpieza)
admin.site.register(despachadores)
admin.site.register(vigilantes)