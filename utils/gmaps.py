import os
import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def query_google_maps(query, location=None, max_results=5):
    full_query = f"{query} in {location}" if location else query
    if not GOOGLE_API_KEY:
        return {"message": "Missing Google Maps API Key"}

    endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": full_query,
        "key": GOOGLE_API_KEY
    }

    response = requests.get(endpoint, params=params)
    if response.status_code != 200:
        return {"message": "Failed to contact Google Maps"}

    data = response.json()
    if data.get("status") != "OK" or not data.get("results"):
        return {"message": "No results found", "raw": data}

    results = []
    for item in data["results"][:max_results]:
        name = item.get("name")
        address = item.get("formatted_address")
        location_data = item.get("geometry", {}).get("location", {})
        lat = location_data.get("lat")
        lng = location_data.get("lng")
        place_id = item.get("place_id")
        map_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}" if lat and lng else ""

        results.append({
            "name": name,
            "address": address,
            "location": location_data,
            "place_id": place_id,
            "maps_url": map_url
        })

    return results

def get_direction(origin: str, destination: str):
    if not GOOGLE_API_KEY:
        return {"message": "Missing Google Maps API Key"}

    endpoint = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "key": GOOGLE_API_KEY
    }

    response = requests.get(endpoint, params=params)
    if response.status_code != 200:
        return {"message": "Failed to contact Google Maps"}

    data = response.json()
    if data.get("status") != "OK" or not data.get("routes"):
        return {"message": "No route found", "raw": data}

    route = data["routes"][0]
    legs = route.get("legs", [])[0]

    # Encode untuk URL link ke Google Maps
    from urllib.parse import quote_plus
    maps_url = (
        "https://www.google.com/maps/dir/?api=1"
        f"&origin={quote_plus(origin)}"
        f"&destination={quote_plus(destination)}"
    )

    return {
        "summary": route.get("summary"),
        "distance": legs.get("distance", {}).get("text"),
        "duration": legs.get("duration", {}).get("text"),
        "start_address": legs.get("start_address"),
        "end_address": legs.get("end_address"),
        "steps": [
            {
                "instruction": step["html_instructions"],
                "distance": step["distance"]["text"],
                "duration": step["duration"]["text"]
            }
            for step in legs.get("steps", [])
        ],
        "maps_url": maps_url
    }
