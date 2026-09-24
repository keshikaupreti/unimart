from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("chat", "0001_initial")]
    operations = [
        migrations.AddField(model_name="conversation", name="buyer_archived", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="conversation", name="seller_archived", field=models.BooleanField(default=False)),
    ]
