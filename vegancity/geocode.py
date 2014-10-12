""" module for performing various sorts of geocoding related tasks """

import urllib
import json

from settings import LOCATION_BOUNDS, LOCATION_COMPONENTS


def geocode_address(address):
    """
    takes an address as a string and returns a tuple of latitude,
    longitude and neighborhood in float format.

    if geocoding fails, silently returns a 3-tuple of None values.
    logging should be performed on the other end where more context
    is available.
    """

    base_url = "http://maps.googleapis.com/maps/api/geocode/json?"
    address_param = "address=" + urllib.quote_plus(address)
    sensor_param = "sensor=false"
    bounds_param = "bounds=" + LOCATION_BOUNDS
    components_param = "components=" + LOCATION_COMPONENTS

    full_url = base_url + "&".join([address_param, sensor_param,
                                    bounds_param, components_param])
    raw_response = urllib.urlopen(full_url).read()
    json_response = json.loads(raw_response)
    if not json_response['status'] == 'OK':
        latitude = longitude = neighborhood = None
    else:
        latitude = json_response['results'][0]['geometry']['location']['lat']
        longitude = json_response['results'][0]['geometry']['location']['lng']
        neighborhd_hashes = [hash for hash in
                             json_response['results'][0]['address_components']
                             if 'neighborhood' in hash['types']]
        if neighborhd_hashes:
            neighborhood = neighborhd_hashes[0]['long_name']
        else:
            neighborhood = None
    return latitude, longitude, neighborhood
