import os
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_openai import AzureOpenAIEmbeddings
from langchain.agents import tool
from langchain_core.documents import Document
from dotenv import load_dotenv, find_dotenv
from shapely import Polygon, box
from datetime import datetime, date
from datetimerange import DateTimeRange
from dateutil import parser
import json
from collections import namedtuple
import requests
import azure.identity


# LangChain tool that searches metadata in an Azure AI Search index about VEDA collections based on content, location, and temporal extents. Intended to be passed into
# and utilized by a LangChain Agent at runtime
# Parameters:
#   query - User query
#   bbox_north_coordinate - Northern most latitude of bounding box extracted from User query
#   bbox_south_coordinate - Southern most latitude of bounding box extracted from User query
#   bbox_east_coordinate - Eastern most longitude of bounding box extracted from User query
#   bbox_west_coordinate - Western most longitude of bounding box extracted from User query
#   start_date - Temporal beginning extracted from User query
#   end_date - Temporal end extracted from User query
@tool
def determine_best_collections(
    query: str,
    bbox_north_coordinate: float,
    bbox_south_coordinate: float,
    bbox_east_coordinate: float,
    bbox_west_coordinate: float,
    start_date: datetime,
    end_date: datetime,
) -> list[tuple[Document, float]]:
    """Query VEDA Collections metadata to determine most applicable collections"""

    find_dotenv()
    search_endpoint = os.getenv("SEARCH_ENDPOINT")
    search_key = os.getenv("SEARCH_KEY")
    search_index = os.getenv("SEARCH_INDEX")
    aoai_endpoint = os.getenv("AOAI_ENDPOINT")
    aoai_key = os.getenv("AOAI_KEY")
    aoai_version = os.getenv("AOAI_VERSION")
    aoai_deployment = os.getenv("AOAI_DEPLOYMENT")
    relevancy_threshold = float(os.getenv("RELEVANCY_THRESHOLD"))
    stac_url = os.getenv("VEDA_CATALOG_URL")
    stac_search_endpoint = stac_url

    collection_start_dates = list()
    collection_end_dates = list()

    # create embeddings
    embeddings: AzureOpenAIEmbeddings = AzureOpenAIEmbeddings(
        azure_deployment=aoai_deployment,
        openai_api_version=aoai_version,
        azure_endpoint=aoai_endpoint,
        api_key=aoai_key,
    )

    # grab handle to vector store
    vector_store: AzureSearch = AzureSearch(
        azure_search_endpoint=search_endpoint,
        azure_search_key=search_key,
        index_name=search_index,
        embedding_function=embeddings.embed_query,
        content_key="content",  # This should map to your combined content field
        # Specify the vector field name that matches your index
        fields={
            "content": "content",
            "metadata": "id",
            "vector": "content_vector",  # This must match the vector field in your index
        },
    )

    docs = vector_store.similarity_search_with_relevance_scores(
        query=query, k=10, score_threshold=relevancy_threshold
    )

    print(f"Vector search returned {len(docs)} results")

    if docs != None and len(docs) > 0:
        # return only collections that intersect the query location and timeframe
        documents: list[tuple[Document, float]] = []

        for doc_tuple in docs:
            doc, score = doc_tuple

            print(f"Processing document with score: {score}")
            print(f"Doc page_content: '{doc.page_content}'")
            print(f"Doc metadata: {doc.metadata}")

            # Try to get document ID from different possible sources
            doc_id = None
            if hasattr(doc, "metadata") and doc.metadata:
                doc_id = doc.metadata.get("id")

            # If no ID in metadata, try to extract from page_content if it exists
            if not doc_id and doc.page_content:
                try:
                    temp_data = json.loads(doc.page_content)
                    doc_id = temp_data.get("id")
                except:
                    pass

            if not doc_id:
                print("Warning: Could not find document ID, skipping...")
                continue

            print(f"Found document ID: {doc_id}")

            try:
                # Fetch the full document using direct HTTP API call with API key
                url = f"{search_endpoint}/indexes/{search_index}/docs('{doc_id}')"
                headers = {"api-key": search_key, "Content-Type": "application/json"}
                params = {"api-version": "2024-07-01"}

                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                full_doc = response.json()

                print(f"Retrieved full document for ID: {doc_id}")

                # Reconstruct the collection object from the indexed fields
                spatial_extent = json.loads(full_doc.get("spatial_extent", "{}"))
                temporal_extent = json.loads(full_doc.get("temporal_extent", "{}"))

                collection = {
                    "id": full_doc["id"],
                    "title": full_doc.get("title", ""),
                    "description": full_doc.get("description", ""),
                    "extent": {"spatial": spatial_extent, "temporal": temporal_extent},
                }

                print(f"Reconstructed collection: {collection['id']}")

            except Exception as e:
                print(f"Error fetching full document for {doc_id}: {e}")
                continue

            # Now continue with your existing geospatial and temporal intersection logic
            # (Keep all the existing code from here down)

            # Grab geographic and temporal extents of the collection
            if (
                collection["extent"]["spatial"].get("bbox")
                and len(collection["extent"]["spatial"]["bbox"]) > 0
                and len(collection["extent"]["spatial"]["bbox"][0]) >= 4
            ):

                bbox = collection["extent"]["spatial"]["bbox"][0]
                coll_west = float(bbox[0]) if bbox[0] is not None else -180.0
                coll_south = float(bbox[1]) if bbox[1] is not None else -90.0
                coll_east = float(bbox[2]) if bbox[2] is not None else 180.0
                coll_north = float(bbox[3]) if bbox[3] is not None else 90.0
            else:
                coll_west = -180.0
                coll_south = -90.0
                coll_east = 180.0
                coll_north = 90.0

            if (
                collection["extent"]["temporal"].get("interval")
                and len(collection["extent"]["temporal"]["interval"]) > 0
                and len(collection["extent"]["temporal"]["interval"][0]) >= 2
            ):

                interval = collection["extent"]["temporal"]["interval"][0]
                if interval[0] is not None:
                    coll_start_date = parser.parse(interval[0])
                else:
                    coll_start_date = datetime(1900, 1, 1)

                if interval[1] is not None:
                    coll_end_date = parser.parse(interval[1])
                else:
                    coll_end_date = datetime.now()
            else:
                coll_start_date = datetime(1900, 1, 1)
                coll_end_date = datetime.now()

            print(f"{coll_west},{coll_south},{coll_east},{coll_north}")
            print(f"{coll_start_date} to {coll_end_date}")

            # Determine if query location intersects collection geospatial extent
            intersects_location: bool = False
            collection_extents = Polygon(
                [
                    (coll_south, coll_west),
                    (coll_south, coll_east),
                    (coll_north, coll_east),
                    (coll_north, coll_west),
                ]
            )
            query_extents = Polygon(
                [
                    (bbox_south_coordinate, bbox_west_coordinate),
                    (bbox_south_coordinate, bbox_east_coordinate),
                    (bbox_north_coordinate, bbox_east_coordinate),
                    (bbox_north_coordinate, bbox_west_coordinate),
                ]
            )
            intersects_location = collection_extents.intersects(query_extents)
            print(f"intersects_location = {intersects_location}")

            # Determine if query date range overlaps collection temporal extent
            intersects_date_range: bool = False
            Range = namedtuple("Range", ["start", "end"])
            collection_range = Range(
                start=coll_start_date.date(), end=coll_end_date.date()
            )
            query_range = Range(start=start_date.date(), end=end_date.date())
            latest_start = max(collection_range.start, query_range.start)
            earliest_end = min(collection_range.end, query_range.end)
            delta = (earliest_end - latest_start).days + 1
            overlap = max(0, delta)
            intersects_date_range = overlap >= 1
            print(f"intersects_date_range = {intersects_date_range}")

            if intersects_date_range and intersects_location:
                # Determine if there is actually data contained in the STAC collections for the user's query
                collection_id = collection["id"]
                if collection_id != None:
                    print(f"Initiating STAC query for {collection_id}")
                    credential = azure.identity.DefaultAzureCredential()
                    token = credential.get_token("https://geocatalog.spatio.azure.com")
                    headers = {"Authorization": f"Bearer {token.token}"}
                    # print(f"Headers: {headers}")
                    format: str = "%Y-%m-%dT%H:%M:%SZ"
                    start_str = start_date.strftime(format)
                    end_str = end_date.strftime(format)
                    datetime_str = f"{start_str}/{end_str}"
                    bbox_str = f"{bbox_west_coordinate},{bbox_south_coordinate},{bbox_east_coordinate},{bbox_north_coordinate}"
                    response = requests.get(
                        stac_search_endpoint,
                        headers=headers,
                        params={
                            "collections": collection_id,
                            "bbox": bbox_str,
                            "datetime": datetime_str,
                            "limit": "1",
                            "api-version": "2024-01-31-preview",
                        },
                    )
                    print(f"Request: {response.request.url}")
                    if 200 <= response.status_code <= 226:
                        json_response = json.loads(response.content)
                        print(json_response)
                        if json_response != None:

                            # Open VEDA has a context section so we can easily tell how many were matched
                            # matched = int(json_response['context']['matched'])

                            # Spatio does not, so we'll examine the length of the features list that comes back
                            if json_response["features"] != None:
                                matched = len(json_response["features"])

                                print(
                                    f"Collection search yielded: {matched} STAC records"
                                )

                                if matched >= 1:
                                    documents.append(
                                        Document(
                                            page_content=doc[0].page_content,
                                            metadata={
                                                "relevancy_score": {doc[1]},
                                                "collection_start_date": {
                                                    coll_start_date.date()
                                                },
                                                "collection_end_date": {
                                                    coll_end_date.date()
                                                },
                                            },
                                        )
                                    )
                    else:
                        print(
                            f"Error in STAC query for {collection_id}. Response code: {response.status_code}"
                        )
                        print(response.content)

                # documents.append(Document(
                #                             page_content=doc[0].page_content,
                #                             metadata = {"relevancy_score": {doc[1]},
                #                                         "collection_start_date": {coll_start_date.date()},
                #                                         "collection_end_date": {coll_end_date.date()}
                #                             }
                #                         )
                #                  )
            collection_start_dates.append(coll_start_date.date())
            collection_end_dates.append(coll_end_date.date())
            print("\n")

            # compress date range to collection date range extents if query extents fall outside of collection extents
            # FinalDateRange = namedtuple('FinalDateRange', ['start_date', 'end_date'])
            # final_start = datetime.combine(max(min(collection_start_dates), start_date.date()), datetime.min.time())
            # final_end = datetime.combine(min(max(collection_end_dates), end_date.date()), datetime.max.time())
            # final_date_range = FinalDateRange(start_date=final_start, end_date=final_end)

            # print(f"Final date range: {final_start} to {final_end}")
            # print(f"FinalDateRange: {final_date_range}")
            return documents  # , final_date_range
    else:
        return "No suitable collections found"
