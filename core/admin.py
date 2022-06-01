from django.contrib import admin
from core.models import Contact, Bidding
# Register your models here.

class BiddingAdmin(admin.ModelAdmin):
    list_display = ("external_code", "contact_email", "sended_to_ac")

    def contact_email(self, obj):
        return f"{obj.contact.email}"

admin.site.register(Contact)
admin.site.register(Bidding, BiddingAdmin)