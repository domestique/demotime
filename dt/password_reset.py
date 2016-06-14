from django.contrib.auth.models import User; [(user.set_password('justtestit'), user.save()) for user in User.objects.all()]
