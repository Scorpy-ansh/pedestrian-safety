# 🛣️ Pedestrian Safety & Safe Route Finder

> A web app that visualizes **street safety** and computes the **safest pedestrian route** between two points in Indian cities using **OpenStreetMap** data.

---

## ✨ Features

- 🌍 **Interactive Map** (MapLibre + OpenStreetMap)
- 🎨 **Safety Heatmap**: Streets are colored by risk level:
  - 🟥 Very Risky  
  - 🟧 Risky  
  - 🟨 Moderate  
  - 🟩 Safer  
  - 🟢 Very Safe
- 🧭 **Safest Route Finder**: Click two points on the map to get the safest walking route.
- 🏙️ **City Selector**: Instantly load networks of major Indian cities & capitals.
- ⚡ **FastAPI Backend**: Graph building, scoring & routing.
- 🎉 **Frontend** deployed on **Netlify**, **Backend** deployed on **Render / Railway**.

---

## 🖼️ Screenshots

### 🔹 Safety Map Example
![Map Demo](./assets/demo-map.png)

### 🔹 Routing Example
![Routing Demo](./assets/demo-route.png)

---

## 🛠️ Tech Stack

### Frontend
- [MapLibre GL JS](https://maplibre.org/) → Interactive maps
- HTML, CSS, Vanilla JS

### Backend
- [FastAPI](https://fastapi.tiangolo.com/) → API
- [OSMnx](https://osmnx.readthedocs.io/) → Build graphs from OpenStreetMap
- [NetworkX](https://networkx.org/) → Graph routing
- [GeoPandas](https://geopandas.org/) & [Shapely](https://shapely.readthedocs.io/) → Geo operations

### Deployment
- 🌐 **Frontend**: [Netlify](https://www.netlify.com/)  
- ⚙️ **Backend**: [Render](https://render.com/) / [Railway](https://railway.app/)  

---

## 🚀 Getting Started (Local Setup)

### 1️⃣ Clone the repo
```bash
git clone https://github.com/<your-username>/pedestrian-safety.git
cd pedestrian-safety
