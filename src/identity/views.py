from django.shortcuts import render, redirect

from .models import Identity
from .forms import IdentityForm

def identity_edit(request):
    identity, created = Identity.objects.get_or_create(pk=1)
    if request.method == 'POST':
        form = IdentityForm(request.POST, instance=identity)
        if form.is_valid():
            form.save()
            return redirect('identity_edit')
    else:
        form = IdentityForm(instance=identity)
    return render(request, 'identity/edit.html', {'form': form})