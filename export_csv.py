import csv
from pprint import pprint
from core.models import Contact
def return_activity():
    with open("pymes.csv", encoding='utf-8') as f:
        csv_reader = csv.reader(f, delimiter=";")
        for row in csv_reader:
            yield row[3]

def upload_from_csv_to_db():
    with open("pymes.csv", encoding='utf-8') as f:
        csv_reader = csv.reader(f, delimiter=";")
        count = 0
        for row in csv_reader:
            try:
                contact = Contact.objects.get(rut=row[1])
            except Contact.DoesNotExist as e:
                contact = Contact()
                contact.rut=row[1]
                contact.name=row[0] 
                contact.activity=row[3] 
                contact.phone=row[14]
                contact.email=row[16]
                contact.save()
                count += 1
                print(count)
