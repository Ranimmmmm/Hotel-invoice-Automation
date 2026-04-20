
DEFAULT_CLIENT_COL = "Kunden"
DEFAULT_DUE_COL = "Hotelleistung Reisebeginn"
DEFAULT_TO_COL = "Hotelleistung Reiseende"
DEFAULT_HOTEL_COL = "Hotelleistung Leistungsbeschreibung"

OUTPUT_LOG = "hotel_search_log.csv"


REQUEST_HEADERS = {
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


BLACKLIST_DOMAINS = [
"booking.com", "tripadvisor", "expedia", "hotels.com", "agoda.com",
"kayak.com", "facebook.com", "instagram.com", "yelp.com"
]


CONTACT_PATHS = [
"/contact", "/contact-us", "/contactus", "/contacts",
"/en/contact", "/en/contact-us"
]