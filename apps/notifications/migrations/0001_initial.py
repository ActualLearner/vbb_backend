from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("users", "0001_initial"),
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificationEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(max_length=64)),
                ("payload", models.JSONField()),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("dispatched", models.BooleanField(default=False)),
                ("facility", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="notification_events", to="users.facility")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="NotificationRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("read", models.BooleanField(default=False)),
                ("delivered_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("event", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="records", to="notifications.notificationevent")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="users.user")),
            ],
            options={"ordering": ["-delivered_at"]},
        ),
    ]
