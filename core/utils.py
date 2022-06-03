import csv
from pprint import pprint
import requests
from django.utils.timezone import datetime, now, timedelta
from core.models import Contact, Bidding
from bs4 import BeautifulSoup
import time


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

def search_contact_in_csv(rut):
    with open("pymes.csv", encoding='utf-8') as f:
        csv_reader = csv.reader(f, delimiter=";")
        contact_result = next((row for row in csv_reader if row[1] == rut), None)
        if contact_result:
            contact = {
            "rut": contact_result[1],
            "name": contact_result[0],
            "activity": contact_result[3],
            "phone": contact_result[14],
            "email": contact_result[16],
            }
            return contact

def get_simplee_token():
    payload = {"email":"prueba@simplee.cl", "password":"27853607"}
    response = requests.post("https://simplee-drf.herokuapp.com/api/auth/login/", data=payload)
    if response.status_code == 201:
        return response.json()["token"]

def get_biddings():
    today = now().isoformat()[:-9]+'Z'
    biddings_codes = []
    results = 0
    total_pages = 0
    page = 1
    date = (now() - timedelta(days=15)).isoformat()[:-9]+'Z'
    while True:
        payload = {
            'codigoRegion': "-1",
            'compradores': [],
            'esPublicoMontoEstimado': None,
            'fechaFin': today,
            'fechaInicio': date,
            'garantias': None,
            'idEstado': "8",
            'idOrden': "1",
            'idTipoFecha': [],
            'idTipoLicitacion': "-1",
            'montoEstimadoTipo': [0],
            'pagina': page,
            'proveedores': [],
            'registrosPorPagina': "10",
            'rubros': list(dict(CATEGORIES).keys()),
            'textoBusqueda': ""
            }
        #pprint(payload)
        response = requests.post("https://www.mercadopublico.cl/BuscarLicitacion/Home/Buscar", data=payload)
        soup = BeautifulSoup(response.text, features="html.parser")
        result_span = soup.find("span", {"class": "n-result"})
        if result_span:
            results = int(result_span.text)
            total_pages = results / 10
        if page >= total_pages:
            break
        else:
            page += 1
        print(f"results of scraping:{results} page:{page} date range: {now().date()} - {date}")
        raw_spans = soup.find_all("span", {"class":"clearfix"}, partial=False)
        spans = [tag.text.strip() for tag in raw_spans if tag.get("class") == ["clearfix"] and tag.text.strip() not in biddings_codes]
        # if not spans:
        #     break
        biddings_codes.extend(spans)
    return list(set(biddings_codes))
        

def get_contacts_from_bidding(bidding_list, user_token=None):
    for bidding in bidding_list:
        time.sleep(2)
        bidding_raw_info = requests.get(f'{URL}?codigo={bidding}&ticket={TICKET}')        
        bidding_info = bidding_raw_info.json()
        # if bidding_info.get("codigoCategoria") in dict(CATEGORIES).keys():
        bidding_results = bidding_info.get("Listado")
        if not bidding_results:
            continue
        adjudications_items = bidding_results[0]
        adjudication_list = adjudications_items.get("Items").get("Listado")
        adjudication = next((subject for subject in adjudication_list if subject.get("Adjudicacion")), None)
        
        if not adjudication:
            print("No Adjudication")
            continue
        
        contact = adjudication.get("Adjudicacion")
        print(contact, bidding)

        if adjudication["CodigoCategoria"] not in dict(CATEGORIES).keys():
            print(f"{adjudication['CodigoCategoria']} not in interested categories\n")
            continue

        print("consultando BD")
        providers_rut_colon = contact.get("RutProveedor").replace(".","")
        providers_rut_plain = contact.get("RutProveedor").replace(".","").replace("-","")
        
        result_contact = search_contact_in_csv(providers_rut_plain)
        if result_contact:
            try:
                existing_contact = Contact.objects.get(rut=providers_rut_plain)
            except Contact.DoesNotExist as b:
                existing_contact = None
            
            if not existing_contact:
                existing_contact = Contact(**result_contact)
                existing_contact.save()
                print(f"Succesfull Found Contacts for RUT:{providers_rut_colon} \n")
            
            try:
                bidding = Bidding.objects.get(external_code=adjudications_items.get("CodigoExterno"))
            except Bidding.DoesNotExist as b:
                bidding = None

            if not bidding:
                bidding = Bidding(
                    adjudicated_date=adjudications_items.get("Fechas").get("FechaAdjudicacion"),
                    published_date=adjudications_items.get("Fechas").get("FechaPublicacion"),
                    external_code=adjudications_items.get("CodigoExterno"),
                    contact=result_contact,
                    category_code=adjudication.get("CodigoCategoria"),
                    activity=adjudication.get("Categoria")
                )
                bidding.save()
                continue
        else:
            print(f"RUT {providers_rut_plain} does not exists in the records, neither CSV nor DB.")
        

        print(f"Trying to Search in Leads Endpoint, RUT: {providers_rut_colon}")
        headers = {
            "Authorization": f"Bearer {user_token}"
        }
        raw_response = requests.get(f"http://simplee-drf.herokuapp.com/api/lead/?rut={providers_rut_colon}", headers=headers)
        response = raw_response.json()
        leads_list = response.get("results")
        if leads_list:
            rut = leads_list[0].get("rut")
            try:
                new_contact = Contact.objects.get(rut=rut)
            except Contact.DoesNotExist as e:
                new_contact = None
                 
            try:
                bidding = Bidding.objects.get(external_code=adjudications_items.get("CodigoExterno"))
            except Bidding.DoesNotExist as b:
                bidding = None


            if not new_contact:
                new_contact = Contact.objects.create(
                    name=f'{leads_list[0].get("name")} {leads_list[0].get("last_name")}',
                    rut= rut,
                    phone=leads_list[0].get("phone"),
                    email=leads_list[0].get("email")
                    )

            if not bidding:
                bidding = Bidding(
                    adjudicated_date=adjudications_items.get("Fechas").get("FechaAdjudicacion"),
                    published_date=adjudications_items.get("Fechas").get("FechaPublicacion"),
                    external_code=adjudications_items.get("CodigoExterno"),
                    contact=new_contact,
                    category_code=adjudication.get("CodigoCategoria"),
                    activity=adjudication.get("Categoria"), 
                )
                bidding.save()
            print(f"Succesfull Found Contacts for RUT:{providers_rut_colon} \n")
        else:
            print(f"Not Found RUT: {providers_rut_colon} \n")


        # if bidding_info.get("codigoCategoria") in dict(CATEGORIES).keys():
        #     yield bidding_info.get("Listado")[0].get("Items").get("Listado")[0]["Adjudicacion"]
        
