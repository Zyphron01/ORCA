import { useState, useEffect } from 'react';
import Map, { Marker, Source, Layer } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { AlertCircle, Layers, Info } from 'lucide-react';
import { setWorkerUrl } from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';

setWorkerUrl(workerUrl);

interface Incident {
  id: string;
  vessel_id: string;
  status: string;
  lkp_lat: number;
  lkp_lon: number;
}

interface SARData {
  predictions: any[];
  search_areas: any;
  agent_trace?: any[];
}

const SATELLITE_STYLE: any = {
  version: 8,
  sources: {
    'esri-satellite': {
      type: 'raster',
      tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
      tileSize: 256
    }
  },
  layers: [
    {
      id: 'satellite',
      type: 'raster',
      source: 'esri-satellite'
    }
  ]
};

const DARK_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

// Deterministic Prototype Data
const mockWeatherData = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', geometry: { type: 'Point', coordinates: [80.5, 13.0] }, properties: { text: '28°C\nCloudy', color: '#fbbf24' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [81.0, 12.5] }, properties: { text: '29°C\nClear', color: '#fbbf24' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [79.8, 11.5] }, properties: { text: '27°C\nRain', color: '#60a5fa' } },
  ]
};

const mockOceanData = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', geometry: { type: 'Point', coordinates: [80.8, 12.8] }, properties: { text: 'Wave: 1.8m\nSea State: 3', color: '#38bdf8' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [81.2, 11.8] }, properties: { text: 'Wave: 2.1m\nSea State: 4', color: '#38bdf8' } },
  ]
};

const mockWindData = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', geometry: { type: 'Point', coordinates: [80.3, 12.8] }, properties: { rot: 45, val: '18kn NE', type: 'Wind', color: '#a78bfa' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [80.6, 12.2] }, properties: { rot: 45, val: '22kn NE', type: 'Wind', color: '#a78bfa' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [80.4, 12.4] }, properties: { rot: 135, val: '1.2kn SE', type: 'Current', color: '#2dd4bf' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: [80.8, 11.6] }, properties: { rot: 135, val: '1.5kn SE', type: 'Current', color: '#2dd4bf' } },
  ]
};

const mockHazardsData = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { name: 'IMBL', type: 'BORDER' },
      geometry: {
        type: 'LineString',
        coordinates: [
          [80.0, 10.0],
          [80.5, 11.0],
          [81.0, 12.0],
          [82.0, 14.0]
        ]
      }
    },
    {
      type: 'Feature',
      properties: { name: 'Gulf of Mannar MPA', type: 'MPA' },
      geometry: {
        type: 'Polygon',
        coordinates: [[[78.5, 8.5], [79.5, 8.8], [79.2, 9.2], [78.4, 9.0], [78.5, 8.5]]]
      }
    }
  ]
};


export default function MarineMap({ incidents, selected, sarData }: { incidents: Incident[], selected: Incident | null, sarData: SARData | null }) {
  const [mapMode, setMapMode] = useState<'MARINE MONITORING' | 'INCIDENT INTELLIGENCE' | 'SAR OPERATIONS'>('MARINE MONITORING');
  const [layersOpen, setLayersOpen] = useState(false);
  
  const [activeLayers, setActiveLayers] = useState({
    satellite: true,
    weather: true,
    ocean: true,
    wind: true,
    hazards: true,
    vessels: true,
    sar: true
  });

  useEffect(() => {
    if (!selected) {
      setMapMode('MARINE MONITORING');
    } else if (selected.status === 'SAR_ACTIVE' || (sarData && sarData.predictions?.length > 0)) {
      setMapMode('SAR OPERATIONS');
    } else {
      setMapMode('INCIDENT INTELLIGENCE');
    }
  }, [selected, sarData]);

  const defaultViewState = {
    longitude: 80.2,
    latitude: 12.5,
    zoom: 7,
    pitch: 0,
    bearing: 0
  };

  const viewState = selected ? {
    longitude: selected.lkp_lon,
    latitude: selected.lkp_lat,
    zoom: 8
  } : defaultViewState;

  let searchConeGeojson = null;
  if (sarData?.search_areas) {
    searchConeGeojson = sarData.search_areas;
  }

  const toggleLayer = (layer: keyof typeof activeLayers) => {
    setActiveLayers(prev => ({ ...prev, [layer]: !prev[layer] }));
  };

  return (
    <div className="absolute inset-0 flex">
      <Map
        initialViewState={viewState}
        mapStyle={activeLayers.satellite ? SATELLITE_STYLE : DARK_STYLE}
        style={{ width: '100%', height: '100%' }}
      >
        {/* HAZARDS LAYER */}
        {activeLayers.hazards && (
          <Source id="hazards-source" type="geojson" data={mockHazardsData as any}>
            <Layer
              id="hazards-line"
              type="line"
              filter={['==', 'type', 'BORDER']}
              paint={{
                'line-color': '#ef4444',
                'line-width': 2,
                'line-dasharray': [4, 4]
              }}
            />
            <Layer
              id="hazards-polygon"
              type="fill"
              filter={['==', 'type', 'MPA']}
              paint={{
                'fill-color': '#10b981',
                'fill-opacity': 0.2
              }}
            />
            <Layer
              id="hazards-polygon-line"
              type="line"
              filter={['==', 'type', 'MPA']}
              paint={{
                'line-color': '#10b981',
                'line-width': 1
              }}
            />
            <Layer
              id="hazards-label"
              type="symbol"
              layout={{
                'text-field': ['get', 'name'],
                'text-size': 12,
                'symbol-placement': 'line',
                'text-offset': [0, 1]
              }}
              paint={{
                'text-color': '#f87171',
                'text-halo-color': '#000000',
                'text-halo-width': 1
              }}
            />
          </Source>
        )}

        {/* WIND / CURRENTS LAYER */}
        {activeLayers.wind && (
          <Source id="wind-source" type="geojson" data={mockWindData as any}>
            <Layer
              id="wind-arrows"
              type="symbol"
              layout={{
                'text-field': '↑',
                'text-size': 24,
                'text-rotate': ['get', 'rot'],
                'text-allow-overlap': true,
                'text-ignore-placement': true,
                'text-offset': [0, -0.5]
              }}
              paint={{
                'text-color': ['get', 'color'],
                'text-halo-color': '#000000',
                'text-halo-width': 2
              }}
            />
            <Layer
              id="wind-labels"
              type="symbol"
              layout={{
                'text-field': ['get', 'val'],
                'text-size': 10,
                'text-offset': [0, 1.5]
              }}
              paint={{
                'text-color': ['get', 'color'],
                'text-halo-color': '#000000',
                'text-halo-width': 1
              }}
            />
          </Source>
        )}

        {/* WEATHER LAYER */}
        {activeLayers.weather && (
          <Source id="weather-source" type="geojson" data={mockWeatherData as any}>
            <Layer
              id="weather-labels"
              type="symbol"
              layout={{
                'text-field': ['get', 'text'],
                'text-size': 12,
                'text-justify': 'center'
              }}
              paint={{
                'text-color': ['get', 'color'],
                'text-halo-color': '#000000',
                'text-halo-width': 2
              }}
            />
          </Source>
        )}

        {/* OCEAN LAYER */}
        {activeLayers.ocean && (
          <Source id="ocean-source" type="geojson" data={mockOceanData as any}>
            <Layer
              id="ocean-labels"
              type="symbol"
              layout={{
                'text-field': ['get', 'text'],
                'text-size': 12,
                'text-justify': 'center'
              }}
              paint={{
                'text-color': ['get', 'color'],
                'text-halo-color': '#000000',
                'text-halo-width': 2
              }}
            />
          </Source>
        )}

        {/* SAR LAYER */}
        {activeLayers.sar && searchConeGeojson && (
          <Source id="search-cone" type="geojson" data={searchConeGeojson}>
            <Layer
              id="search-cone-fill"
              type="circle"
              paint={{
                'circle-radius': ['*', ['get', 'uncertainty_radius_nm'], 5],
                'circle-color': '#3b82f6',
                'circle-opacity': 0.2
              }}
            />
            <Layer
              id="search-cone-line"
              type="circle"
              paint={{
                'circle-radius': ['*', ['get', 'uncertainty_radius_nm'], 5],
                'circle-stroke-color': '#3b82f6',
                'circle-stroke-width': 2,
                'circle-opacity': 0,
                'circle-color': 'transparent'
              }}
            />
          </Source>
        )}

        {/* VESSEL MARKERS */}
        {activeLayers.vessels && incidents.map(inc => (
          <Marker 
            key={inc.id} 
            longitude={inc.lkp_lon} 
            latitude={inc.lkp_lat}
            anchor="bottom"
          >
            <div className={`p-1 rounded-full ${selected?.id === inc.id ? 'bg-red-500 animate-pulse' : 'bg-red-900/80'} shadow-lg`}>
               <AlertCircle className="text-white w-6 h-6" />
            </div>
          </Marker>
        ))}

        {/* SAR MARKERS */}
        {activeLayers.sar && sarData?.predictions?.map((pred, idx) => {
          const lat = pred.predicted_lat || pred.position?.lat;
          const lon = pred.predicted_lon || pred.position?.lon;
          if (!lat || !lon) return null;
          
          return (
            <Marker 
              key={idx} 
              longitude={lon} 
              latitude={lat}
              anchor="center"
            >
              <div className="text-[10px] bg-blue-900 border border-blue-500 text-blue-100 px-1.5 py-0.5 rounded flex items-center shadow-lg font-bold">
                T+{pred.horizon_h || pred.horizon_hours}
              </div>
            </Marker>
          );
        })}
      </Map>

      {/* MAP MODE BADGE */}
      <div className="absolute top-4 left-4 z-10 flex flex-col gap-2">
        <div className={`px-3 py-1.5 rounded border font-bold text-xs shadow-lg flex items-center gap-2 ${
          mapMode === 'MARINE MONITORING' ? 'bg-slate-800 text-slate-300 border-slate-600' :
          mapMode === 'INCIDENT INTELLIGENCE' ? 'bg-amber-900/80 text-amber-400 border-amber-500/50' :
          'bg-red-900/80 text-red-400 border-red-500/50 animate-pulse'
        }`}>
          {mapMode === 'SAR OPERATIONS' && <div className="w-2 h-2 rounded-full bg-red-500 animate-ping" />}
          {mapMode}
        </div>
        
        {activeLayers.satellite && (
          <div className="px-3 py-1 rounded bg-blue-900/80 text-blue-300 border border-blue-500/50 font-bold text-[10px] shadow-lg flex items-center gap-2">
            SATELLITE VIEW — PROTOTYPE
          </div>
        )}
      </div>

      {/* MAP CONTROLS & LAYERS */}
      <div className="absolute top-4 right-4 z-10 flex flex-col items-end gap-2">
        <div className="flex items-center gap-2">
          <div className="px-2 py-1 rounded bg-slate-800/80 border border-slate-600 text-[10px] text-slate-400 font-bold flex items-center gap-1 shadow-lg backdrop-blur-sm">
            PROTOTYPE ENVIRONMENT
            <div className="group relative">
              <Info size={12} className="cursor-help" />
              <div className="hidden group-hover:block absolute right-0 top-full mt-2 w-48 bg-slate-800 border border-slate-600 rounded p-2 text-slate-300 text-[10px] font-normal shadow-xl z-50">
                Environmental visualization uses deterministic prototype data where live spatial feeds are not connected.
              </div>
            </div>
          </div>
          <button 
            onClick={() => setLayersOpen(!layersOpen)}
            className="bg-slate-800 hover:bg-slate-700 text-white p-2 rounded shadow-lg border border-slate-700 transition-colors"
            title="Map Layers"
          >
            <Layers size={20} />
          </button>
        </div>

        {layersOpen && (
          <div className="bg-slate-900/95 border border-slate-700 rounded-lg shadow-xl w-64 overflow-hidden backdrop-blur-sm">
            <div className="p-3 border-b border-slate-700 bg-slate-800">
              <h3 className="text-xs font-bold text-slate-300 tracking-wider">MAP LAYERS</h3>
            </div>
            <div className="p-2 space-y-1">
              
              <label className="flex items-center p-2 rounded hover:bg-slate-800 cursor-pointer">
                <input type="checkbox" className="rounded bg-slate-800 border-slate-600 text-blue-500" checked={activeLayers.satellite} onChange={() => toggleLayer('satellite')} />
                <span className="ml-3 text-sm text-slate-200">Satellite</span>
              </label>

              <label className="flex items-center p-2 rounded hover:bg-slate-800 cursor-pointer">
                <input type="checkbox" className="rounded bg-slate-800 border-slate-600 text-blue-500" checked={activeLayers.weather} onChange={() => toggleLayer('weather')} />
                <span className="ml-3 text-sm text-slate-200">Weather</span>
              </label>
              
              <label className="flex items-center p-2 rounded hover:bg-slate-800 cursor-pointer">
                <input type="checkbox" className="rounded bg-slate-800 border-slate-600 text-blue-500" checked={activeLayers.ocean} onChange={() => toggleLayer('ocean')} />
                <span className="ml-3 text-sm text-slate-200">Ocean</span>
              </label>

              <label className="flex items-center p-2 rounded hover:bg-slate-800 cursor-pointer">
                <input type="checkbox" className="rounded bg-slate-800 border-slate-600 text-blue-500" checked={activeLayers.wind} onChange={() => toggleLayer('wind')} />
                <span className="ml-3 text-sm text-slate-200">Wind / Currents</span>
              </label>
              
              <label className="flex items-center p-2 rounded hover:bg-slate-800 cursor-pointer">
                <input type="checkbox" className="rounded bg-slate-800 border-slate-600 text-blue-500" checked={activeLayers.hazards} onChange={() => toggleLayer('hazards')} />
                <span className="ml-3 text-sm text-slate-200">Marine Hazards</span>
              </label>

              <div className="my-2 border-t border-slate-700" />

              <label className="flex items-center p-2 rounded hover:bg-slate-800 cursor-pointer">
                <input type="checkbox" className="rounded bg-slate-800 border-slate-600 text-blue-500" checked={activeLayers.vessels} onChange={() => toggleLayer('vessels')} />
                <span className="ml-3 text-sm text-slate-200">Vessels</span>
              </label>

              <label className="flex items-center p-2 rounded hover:bg-slate-800 cursor-pointer">
                <input type="checkbox" className="rounded bg-slate-800 border-slate-600 text-blue-500" checked={activeLayers.sar} onChange={() => toggleLayer('sar')} />
                <span className="ml-3 text-sm text-slate-200">SAR Operations</span>
              </label>

            </div>
          </div>
        )}
      </div>

      {/* DYNAMIC LEGEND */}
      <div className="absolute bottom-6 right-2 z-10 flex flex-col gap-2">
        {activeLayers.weather && (
          <div className="bg-slate-900/95 border border-slate-700 rounded shadow-xl p-3 backdrop-blur-sm min-w-48 text-left">
            <h4 className="text-[10px] font-bold text-slate-400 tracking-wider mb-2">WEATHER — PROTOTYPE DATA</h4>
            <div className="text-xs text-slate-300 space-y-1">
              <p className="text-amber-400">● 28°C / Cloudy</p>
            </div>
          </div>
        )}

        {activeLayers.ocean && (
          <div className="bg-slate-900/95 border border-slate-700 rounded shadow-xl p-3 backdrop-blur-sm min-w-48 text-left">
            <h4 className="text-[10px] font-bold text-slate-400 tracking-wider mb-2">OCEAN CONDITIONS<br/>PROTOTYPE DATA</h4>
            <div className="text-xs text-slate-300 space-y-1">
              <p className="text-sky-400">● Wave: 1.8m</p>
            </div>
          </div>
        )}

        {activeLayers.wind && (
          <div className="bg-slate-900/95 border border-slate-700 rounded shadow-xl p-3 backdrop-blur-sm min-w-48 text-left">
            <h4 className="text-[10px] font-bold text-slate-400 tracking-wider mb-2">WIND / CURRENTS<br/>PROTOTYPE DATA</h4>
            <div className="text-xs text-slate-300 space-y-1">
              <p className="text-violet-400">WIND <span className="float-right">↗ 18 kn NE</span></p>
              <p className="text-teal-400">CURRENT <span className="float-right">↘ 1.2 kn SE</span></p>
            </div>
          </div>
        )}

        {activeLayers.hazards && (
          <div className="bg-slate-900/95 border border-slate-700 rounded shadow-xl p-3 backdrop-blur-sm min-w-48 text-left">
            <h4 className="text-[10px] font-bold text-slate-400 tracking-wider mb-2">MARINE HAZARDS<br/>PROTOTYPE VISUALIZATION</h4>
            <div className="text-xs text-slate-300 space-y-1">
              <p className="flex items-center gap-2"><span className="w-4 border-t-2 border-dashed border-red-500"></span> IMBL</p>
              <p className="flex items-center gap-2"><span className="w-4 h-4 bg-emerald-500/20 border border-emerald-500"></span> MPA</p>
            </div>
          </div>
        )}

        {activeLayers.sar && (mapMode === 'SAR OPERATIONS' || mapMode === 'INCIDENT INTELLIGENCE') && (
          <div className="bg-slate-900/95 border border-slate-700 rounded shadow-xl p-3 backdrop-blur-sm min-w-48 text-left">
            <h4 className="text-[10px] font-bold text-slate-400 tracking-wider mb-2">SAR LEGEND</h4>
            <div className="text-xs text-slate-300 space-y-1">
              <p className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-red-500"></span> LKP</p>
              <p className="flex items-center gap-2"><span className="w-2 h-2 rounded border border-blue-500"></span> Drift T+X</p>
              <p className="flex items-center gap-2"><span className="w-4 h-4 rounded-full bg-blue-500/20 border border-blue-500/50"></span> Search Radius</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
