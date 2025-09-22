from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse

app = FastAPI(title="Pedestrian Safety API", default_response_class=ORJSONResponse)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # later you can replace "*" with your Netlify URL
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from shapely.geometry import mapping, LineString
import osmnx as ox

from fastapp.safety import (
    build_graph, graph_to_edges, compute_scores, set_route_weights, safest_path
)


BASE_DIR = Path(__file__).parent          
STATIC_DIR = BASE_DIR / "static"          
INDEX_HTML = STATIC_DIR / "index.html"

app = FastAPI(title="Pedestrian Safety API")


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

_STATE = {"place": None, "G": None, "nodes": None, "edges": None, "alpha": 0.5}

@app.get("/health")
def health():
    return {"ok": True, "has_graph": _STATE["G"] is not None, "place": _STATE["place"]}

@app.post("/graph")
def create_graph(payload: dict):
    place = payload.get("place")
    alpha = float(payload.get("alpha", 0.5))
    if not place:
        raise HTTPException(400, "place is required")

    G = build_graph(place)
    nodes, edges = graph_to_edges(G)
    edges = compute_scores(edges)
    G, edges = set_route_weights(G, edges, alpha=alpha)

    _STATE.update(place=place, G=G, nodes=nodes, edges=edges, alpha=alpha)
    return {"ok": True, "place": place, "nodes": int(len(nodes)), "edges": int(len(edges)), "alpha": alpha}

@app.get("/edges.geojson")
def get_edges_geojson():
    if _STATE["edges"] is None:
        raise HTTPException(400, "Graph not loaded. POST /graph first.")
    features = []
    for _, r in _STATE["edges"].iterrows():
        geom = r.geometry
        if geom is None:
            u, v = r["u"], r["v"]
            if (u in _STATE["G"]) and (v in _STATE["G"]):
                y1, x1 = _STATE["G"].nodes[u]["y"], _STATE["G"].nodes[u]["x"]
                y2, x2 = _STATE["G"].nodes[v]["y"], _STATE["G"].nodes[v]["x"]
                geom = LineString([(x1, y1), (x2, y2)])
            else:
                continue
        features.append({
            "type": "Feature",
            "geometry": mapping(geom),
            "properties": {"safety_score": float(r["safety_score"])}
        })
    return JSONResponse({"type": "FeatureCollection", "features": features})

@app.post("/route")
def route(payload: dict):
    if _STATE["G"] is None:
        raise HTTPException(400, "Graph not loaded. POST /graph first.")
    try:
        lat1, lon1 = float(payload["start"]["lat"]), float(payload["start"]["lon"])
        lat2, lon2 = float(payload["end"]["lat"]), float(payload["end"]["lon"])
    except Exception:
        raise HTTPException(400, "start/end must have lat/lon")

    path = safest_path(_STATE["G"], lat1, lon1, lat2, lon2)

    # convert path to coordinates (lon, lat)
    coords = []
    for u, v in zip(path[:-1], path[1:]):
        data = _STATE["G"].get_edge_data(u, v)
        key, attrs = min(data.items(), key=lambda kv: kv[1].get("route_weight", 1e9))
        if attrs.get("geometry") is not None:
            coords.extend(list(attrs["geometry"].coords))
        else:
            y1, x1 = _STATE["G"].nodes[u]["y"], _STATE["G"].nodes[u]["x"]
            y2, x2 = _STATE["G"].nodes[v]["y"], _STATE["G"].nodes[v]["x"]
            coords.extend([(x1, y1), (x2, y2)])

    gj = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": {"color": "#0077ff", "name": "Safest route"}
        }]
    }
    return JSONResponse(gj)

@app.get("/")
def index():
    if not INDEX_HTML.exists():
        # Helpful message if the path is wrong
        return JSONResponse({"error": f"index.html not found at {INDEX_HTML}"}, status_code=500)
    return FileResponse(str(INDEX_HTML))
