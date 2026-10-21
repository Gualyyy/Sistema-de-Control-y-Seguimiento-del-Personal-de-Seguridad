from django.shortcuts import render

# Vistas del foro

def foro(request):
    return render(request, "Foro/foro.html")

def historia(request):
    return render(request, "Foro/historia.html")

def quienes_somos(request):
    return render(request, "Foro/quienes_somos.html")

def contactanos(request):
    return render(request, "Foro/contactanos.html")
