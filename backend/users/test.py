from django.conf import settings
from django.contrib.auth import authenticate

user = authenticate(email='test@test.com', password='QWE123qwe')

if user is not None:
    print("Аутентификация успешна")
else:
    print("Аутентификация не удалась")