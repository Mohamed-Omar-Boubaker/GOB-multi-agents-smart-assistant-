import React, { useEffect, useRef, useState } from 'react';
import { apiService } from '../../services/api';
import './DeviceManagerPanel.css';

type DeviceMapping = Record<string, Record<string, string>>;

type DeviceAliasMap = Record<string, string>;

interface DeviceItem {
  device_type: string;
  location: string;
  device_id: string;
}

const toDeviceList = (mapping: DeviceMapping): DeviceItem[] => {
  const items: DeviceItem[] = [];
  Object.entries(mapping).forEach(([deviceType, locations]) => {
    Object.entries(locations).forEach(([location, deviceId]) => {
      items.push({
        device_type: deviceType,
        location,
        device_id: deviceId
      });
    });
  });
  return items;
};

const DeviceManagerPanel: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [devices, setDevices] = useState<DeviceItem[]>([]);
  const [aliases, setAliases] = useState<DeviceAliasMap>({});

  const [deviceType, setDeviceType] = useState('');
  const [location, setLocation] = useState('');
  const [deviceId, setDeviceId] = useState('');

  const [aliasName, setAliasName] = useState('');
  const [aliasLocation, setAliasLocation] = useState('');

  const [fabPosition, setFabPosition] = useState({ x: 0, y: 0 });
  const dragStateRef = useRef({
    dragging: false,
    moved: false,
    startX: 0,
    startY: 0,
    offsetX: 0,
    offsetY: 0
  });

  const fetchDevices = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.getDevicesConfig();
      setDevices(toDeviceList(data.device_mapping || {}));
      setAliases(data.aliases || {});
    } catch (err: any) {
      console.error('Failed to fetch devices', err);
      setError('Failed to load devices');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchDevices();
    }
  }, [isOpen]);

  useEffect(() => {
    const setDefaultPosition = () => {
      const margin = 16;
      const size = 50;
      const gap = 12;
      const x = margin;
      const baseY = window.innerHeight - size - 120;
      const y = Math.max(margin, baseY - (size + gap) * 2);
      setFabPosition({ x, y });
    };

    setDefaultPosition();
    window.addEventListener('resize', setDefaultPosition);

    return () => {
      window.removeEventListener('resize', setDefaultPosition);
    };
  }, []);

  const handleFabPointerDown = (event: React.PointerEvent<HTMLButtonElement>) => {
    const button = event.currentTarget;
    button.setPointerCapture(event.pointerId);

    dragStateRef.current.dragging = true;
    dragStateRef.current.moved = false;
    dragStateRef.current.startX = event.clientX;
    dragStateRef.current.startY = event.clientY;
    dragStateRef.current.offsetX = event.clientX - fabPosition.x;
    dragStateRef.current.offsetY = event.clientY - fabPosition.y;
  };

  const handleFabPointerMove = (event: React.PointerEvent<HTMLButtonElement>) => {
    if (!dragStateRef.current.dragging) return;

    const deltaX = Math.abs(event.clientX - dragStateRef.current.startX);
    const deltaY = Math.abs(event.clientY - dragStateRef.current.startY);
    if (deltaX > 4 || deltaY > 4) {
      dragStateRef.current.moved = true;
    }

    const size = 50;
    const margin = 8;
    const maxX = window.innerWidth - size - margin;
    const maxY = window.innerHeight - size - margin;
    const nextX = Math.min(Math.max(margin, event.clientX - dragStateRef.current.offsetX), maxX);
    const nextY = Math.min(Math.max(margin, event.clientY - dragStateRef.current.offsetY), maxY);

    setFabPosition({ x: nextX, y: nextY });
  };

  const handleFabPointerUp = (event: React.PointerEvent<HTMLButtonElement>) => {
    const button = event.currentTarget;
    button.releasePointerCapture(event.pointerId);

    const wasMoved = dragStateRef.current.moved;
    dragStateRef.current.dragging = false;

    if (!wasMoved) {
      setIsOpen(true);
    }
  };

  const resetForm = () => {
    setDeviceType('');
    setLocation('');
    setDeviceId('');
  };

  const submitDevice = async () => {
    if (!deviceType || !location || !deviceId) {
      setError('Device type, location and device id are required');
      return;
    }

    setError(null);
    try {
      await apiService.upsertDevice({
        device_type: deviceType,
        location,
        device_id: deviceId
      });
      resetForm();
      fetchDevices();
    } catch (err: any) {
      console.error('Failed to save device', err);
      setError('Failed to save device');
    }
  };

  const deleteDevice = async (item: DeviceItem) => {
    setError(null);
    try {
      await apiService.deleteDevice(item.device_type, item.location);
      fetchDevices();
    } catch (err: any) {
      console.error('Failed to delete device', err);
      setError('Failed to delete device');
    }
  };

  const startEdit = (item: DeviceItem) => {
    setDeviceType(item.device_type);
    setLocation(item.location);
    setDeviceId(item.device_id);
  };

  const addAlias = async () => {
    if (!aliasName || !aliasLocation) {
      setError('Alias and location are required');
      return;
    }

    setError(null);
    try {
      await apiService.addDeviceAlias({ alias: aliasName, location: aliasLocation });
      setAliasName('');
      setAliasLocation('');
      fetchDevices();
    } catch (err: any) {
      console.error('Failed to add alias', err);
      setError('Failed to add alias');
    }
  };

  const deleteAlias = async (alias: string) => {
    setError(null);
    try {
      await apiService.deleteDeviceAlias(alias);
      fetchDevices();
    } catch (err: any) {
      console.error('Failed to delete alias', err);
      setError('Failed to delete alias');
    }
  };

  return (
    <>
      <button
        className="device-manager-trigger"
        style={{ left: `${fabPosition.x}px`, top: `${fabPosition.y}px` }}
        onPointerDown={handleFabPointerDown}
        onPointerMove={handleFabPointerMove}
        onPointerUp={handleFabPointerUp}
        onPointerCancel={handleFabPointerUp}
        title="Device Manager"
      >
        💡
      </button>

      {isOpen && (
        <div className="device-manager-overlay" onClick={() => setIsOpen(false)}>
          <div className="device-manager-panel" onClick={(e) => e.stopPropagation()}>
            <div className="device-manager-header">
              <div className="device-manager-title">Device Manager</div>
              <button className="device-manager-close" onClick={() => setIsOpen(false)}>
                X
              </button>
            </div>

            <div className="device-manager-content">
              {error && <div className="device-manager-error">{error}</div>}

              <section className="device-manager-section">
                <h3>Devices</h3>
                {loading ? (
                  <div className="device-manager-loading">Loading...</div>
                ) : (
                  <div className="device-manager-list">
                    {devices.map((item) => (
                      <div key={`${item.device_type}-${item.location}`} className="device-manager-row">
                        <div className="device-manager-row-main">
                          <div className="device-manager-row-title">{item.device_type}</div>
                          <div className="device-manager-row-sub">{item.location} {'->'} {item.device_id}</div>
                        </div>
                        <div className="device-manager-row-actions">
                          <button onClick={() => startEdit(item)}>Edit</button>
                          <button onClick={() => deleteDevice(item)}>Delete</button>
                        </div>
                      </div>
                    ))}
                    {devices.length === 0 && <div className="device-manager-empty">No devices yet</div>}
                  </div>
                )}
              </section>

              <section className="device-manager-section">
                <h3>Add or Update Device</h3>
                <div className="device-manager-form">
                  <input
                    type="text"
                    placeholder="Type (light, shutter, etc.)"
                    value={deviceType}
                    onChange={(e) => setDeviceType(e.target.value)}
                  />
                  <input
                    type="text"
                    placeholder="Location"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                  />
                  <input
                    type="text"
                    placeholder="Device ID"
                    value={deviceId}
                    onChange={(e) => setDeviceId(e.target.value)}
                  />
                  <div className="device-manager-form-actions">
                    <button onClick={submitDevice}>Save</button>
                    <button onClick={resetForm} className="secondary">Clear</button>
                  </div>
                </div>
              </section>

              <section className="device-manager-section">
                <h3>Aliases</h3>
                <div className="device-manager-list">
                  {Object.entries(aliases).map(([alias, loc]) => (
                    <div key={alias} className="device-manager-row">
                      <div className="device-manager-row-main">
                        <div className="device-manager-row-title">{alias}</div>
                        <div className="device-manager-row-sub">{loc}</div>
                      </div>
                      <div className="device-manager-row-actions">
                        <button onClick={() => deleteAlias(alias)}>Delete</button>
                      </div>
                    </div>
                  ))}
                  {Object.keys(aliases).length === 0 && (
                    <div className="device-manager-empty">No aliases yet</div>
                  )}
                </div>
                <div className="device-manager-form">
                  <input
                    type="text"
                    placeholder="Alias"
                    value={aliasName}
                    onChange={(e) => setAliasName(e.target.value)}
                  />
                  <input
                    type="text"
                    placeholder="Location target"
                    value={aliasLocation}
                    onChange={(e) => setAliasLocation(e.target.value)}
                  />
                  <div className="device-manager-form-actions">
                    <button onClick={addAlias}>Add Alias</button>
                  </div>
                </div>
              </section>
            </div>

            <div className="device-manager-footer">
              <button onClick={fetchDevices} className="secondary">Refresh</button>
              <button onClick={() => setIsOpen(false)}>Done</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default DeviceManagerPanel;
