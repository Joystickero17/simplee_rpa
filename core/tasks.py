from celery import shared_task
import requests

from core.utils import get_biddings, get_contacts_from_bidding, get_simplee_token
from core.models import Bidding
from core.services.active_campaing import sync_contact

@shared_task
def check_bidding_list():
    token = get_simplee_token()
    bidding_list = get_biddings()
    get_contacts_from_bidding(bidding_list, token)


@shared_task
def send_biddings_to_active_campaing():
    biddings = Bidding.objects.filter(sended_to_ac=False)
    for bidding in biddings:
        sync_contact(email=bidding.contact.email, first_name=bidding.contact.name, phone=bidding.contact.phone)
        print(f"{bidding.contact.email} with bidding code {bidding.external_code} has been sent to Active Campaing")
        bidding.sended_to_ac = True
        bidding.save()

