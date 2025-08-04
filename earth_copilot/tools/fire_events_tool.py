import os
import requests
import json
import re
from langchain.agents import tool
from dotenv import find_dotenv
from datetime import datetime, date
import datetime as datetime_base



# LangChain tool that searches for a fire event by name and returns that event's information, including location and date
# Parameters: 
#   event_name - Name of the fire event 
#   start_date / end_date - Date range to search
#   bbox_north/south/east/west_coordiantes - Bounding box to search
@tool
def search_fire_event(event_name: str, start_date: datetime = None,
                               end_date: datetime = None, bbox_north_coordinate: float = None, bbox_south_coordinate: float = None, 
                               bbox_east_coordinate: float = None, bbox_west_coordinate: float = None, 
                               ) -> str:
    """Determine a fire event's location and date range by searching the National Interagency Fire Center"""
    
    find_dotenv()
    search_url = os.getenv("FIRE_EVENTS_SEARCH_URL")
    date_format: str = "%Y-%m-%dT%H:%M:%SZ"
    #strip out extraneous stuff from query
    if len(event_name.split()) > 1:
        compiled = re.compile(re.escape("fire"), re.IGNORECASE)
        event_name = compiled.sub("", event_name)        
        event_name = event_name.strip()
    
    #include temporal terms if present
    where_clause = f"(IncidentName LIKE '{event_name}' OR IncidentShortDescription LIKE '{event_name}')"
    if start_date != None and end_date != None:
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        where_clause = f"{where_clause} AND FireDiscoveryDateTime BETWEEN DATE '{start_str}' and DATE '{end_str}' "
    print (f"WHERE: {where_clause}")
    params = {
                "where": where_clause, 
                "outFields": "IncidentName,IncidentShortDescription,POOState,ContainmentDateTime,ControlDateTime,FireDiscoveryDateTime,FireOutDateTime,POOCity,POOCounty", 
                "outSR": "4326", 
                "f": "json"}
  
    #include geospatial search terms if present  
    if bbox_north_coordinate != None and bbox_south_coordinate != None and bbox_east_coordinate != None and bbox_west_coordinate != None:
        params.update({"geometry": f"{bbox_west_coordinate},{bbox_south_coordinate},{bbox_east_coordinate},{bbox_north_coordinate}"})
        params.update({"geometryType": "esriGeometryEnvelope"})
        params.update({"spatialRel": "esriSpatialRelIntersects"})
           
    response = requests.get(
                            search_url,
                            params=params
                            )
    
    if (200 <= response.status_code <= 226): 
        json_response=json.loads(response.content)
        
        if json_response != None:
            
            #start trimming down response
            if 'fields' in json_response:
                del json_response['fields']
            
            # process the actual results of the query
            if 'features' in json_response:
                length = len(json_response['features'])
                print (f"Processing {length} results from National Interagency Fire Center query: {event_name}")
                print (f"Request: {response.request.url}")
                for item in json_response['features']:
                    
                    start_ticks = item['attributes']['FireDiscoveryDateTime'] / 1000.0
                    end_ticks: list[float] = []
                    if item['attributes']['ContainmentDateTime'] != None:
                        end_ticks.append(item['attributes']['ContainmentDateTime'])
                    if item['attributes']['ControlDateTime'] != None:
                        end_ticks.append(item['attributes']['ControlDateTime'])
                    if item['attributes']['FireOutDateTime'] != None:
                        end_ticks.append(item['attributes']['FireOutDateTime'])
                    
                    start_datetime = datetime.fromtimestamp(start_ticks)
                    start_datetime_str = start_datetime.strftime('%Y-%m-%d')
                    if len(end_ticks) > 0:
                        end_ticks_max = max(end_ticks) / 1000.0
                        end_datetime = date.fromtimestamp(end_ticks_max)
                    else:
                        #if no natural end to the fire detected, set end date 30 days out 
                        end_datetime = start_datetime + datetime_base.timedelta(days=30)
                    end_datetime_str = end_datetime.strftime('%Y-%m-%d')
                    del item['attributes']['ContainmentDateTime']
                    del item['attributes']['ControlDateTime']
                    del item['attributes']['FireOutDateTime']
                    del item['attributes']['FireDiscoveryDateTime']
                    item['attributes']['start_date'] = start_datetime_str
                    item['attributes']['end_date'] = end_datetime_str
                    item['attributes']['state'] = item['attributes']['POOState']
                    item['attributes']['county'] = item['attributes']['POOCounty']
                    item['attributes']['city'] = item['attributes']['POOCity']
                    del item['attributes']['POOState']
                    del item['attributes']['POOCounty']
                    del item['attributes']['POOCity']
                    longitude: float = float(item['geometry']['x'])
                    latitude: float = float(item['geometry']['y'])
                    #create bounding box from centroid
                    item['geometry']['bbox_west_longitude'] = longitude - 0.5
                    item['geometry']['bbox_east_longitude'] = longitude + 0.5
                    item['geometry']['bbox_south_latitude'] = latitude - 0.5
                    item['geometry']['bbox_north_latitude'] = latitude + 0.5
                    del item['geometry']['x']
                    del item['geometry']['y']                       
    else:
        print (f"Error in Fire Event query for {event_name}. Response code: {response.status_code}")
        print (response.content)
    
    return json_response
 
    
    
    