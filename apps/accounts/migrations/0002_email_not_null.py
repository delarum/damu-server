from django.db import migrations, models
import django.core.validators


def populate_email(apps, schema_editor):
    """Populate email for existing users with a placeholder."""
    User = apps.get_model('accounts', 'User')
    # First, handle null emails
    for user in User.objects.filter(email__isnull=True):
        user.email = f"user_{user.id}@placeholder.damulink.co.ke"
        user.save()
    
    # Then, handle duplicate emails by appending user ID
    seen_emails = {}
    for user in User.objects.all().order_by('id'):
        if user.email in seen_emails:
            # Duplicate found, make it unique
            base_email = user.email.split('@')[0]
            domain = user.email.split('@')[1]
            user.email = f"{base_email}_{user.id}@{domain}"
            user.save()
        else:
            seen_emails[user.email] = True


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        # First, populate email for existing users
        migrations.RunPython(populate_email, reverse_code=migrations.RunPython.noop),
        # Then alter the field to be non-nullable
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=254, unique=True),
        ),
    ]