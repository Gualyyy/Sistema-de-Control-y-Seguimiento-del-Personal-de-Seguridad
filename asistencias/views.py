from django.shortcuts import render

# Create your views here.
def registrar_asistencia(request):
    return render(request, "registrar_asistencia.html")