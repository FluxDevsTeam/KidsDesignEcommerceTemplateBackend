# this is for namecheap server as ssh might be slow. so this script can just handle the superuser creation
import os
import sys
from dotenv import load_dotenv
import django

load_dotenv()


def main():
    DJANGO_ENV = os.getenv("DJANGO_ENV", "development").lower()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"config.settings.{DJANGO_ENV}")

    try:
        from django.core.management import call_command
        from django.contrib.auth import get_user_model
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    django.setup()

    print("Running makemigrations...")
    try:
        call_command('makemigrations')
        print("Makemigrations completed")
    except Exception as e:
        print(f"Makemigrations failed: {str(e)}")
        sys.exit(1)

    print("Running migrate...")
    try:
        call_command('migrate')
        print("Migrate completed")
    except Exception as e:
        print(f"Migrate failed: {str(e)}")
        sys.exit(1)

    print("Creating superuser...")
    User = get_user_model()
    email = 'example@gmail.com'
    password = 'adminpassword'

    if not User.objects.filter(email=email).exists():
        try:
            User.objects.create_superuser(
                email=email,
                password=password,
            )
            print("Superuser created successfully")
        except Exception as e:
            print(f"Superuser creation failed: {str(e)}")
            sys.exit(1)
    else:
        print("Superuser already exists")


if __name__ == "__main__":
    main()
