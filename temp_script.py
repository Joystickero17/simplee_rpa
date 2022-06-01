from core.utils import get_biddings, get_contacts_from_bidding, get_simplee_token, requests

token = get_simplee_token()
bidding_list = get_biddings()
print(len(bidding_list))
get_contacts_from_bidding(bidding_list, token)