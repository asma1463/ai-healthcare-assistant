import math
import requests


class OSMPlacesError(RuntimeError):
    pass


def _distance_km(origin, destination):
    if not origin or not destination:
        return None

    lat1, lon1 = map(math.radians, origin)
    lat2, lon2 = map(math.radians, destination)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )

    return 6371 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def search_nearby_providers(provider_type, latitude, longitude, radius=5000, limit=5):

    provider_type_lower = provider_type.lower()

    if "dermatolog" in provider_type_lower:
        tag_queries = """
        node["healthcare:speciality"="dermatology"](around:{radius},{lat},{lon});
        node["medical_specialty"="dermatology"](around:{radius},{lat},{lon});
        node["name"~"dermatolog",i](around:{radius},{lat},{lon});
        """

    elif "hospital" in provider_type_lower:
        tag_queries = """
        node["amenity"="hospital"](around:{radius},{lat},{lon});
        way["amenity"="hospital"](around:{radius},{lat},{lon});
        """

    elif "clinic" in provider_type_lower:
        tag_queries = """
        node["amenity"="clinic"](around:{radius},{lat},{lon});
        way["amenity"="clinic"](around:{radius},{lat},{lon});
        """

    elif "pharmacy" in provider_type_lower:
        tag_queries = """
        node["amenity"="pharmacy"](around:{radius},{lat},{lon});
        way["amenity"="pharmacy"](around:{radius},{lat},{lon});
        """

    else:
        tag_queries = """
        node["amenity"="doctors"](around:{radius},{lat},{lon});
        node["healthcare"="doctor"](around:{radius},{lat},{lon});
        """

    query = f"""
    [out:json][timeout:20];
    (
        {tag_queries.format(radius=radius, lat=latitude, lon=longitude)}
    );
    out center;
    """

    OVERPASS_URLS = [
        "https://overpass-api.de/api/interpreter",
        "https://lz4.overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
    ]

    headers = {
        "User-Agent": "AIHealthcareAssistant/1.0",
        "Accept": "application/json",
    }

    payload = None
    last_error = None

    for url in OVERPASS_URLS:
        try:
            print(f"Trying Overpass server: {url}")

            response = requests.post(
                url,
                data={"data": query},
                headers=headers,
                timeout=20,
            )

            print("Status:", response.status_code)

            response.raise_for_status()

            payload = response.json()
            print("Connected successfully!")
            break

        except (requests.RequestException, ValueError) as exc:
            print(f"Failed: {url}")
            print(exc)
            last_error = exc

    if payload is None:
        raise OSMPlacesError(f"All OpenStreetMap servers failed.\n{last_error}")

    elements = payload.get("elements", [])

    origin = (float(latitude), float(longitude))
    providers = []

    for element in elements:

        tags = element.get("tags", {})

        name = tags.get("name", provider_type.title())

        if "lat" in element:
            dest_lat = element["lat"]
            dest_lon = element["lon"]
        elif "center" in element:
            dest_lat = element["center"]["lat"]
            dest_lon = element["center"]["lon"]
        else:
            continue

        distance = _distance_km(origin, (dest_lat, dest_lon))

        address_parts = []

        if tags.get("addr:housenumber"):
            address_parts.append(tags["addr:housenumber"])

        if tags.get("addr:street"):
            address_parts.append(tags["addr:street"])

        if tags.get("addr:city"):
            address_parts.append(tags["addr:city"])

        address = ", ".join(address_parts) if address_parts else "Address unavailable"

        providers.append(
            {
                "name": name,
                "rating": None,
                "address": address,
                "distance": round(distance, 2) if distance is not None else None,
                "directions_url": f"https://www.google.com/maps/search/?api=1&query={dest_lat},{dest_lon}",
            }
        )

    providers.sort(
        key=lambda p: p["distance"] if p["distance"] is not None else 9999
    )

    unique = []
    seen = set()

    for provider in providers:
        if provider["name"] not in seen:
            seen.add(provider["name"])
            unique.append(provider)

        if len(unique) >= limit:
            break

    return unique