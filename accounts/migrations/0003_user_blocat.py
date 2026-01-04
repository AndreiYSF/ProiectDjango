from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_email_confirm_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="blocat",
            field=models.BooleanField(default=False),
        ),
    ]
