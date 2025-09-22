import osmnx as ox, numpy as np, pandas as pd, networkx as nx

def build_graph(place: str):
    G = ox.graph_from_place(place, network_type="walk", simplify=True)
    G = ox.speed.add_edge_speeds(G)
    G = ox.distance.add_edge_lengths(G)
    return G

def graph_to_edges(G):
    nodes, edges = ox.graph_to_gdfs(G)
    edges = edges.reset_index(drop=False)
    return nodes, edges

def _to_float(x):
    try:
        if isinstance(x, list): x = x[0]
        x = str(x).split(';')[0]; return float(x)
    except: return np.nan

def _true(x):
    s = str(x).lower()
    return any(k in s for k in ["yes","true","1","both","left","right","separate"])

def _col(df, name, default=np.nan):
    return df[name] if name in df.columns else pd.Series([default]*len(df), index=df.index)

def compute_scores(edges):
    edges = edges.copy()
    edges["maxspeed_kph"] = _col(edges,"maxspeed").apply(_to_float)
    edges["lanes_num"]    = _col(edges,"lanes").apply(_to_float)

    tmp = pd.DataFrame({
        "sidewalk": _col(edges,"sidewalk"),
        "sidewalk:left": _col(edges,"sidewalk:left"),
        "sidewalk:right": _col(edges,"sidewalk:right"),
        "highway": _col(edges,"highway","")
    })
    def has_sidewalk_row(r):
        if _true(r["sidewalk"]) or _true(r["sidewalk:left"]) or _true(r["sidewalk:right"]):
            return True
        hw = str(r["highway"]).lower()
        return any(k in hw for k in ["footway","pedestrian","path","living_street"])
    edges["has_sidewalk"] = tmp.apply(has_sidewalk_row, axis=1)

    edges["is_lit"] = _col(edges,"lit").apply(_true)
    edges["is_crossing"] = (
        _col(edges,"highway","").astype(str).str.contains("crossing",case=False,na=False) |
        _col(edges,"crossing","").astype(str).str.contains("zebra|uncontrolled|traffic_signals|marked",case=False,na=False)
    )

    risk_map = {"footway":0.10,"path":0.15,"pedestrian":0.12,"residential":0.25,"living_street":0.20,
                "service":0.30,"tertiary":0.50,"secondary":0.60,"primary":0.70,"trunk":0.85,"motorway":1.00}
    def base_risk(hw):
        if isinstance(hw, list): hw = hw[0]
        hw = str(hw).lower()
        for k,v in risk_map.items():
            if k in hw: return v
        return 0.50
    edges["base_risk"] = _col(edges,"highway","").apply(base_risk)

    edges["maxspeed_kph"] = edges["maxspeed_kph"].fillna(edges["base_risk"].apply(lambda r: 30 if r<=0.25 else (40 if r<=0.5 else 50)))
    edges["lanes_num"]    = edges["lanes_num"].fillna(edges["base_risk"].apply(lambda r: 1 if r<=0.25 else (2 if r<=0.6 else 3)))
    edges["speed_norm"]   = edges["maxspeed_kph"] / 60.0
    edges["lanes_norm"]   = edges["lanes_num"] / 4.0
    edges["sidewalk_risk"]= np.where(edges["has_sidewalk"], 0.0, 0.30)
    edges["light_risk"]   = np.where(edges["is_lit"], 0.0, 0.20)
    edges["night_risk"]   = 0.10
    edges["crossing_bonus"]= np.where(edges["is_crossing"], -0.10, 0.0)

    W = {"base":0.35,"speed":0.20,"lanes":0.10,"sidewalk":0.15,"light":0.10,"night":0.05,"crossing":0.05}
    risk = (W["base"]*edges["base_risk"] + W["speed"]*edges["speed_norm"] + W["lanes"]*edges["lanes_norm"] +
            W["sidewalk"]*edges["sidewalk_risk"] + W["light"]*edges["light_risk"] + W["night"]*edges["night_risk"] +
            W["crossing"]*edges["crossing_bonus"])
    edges["risk"] = risk.clip(0,1)
    edges["safety_score"] = ((1 - edges["risk"]) * 100).round(1)
    return edges

def set_route_weights(G, edges, alpha: float = 0.5):
    len_norm  = (edges["length"] - edges["length"].min())/(edges["length"].max()-edges["length"].min()+1e-9)
    safe_norm = (edges["safety_score"] - edges["safety_score"].min())/(edges["safety_score"].max()-edges["safety_score"].min()+1e-9)
    edges["route_weight"] = alpha*len_norm + (1-alpha)*(1 - safe_norm)
    nx.set_edge_attributes(G, {(r.u, r.v, r.key): r.route_weight for _, r in edges.iterrows()}, "route_weight")
    return G, edges

def safest_path(G, lat1, lon1, lat2, lon2):
    s = ox.distance.nearest_nodes(G, lon1, lat1)
    t = ox.distance.nearest_nodes(G, lon2, lat2)
    return nx.shortest_path(G, s, t, weight="route_weight")
