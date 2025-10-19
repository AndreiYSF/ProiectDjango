from django.http import HttpResponse
from django.shortcuts import render

def home(request):
    return HttpResponse(
        """
        <h1>Welcome to my Django app!</h1>
        <p>This is the home page, powered by Django.</p>
        """
    )