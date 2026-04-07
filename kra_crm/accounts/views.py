from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('dashboard')   #  FIXED
        else:
            return render(request, 'accounts/login.html', {
                'error': 'Invalid credentials'
            })

    return render(request, 'accounts/login.html')


#def user_login(request):
#    if request.method == 'POST':
#        username = request.POST['username']
#        password = request.POST['password']

#        user = authenticate(request, username=username, password=password)

#        if user:
#            login(request, user)
#
#            #  ROLE BASED REDIRECT
#            if user.is_superuser:
 #               return redirect('admin_dashboard')
 #           else:
 #               return redirect('employee_dashboard')
#
 #       else:
 #           return render(request, 'accounts/login.html', {
 #               'error': 'Invalid credentials'
 #           })

    return render(request, 'accounts/login.html')