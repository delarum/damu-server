import math


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance in kilometers between two points
    on Earth using the Haversine formula.
    Donor GPS coordinates are never exposed — only this result is returned.
    """
    R = 6371  # Earth radius in km

    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    return round(R * c, 2)


def donors_within_radius(donors_qs, hospital_lat, hospital_lng, radius_km):
    """
    Filter a DonorProfile queryset to those within radius_km of the hospital.
    Returns a list of (donor, distance_km) tuples sorted by distance.
    """
    results = []
    for donor in donors_qs:
        if donor.lat is None or donor.lng is None:
            continue
        distance = haversine_distance(hospital_lat, hospital_lng, donor.lat, donor.lng)
        if distance <= radius_km:
            results.append((donor, distance))
    results.sort(key=lambda x: x[1])
    return results