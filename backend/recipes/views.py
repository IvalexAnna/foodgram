from api import constants
from django.http import Http404
from django.shortcuts import redirect
from recipes.models import Recipe


def recipe_redirect(request, pk):
    if Recipe.objects.filter(pk=pk).exists():
        return redirect(f"/recipes/{pk}")
    return Http404(constants.RECIPE_NOT_FOUND.format(pk))
