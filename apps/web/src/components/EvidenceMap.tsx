import { useMemo } from 'react';
import Map, { Source, Layer, Marker } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Target, Navigation, Wind } from 'lucide-react';

interface EvidenceMapProps {
  type: string;
  data: any;
}

const DARK_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

export default function EvidenceMap({ type, data }: EvidenceMapProps) {
  // Extract coordinates based on evidence type and data shape
  const { viewState, features, markers } = useMemo(() => {
    let lat = 13.0;
    let lon = 80.0;
    let zoom = 8;
    const fts: any[] = [];
    const mkrs: any[] = [];

    try {
      if (data) {
        if (data.lat !== undefined && data.lon !== undefined) {
          lat = data.lat;
          lon = data.lon;
        } else if (data.origin_lat !== undefined && data.origin_lon !== undefined) {
          lat = data.origin_lat;
          lon = data.origin_lon;
        }
      }

      if (type === 'pfz' && data?.pfz_zones) {
        mkrs.push({ lat, lon, type: 'vessel' });
        if (data.pfz_zones.length > 0) {
          const pfz = data.pfz_zones[0];
          mkrs.push({ lat: pfz.lat, lon: pfz.lon, type: 'pfz', distance: pfz.distance_nm });
          
          fts.push({
            type: 'Feature',
            geometry: { type: 'LineString', coordinates: [[lon, lat], [pfz.lon, pfz.lat]] },
            properties: { type: 'route' }
          });
          // Mock PFZ bounding area
          fts.push({
            type: 'Feature',
            geometry: { type: 'Polygon', coordinates: [[[pfz.lon - 0.1, pfz.lat - 0.1], [pfz.lon + 0.1, pfz.lat - 0.1], [pfz.lon + 0.1, pfz.lat + 0.1], [pfz.lon - 0.1, pfz.lat + 0.1], [pfz.lon - 0.1, pfz.lat - 0.1]]] },
            properties: { type: 'pfz_area' }
          });
          // Mock SST gradient points
          fts.push({
            type: 'Feature',
            geometry: { type: 'Point', coordinates: [pfz.lon, pfz.lat] },
            properties: { type: 'sst_heatmap' }
          });
        }
      } else if (type === 'weather' || type === 'wave') {
        mkrs.push({ lat, lon, type: 'weather', wind_speed: data?.wind_speed_ms, wave: data?.wave_height_m });
        // Hazard Zone
        fts.push({
          type: 'Feature',
          geometry: { type: 'Polygon', coordinates: [[[lon - 0.5, lat - 0.5], [lon + 0.5, lat - 0.5], [lon + 0.5, lat + 0.5], [lon - 0.5, lat + 0.5], [lon - 0.5, lat - 0.5]]] },
          properties: { type: 'hazard_area' }
        });
        // Wind arrows grid
        const wd = data?.wind_direction_deg || 45;
        mkrs.push({ lat: lat + 0.1, lon: lon + 0.1, type: 'wind_arrow', bearing: wd });
        mkrs.push({ lat: lat - 0.1, lon: lon - 0.1, type: 'wind_arrow', bearing: wd });
        mkrs.push({ lat: lat + 0.1, lon: lon - 0.1, type: 'wind_arrow', bearing: wd });
        mkrs.push({ lat: lat - 0.1, lon: lon + 0.1, type: 'wind_arrow', bearing: wd });
        zoom = 9;
      } else if (type === 'sar_drift' || type === 'sar_search_area' || type === 'sar') {
        if (data?.lkp_lat) {
          lat = data.lkp_lat;
          lon = data.lkp_lon;
          mkrs.push({ lat, lon, type: 'incident' });
          // SAR predicted drift
          if (data?.predictions && data.predictions.length > 0) {
            const pathCoords = [[lon, lat]];
            data.predictions.forEach((p: any) => pathCoords.push([p.lon, p.lat]));
            fts.push({
              type: 'Feature',
              geometry: { type: 'LineString', coordinates: pathCoords },
              properties: { type: 'route', routeType: 'sar_drift' }
            });
            const lastPred = data.predictions[data.predictions.length - 1];
            mkrs.push({ lat: lastPred.lat, lon: lastPred.lon, type: 'default' });
            
            fts.push({
              type: 'Feature',
              geometry: { type: 'Polygon', coordinates: [[[lastPred.lon - 0.2, lastPred.lat - 0.2], [lastPred.lon + 0.2, lastPred.lat - 0.2], [lastPred.lon + 0.2, lastPred.lat + 0.2], [lastPred.lon - 0.2, lastPred.lat + 0.2], [lastPred.lon - 0.2, lastPred.lat - 0.2]]] },
              properties: { type: 'sar_area' }
            });
          }
          zoom = 9;
        }

      } else {
        mkrs.push({ lat, lon, type: 'default' });
      }
    } catch (e) {
      console.error("EvidenceMap parsing error", e);
    }

    return {
      viewState: { latitude: lat, longitude: lon, zoom, pitch: 0, bearing: 0 },
      features: fts,
      markers: mkrs
    };
  }, [type, data]);

  const geojson = {
    type: 'FeatureCollection',
    features
  };

  return (
    <div className="w-full h-64 bg-slate-800 rounded-lg overflow-hidden relative border border-slate-300">
      <Map
        initialViewState={viewState}
        mapStyle={DARK_STYLE}
        interactive={false}
      >
        <Source type="geojson" data={geojson as any}>
          {/* MARINE CONDITION OVERLAYS */}
          <Layer
            id="marine-sst-layer"
            type="heatmap"
            paint={{
              'heatmap-weight': 1,
              'heatmap-intensity': 1,
              'heatmap-color': [
                'interpolate',
                ['linear'],
                ['heatmap-density'],
                0, 'rgba(0, 0, 255, 0)',
                0.2, 'royalblue',
                0.4, 'cyan',
                0.6, 'lime',
                0.8, 'yellow',
                1, 'red'
              ],
              'heatmap-radius': 60,
              'heatmap-opacity': 0.4
            }}
            filter={['==', 'type', 'sst_heatmap']}
          />
          
          <Layer
            id="weather-hazard-area"
            type="fill"
            paint={{
              'fill-color': '#ef4444',
              'fill-opacity': 0.15,
              'fill-outline-color': '#f87171'
            }}
            filter={['==', 'type', 'hazard_area']}
          />
          
          <Layer
            id="pfz-area"
            type="fill"
            paint={{
              'fill-color': '#14b8a6',
              'fill-opacity': 0.2,
              'fill-outline-color': '#0d9488'
            }}
            filter={['==', 'type', 'pfz_area']}
          />
          
          <Layer
            id="sar-search-area"
            type="fill"
            paint={{
              'fill-color': '#f59e0b',
              'fill-opacity': 0.2,
              'fill-outline-color': '#d97706'
            }}
            filter={['==', 'type', 'sar_area']}
          />

          <Layer
            id="route-line"
            type="line"
            paint={{
              'line-color': ['match', ['get', 'routeType'], 'sar_drift', '#f59e0b', '#2dd4bf'],
              'line-width': 3,
              'line-dasharray': [2, 2]
            }}
            filter={['==', 'type', 'route']}
          />
        </Source>

        {markers.map((m, i) => (
          <Marker key={i} latitude={m.lat} longitude={m.lon} anchor="bottom" rotation={m.bearing || 0}>
            {m.type === 'vessel' && (
              <div className="flex flex-col items-center">
                <Navigation size={16} className="text-white fill-slate-800" />
                <span className="text-[10px] bg-black/60 text-white px-1 mt-1 rounded font-mono">VESSEL</span>
              </div>
            )}
            {m.type === 'pfz' && (
              <div className="flex flex-col items-center">
                <Target size={20} className="text-teal-400 fill-teal-900/50" />
                <span className="text-[10px] bg-teal-900/80 text-teal-100 px-1 mt-1 rounded font-mono border border-teal-500/50 whitespace-nowrap">
                  PFZ {m.distance ? `(${m.distance.toFixed(1)} NM)` : ''}
                </span>
              </div>
            )}
            {m.type === 'weather' && (
              <div className="flex flex-col items-center">
                <Wind size={20} className="text-blue-400 fill-blue-900/50" />
                <span className="text-[10px] bg-blue-900/80 text-blue-100 px-1 mt-1 rounded font-mono border border-blue-500/50 whitespace-nowrap">
                  {m.wind_speed ? `${m.wind_speed} m/s` : 'Weather'} {m.wave ? `| ${m.wave}m` : ''}
                </span>
              </div>
            )}
            {m.type === 'incident' && (
              <div className="flex flex-col items-center">
                <div className="w-4 h-4 bg-red-500 rounded-full animate-pulse border-2 border-white" />
                <span className="text-[10px] bg-red-900/80 text-red-100 px-1 mt-1 rounded font-mono border border-red-500/50">LKP / INCIDENT</span>
              </div>
            )}
            {m.type === 'wind_arrow' && (
              <div className="text-blue-400 opacity-60">
                <Navigation size={14} className="fill-blue-400" />
              </div>
            )}
            {m.type === 'default' && (
              <div className="w-3 h-3 bg-slate-400 rounded-full border-2 border-white" />
            )}
          </Marker>
        ))}
      </Map>
      
      <div className="absolute bottom-2 right-2 px-2 py-1 bg-black/60 backdrop-blur text-white text-[9px] font-mono tracking-widest rounded border border-white/20">
        PROTOTYPE VISUALIZATION
      </div>
    </div>
  );
}
