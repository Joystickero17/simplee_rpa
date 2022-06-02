from core.utils import get_biddings, get_contacts_from_bidding, get_simplee_token, requests, search_contact_in_csv


#print(search_contact_in_csv("77921930"))

token = get_simplee_token()
bidding_list = get_biddings()
print(len(bidding_list))
get_contacts_from_bidding(bidding_list, token)