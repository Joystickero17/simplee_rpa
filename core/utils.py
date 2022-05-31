import logging
from pprint import pprint
import requests
from django.utils.timezone import datetime, now, timedelta
from core.models import Contact, Bidding
from django.conf import settings
import time

API_TOKEN = settings.EXTERNAL_USER_TOKEN
URL =  "http://api.mercadopublico.cl/servicios/v1/Publico/Licitaciones/"
TICKET = "471052E9-58E8-4217-9CAB-7935F177B353"
CATEGORIES = [
    ("72131600", "Construcción comercial o industrial"),
    ("72131700", "Construcción de obras civiles y infraestructuras"),
    ("72131500", "Construcción residencial"),
    ("30201500", "Construcciones agrícolas prefabricadas"),
    ("30201700", "Construcciones comerciales e industriales prefabricadas"),
    ("30221000", "Construcciones comerciales y de recreación"),
    ("30222600", "Construcciones deportivas y sanitarias"),
    ("30222400", "Construcciones hospitalarias"),
    ("30222700", "Construcciones industriales"),
    ("30201900", "Construcciones médicas prefabricadas"),
    ("30222800", "Construcciones para agricultura, pesca y ganadería"),
    ("30222500", "Construcciones para alojamiento"),
    ("30222900", "Construcciones para defensa"),
    ("30222300", "Construcciones para educación e investigación"),
    ("30222200", "Construcciones para servicios"),
    ("30222000", "Construcciones para trasporte permanentes"),
    ("30201800", "Construcciones prefabricadas para emergencias"),
    ("30222100", "Construcciones públicas permanentes"),
    ("30223000", "Construcciones religiosas"),
    ("30201600", "Construcciones residenciales prefabricadas"),
]

def get_biddings():
    for day in range(15):
        date = (now() - timedelta(days=day)).strftime("%d%m%Y")
        print(f"Checking biddings for date {date}")
        response = requests.get(f'{URL}?ticket={TICKET}&fecha={date}&estado=adjudicada')
        
        listado = response.json().get("Listado")
        if not listado:
            print(f"failed to get Biddings in date {date}, reason: {response.json()}")
        get_contacts_from_bidding(listado)
        time.sleep(2)

def get_contacts_from_bidding(bidding_list):
    for bidding in bidding_list:
        time.sleep(2)
        bidding_raw_info = requests.get(f'{URL}?codigo={bidding["CodigoExterno"]}&ticket={TICKET}')        
        bidding_info = bidding_raw_info.json()
        # if bidding_info.get("codigoCategoria") in dict(CATEGORIES).keys():
        adjudications_items = bidding_info.get("Listado")[0]
        if not adjudications_items:
            continue
        adjudication_list = adjudications_items.get("Items").get("Listado")
        adjudication = next((subject for subject in adjudication_list if subject.get("Adjudicacion")), None)
        
        if not adjudication:
            print("No Adjudication")
            continue
        
        contact = adjudication.get("Adjudicacion")
        print(contact, bidding["CodigoExterno"])

        if adjudication["CodigoCategoria"] not in dict(CATEGORIES).keys():
            print(f"{adjudication['CodigoCategoria']} not in interested categories\n")
            continue

        try:
            print("consultando BD")
            providers_rut_colon = contact.get("RutProveedor").replace(".","")
            providers_rut_plain = contact.get("RutProveedor").replace(".","").replace("-","")
            result_contact = Contact.objects.get(rut=providers_rut_plain)
            
            bidding = Bidding(
                adjudicated_date=adjudications_items.get("Fechas").get("FechaAdjudicacion"),
                published_date=adjudications_items.get("Fechas").get("FechaPublicacion"),
                external_code=adjudications_items.get("CodigoExterno"),
                contact=result_contact,
                category_code=adjudication.get("CodigoCategoria") 
            )
            bidding.save()
            print(f"Succesfull Found Contacts for RUT:{providers_rut_colon} \n")
            continue
        except Contact.DoesNotExist as e:
            print(f"RUT {providers_rut_plain} does not exists in the records")

        print(f"Trying to Search in Leads Endpoint, RUT: {providers_rut_colon}")
        headers = {
            "Authorization": f"Bearer {API_TOKEN}"
        }
        raw_response = requests.get(f"http://simplee-drf.herokuapp.com/api/lead/?rut={providers_rut_colon}", headers=headers)
        response = raw_response.json()
        leads_list = response.get("results")
        if leads_list:
            rut = leads_list[0].get("rut").replace(".", "")
            new_contact = Contact.objects.create(
                name=f'{leads_list[0].get("name")} {leads_list[0].get("last_name")}',
                rut= rut,
                phone=leads_list[0].get("phone"),
                email=leads_list[0].get("email")
                )

            bidding = Bidding(
                adjudicated_date=adjudications_items.get("Fechas").get("FechaAdjudicacion"),
                published_date=adjudications_items.get("Fechas").get("FechaPublicacion"),
                external_code=adjudications_items.get("CodigoExterno"),
                contact=new_contact,
                category_code=adjudication.get("CodigoCategoria") 
            )
            bidding.save()
            print(f"Succesfull Found Contacts for RUT:{providers_rut_colon} \n")
        else:
            print(f"Not Found RUT: {providers_rut_colon} \n")


        # if bidding_info.get("codigoCategoria") in dict(CATEGORIES).keys():
        #     yield bidding_info.get("Listado")[0].get("Items").get("Listado")[0]["Adjudicacion"]
        
