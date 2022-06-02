from django.db import models

# Create your models here.

class Contact(models.Model):
    name = models.CharField(max_length=255)
    rut = models.CharField(max_length=255, unique=True)
    email = models.EmailField(null=True)
    phone = models.CharField(max_length=255, null=True)
    activity = models.CharField(max_length=255)

class Bidding(models.Model):
    adjudicated_date = models.DateTimeField(null=True)
    published_date = models.DateTimeField(null=True)
    external_code = models.CharField(max_length=255, unique=True)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    category_code = models.CharField(max_length=255)
    activity = models.CharField(max_length=255)
    mercadopublico_url = models.CharField(max_length=255)
    sended_to_ac = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.mercadopublico_url = f'http://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?idlicitacion={self.external_code}'
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.external_code}"
    