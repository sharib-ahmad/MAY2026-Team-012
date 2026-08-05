# app/features/collection_ops/ors_client.py
import json
import logging
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)


def decode_polyline(polyline_str: str) -> list[list[float]]:
    """
    Decodes a Google encoded polyline string into a list of [latitude, longitude] coordinates.
    """
    coordinates = []
    index = 0
    lat, lng = 0, 0

    while index < len(polyline_str):
        results = []
        for _ in range(2):
            shift = 0
            result = 0
            while True:
                byte = ord(polyline_str[index]) - 63
                index += 1
                result |= (byte & 0x1F) << shift
                shift += 5
                if byte < 0x20:
                    break

            if result & 1:
                results.append(~(result >> 1))
            else:
                results.append(result >> 1)

        lat += results[0]
        lng += results[1]

        coordinates.append([lat / 100000.0, lng / 100000.0])

    return coordinates


class ORSClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openrouteservice.org/optimization"

    def optimize_route(
        self,
        start_coords: tuple[float, float],
        stop_coords: list[tuple[float, float]],
    ) -> dict:
        """
        Calls OpenRouteService Optimization API to get optimized route and polyline geometry.
        Returns a dict containing:
        - "optimized_indices": list of indices mapping to the optimized order of stop_coords.
        - "geometry": list of [latitude, longitude] coordinates representing the route geometry.
        """
        if not self.api_key:
            raise ValueError("OpenRouteService API key is missing.")

        # Convert coordinates to [lon, lat] for ORS
        start_lon_lat = [start_coords[1], start_coords[0]]

        jobs = []
        for idx, (lat, lon) in enumerate(stop_coords):
            jobs.append({"id": idx, "location": [lon, lat]})

        vehicles = [
            {"id": 0, "profile": "driving-car", "start": start_lon_lat, "end": start_lon_lat}
        ]

        payload = {"jobs": jobs, "vehicles": vehicles, "options": {"g": True}}

        req = urllib.request.Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": self.api_key, "Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            logger.error(f"ORS HTTP Error: {e.code} - {err_body}")
            raise Exception(f"ORS Optimization API returned error {e.code}: {err_body}") from e
        except Exception as e:
            logger.error(f"ORS request failed: {e}")
            raise Exception(f"Failed to query ORS Optimization API: {e}") from e

        # Parse response to extract optimized order and geometry
        routes = res_data.get("routes", [])
        if not routes:
            raise Exception("ORS Optimization API returned no routes.")

        route = routes[0]
        steps = route.get("steps", [])

        # Extract job IDs in visit order
        optimized_indices = []
        for step in steps:
            if step.get("type") == "job":
                optimized_indices.append(int(step["id"]))

        # Decode geometry polyline
        geometry_str = route.get("geometry", "")
        geometry_coords = []
        if geometry_str:
            geometry_coords = decode_polyline(geometry_str)
        else:
            # Fallback to straight line connecting stops in optimized order
            geometry_coords = [list(start_coords)]
            for idx in optimized_indices:
                geometry_coords.append(list(stop_coords[idx]))

        return {"optimized_indices": optimized_indices, "geometry": geometry_coords}
