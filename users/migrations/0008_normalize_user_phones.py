import re

from django.db import migrations


def phones_to_eight(apps, schema_editor):
    User = apps.get_model('users', 'User')
    for user in User.objects.all():
        digits = re.sub(r'\D', '', user.phone or '')
        if len(digits) == 11 and digits.startswith('7'):
            digits = '8' + digits[1:]
        if not (len(digits) == 11 and digits.startswith('8')):
            continue
        if user.phone == digits:
            continue
        if User.objects.filter(phone=digits).exclude(pk=user.pk).exists():
            raise RuntimeError(
                f'Нельзя привести телефон пользователя id={user.pk} ({user.phone}) '
                f'к {digits}: такой номер уже есть'
            )
        user.phone = digits
        user.save(update_fields=['phone'])


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_activitylog'),
    ]

    operations = [
        migrations.RunPython(phones_to_eight, migrations.RunPython.noop),
    ]
