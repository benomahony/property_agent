import httpx
from typing import Any
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("LandRegistry")
SPARQL_ENDPOINT = "https://landregistry.data.gov.uk/landregistry/query"

# Region data will be loaded on first access
REGIONS: dict[str, dict[str, str]] = {}


async def load_regions() -> None:
    """Load all regions from the Land Registry."""
    global REGIONS

    if REGIONS:
        return

    query = """
        PREFIX ukhpi: <http://landregistry.data.gov.uk/def/ukhpi/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT DISTINCT ?uri ?name
        WHERE {
          ?uri a ukhpi:Region ;
              rdfs:label ?name .
          FILTER (langMatches(lang(?name), "EN"))
        }
        ORDER BY ?name
    """

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                SPARQL_ENDPOINT, params={"output": "json", "query": query}
            )
            data = response.json()

            for item in data.get("results", {}).get("bindings", []):
                name = item.get("name", {}).get("value", "")
                uri = item.get("uri", {}).get("value", "")
                key = (
                    name.lower().replace(" ", "_").replace(",", "").replace("&", "and")
                )
                REGIONS[key] = {"name": name, "uri": uri}

    except Exception as e:
        print(f"Error loading regions: {e}")


def find_region_uri(region_name: str) -> str:
    """Find the URI for a region by name."""
    # Normalize the search key
    search_key = (
        region_name.lower().replace(" ", "_").replace(",", "").replace("&", "and")
    )

    # Direct match
    if search_key in REGIONS:
        return REGIONS[search_key]["uri"]

    # Partial match
    for key, data in REGIONS.items():
        if search_key in key or key in search_key:
            return data["uri"]

    # No match found
    return ""


def create_query(region_name: str, year: int, month: int) -> str:
    """Create a SPARQL query for house price data."""
    date_str = f"{year}-{month:02d}"

    # Try to find the region URI
    region_uri = find_region_uri(region_name)

    if region_uri:
        # Use direct URI query
        return f"""
            PREFIX ukhpi: <http://landregistry.data.gov.uk/def/ukhpi/>
            
            SELECT ?date ?ukhpi ?averagePrice
            WHERE {{
              ?data ukhpi:refRegion <{region_uri}> ;
                    ukhpi:refMonth ?date ;
                    ukhpi:housePriceIndex ?ukhpi ;
                    ukhpi:averagePrice ?averagePrice .
                    
              FILTER(CONTAINS(STR(?date), "{date_str}"))
            }}
            LIMIT 1
        """
    else:
        return f"""
            PREFIX ukhpi: <http://landregistry.data.gov.uk/def/ukhpi/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT ?regionName ?date ?ukhpi ?averagePrice
            WHERE {{
              ?data ukhpi:refRegion/rdfs:label ?regionName ;
                    ukhpi:refMonth ?date ;
                    ukhpi:housePriceIndex ?ukhpi ;
                    ukhpi:averagePrice ?averagePrice .
                    
              FILTER(CONTAINS(LCASE(?regionName), LCASE("{region_name}")))
              FILTER(CONTAINS(STR(?date), "{date_str}"))
              FILTER(langMatches(lang(?regionName), "EN"))
            }}
            LIMIT 5
        """


def create_postcode_query(postcode: str, limit: int = 10) -> str:
    """Create a SPARQL query for property transactions in a postcode."""
    return f"""
        PREFIX lrppi: <http://landregistry.data.gov.uk/def/ppi/>
        PREFIX lrcommon: <http://landregistry.data.gov.uk/def/common/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT ?date ?price ?propertyType ?newBuild ?tenure ?paon ?saon ?street ?locality ?town ?district ?county
        WHERE {{
          ?transaction lrppi:propertyAddress ?address ;
                      lrppi:pricePaid ?price ;
                      lrppi:transactionDate ?date ;
                      lrppi:propertyType ?propertyTypeUri ;
                      lrppi:newBuild ?newBuild ;
                      lrppi:estateType ?estateTypeUri .
                      
          ?address lrcommon:postcode "{postcode}" .
          
          OPTIONAL {{ ?address lrcommon:paon ?paon . }}
          OPTIONAL {{ ?address lrcommon:saon ?saon . }}
          OPTIONAL {{ ?address lrcommon:street ?street . }}
          OPTIONAL {{ ?address lrcommon:locality ?locality . }}
          OPTIONAL {{ ?address lrcommon:town ?town . }}
          OPTIONAL {{ ?address lrcommon:district ?district . }}
          OPTIONAL {{ ?address lrcommon:county ?county . }}
          
          ?propertyTypeUri rdfs:label ?propertyType .
          ?estateTypeUri rdfs:label ?tenure .
          
          FILTER(LANG(?propertyType) = '' || LANGMATCHES(LANG(?propertyType), 'en'))
          FILTER(LANG(?tenure) = '' || LANGMATCHES(LANG(?tenure), 'en'))
        }}
        ORDER BY DESC(?date)
        LIMIT {limit}
    """


async def execute_query(query: str) -> list[dict[str, Any]]:
    """Execute a SPARQL query and return the results."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(
                SPARQL_ENDPOINT, params={"output": "json", "query": query}
            )
            data = response.json()

            results = []
            for item in data.get("results", {}).get("bindings", []):
                result = {}
                for field, value in item.items():
                    if field == "regionName":
                        result["region_name"] = value.get("value", "")
                    elif field == "date":
                        result["date"] = value.get("value", "").split("T")[0]
                    elif field == "price" or field == "newBuild":
                        try:
                            result[field] = float(value.get("value", 0))
                        except ValueError:
                            result[field] = value.get("value", "")
                    else:
                        try:
                            result[field] = float(value.get("value", 0))
                        except ValueError:
                            result[field] = value.get("value", "")
                results.append(result)

            return results
    except Exception as e:
        print(f"Error executing query: {e}")
        return []


@mcp.tool()
async def query_hpi(region: str, year: int, month: int) -> dict[str, Any]:
    """Query house price index data for a region and month."""
    await load_regions()
    query = create_query(region, year, month)
    results = await execute_query(query)
    return {"results": results}


@mcp.tool()
async def compare_regions(regions: list[str], year: int, month: int) -> dict[str, Any]:
    """Compare House Price Index data across multiple regions."""
    await load_regions()

    results = []
    for region in regions:
        query = create_query(region, year, month)
        region_results = await execute_query(query)
        if region_results:
            for result in region_results:
                if "region_name" not in result and "averagePrice" in result:
                    # Add region name if it's a direct URI match
                    result["region_name"] = region
                results.append(result)

    return {"results": results}


@mcp.tool()
async def get_postcode_transactions(postcode: str, limit: int = 10) -> dict[str, Any]:
    """Get property transactions for a specific postcode."""
    query = create_postcode_query(postcode, limit)
    results = await execute_query(query)
    return {"results": results}


@mcp.resource("hpi://regions")
async def get_regions() -> str:
    """Get a list of all available regions."""
    await load_regions()

    output = ["# Available House Price Index Regions\n"]

    for key, data in sorted(REGIONS.items(), key=lambda x: x[1]["name"]):
        output.append(f"- {data['name']}")

    return "\n".join(output)


if __name__ == "__main__":
    mcp.run()
