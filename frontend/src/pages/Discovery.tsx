import React, { useState } from 'react';
import {
  Compass,
  Radar,
  Search,
  CheckCircle2,
  Play,
  Layers,
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import {
  useDiscoveryResults,
  useRunDiscoveryProbe,
  usePortScan,
  useOnvifInterrogate,
} from '../hooks/useDiscovery';
import { useDeviceStore } from '../store/deviceStore';

export const Discovery: React.FC = () => {
  const { data: results } = useDiscoveryResults();
  const runProbe = useRunDiscoveryProbe();
  const portScan = usePortScan();
  const onvifInterrogate = useOnvifInterrogate();
  const setActiveLiveCamera = useDeviceStore((s) => s.setActiveLiveCamera);

  const [targetIp, setTargetIp] = useState('');
  const [onvifIp, setOnvifIp] = useState('');
  const [onvifPort, setOnvifPort] = useState(80);
  const [onvifUser, setOnvifUser] = useState('admin');
  const [onvifPass, setOnvifPass] = useState('');

  const handlePortScan = (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetIp.trim()) return;
    portScan.mutate({ ip_address: targetIp.trim() });
  };

  const handleOnvifQuery = (e: React.FormEvent) => {
    e.preventDefault();
    if (!onvifIp.trim()) return;
    onvifInterrogate.mutate({
      ip_address: onvifIp.trim(),
      port: Number(onvifPort) || 80,
      username: onvifUser.trim() || undefined,
      password: onvifPass || undefined,
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Protocol Discovery &amp; ONVIF / Port Diagnostics
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Active ONVIF WS-Discovery, mDNS/Zeroconf, SSDP/UPnP, and targeted CCTV port interrogation
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          leftIcon={<Compass className="w-4 h-4" />}
          isLoading={runProbe.isPending}
          onClick={() => runProbe.mutate(['onvif', 'mdns', 'ssdp', 'http'])}
        >
          Run Broadcast Discovery Probe
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Targeted CCTV Port Scanner */}
        <Card
          title="Targeted Host Port Scanner"
          subtitle="Probe common CCTV, RTSP, ONVIF, and web admin ports on a local IPv4 host"
        >
          <form onSubmit={handlePortScan} className="space-y-4">
            <div className="flex gap-2">
              <input
                type="text"
                required
                value={targetIp}
                onChange={(e) => setTargetIp(e.target.value)}
                placeholder="Enter local IP e.g. 192.168.1.64"
                className="flex-1 px-3 py-2 text-sm font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
              />
              <Button
                type="submit"
                variant="primary"
                size="sm"
                leftIcon={<Search className="w-4 h-4" />}
                isLoading={portScan.isPending}
              >
                Scan Ports
              </Button>
            </div>

            {portScan.data && (
              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 space-y-2.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold">
                    Host {portScan.data.ip_address} — Open Ports (
                    {portScan.data.open_ports?.length || 0})
                  </span>
                  <Button
                    type="button"
                    size="xs"
                    variant="primary"
                    leftIcon={<Play className="w-3 h-3" />}
                    onClick={() =>
                      setActiveLiveCamera({
                        id: Date.now(),
                        ip_address: portScan.data.ip_address,
                        label: `Camera ${portScan.data.ip_address}`,
                        rtsp_port: 554,
                        http_port: 80,
                        is_online: true,
                      })
                    }
                  >
                    Connect Live Stream
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {(portScan.data.open_ports || []).length === 0 ? (
                    <span className="text-xs text-slate-500">
                      No open CCTV/admin ports responded on {portScan.data.ip_address}.
                    </span>
                  ) : (
                    portScan.data.open_ports.map((p) => (
                      <Badge key={p.port} variant="success" className="font-mono">
                        {p.port}/{p.protocol} ({p.service})
                      </Badge>
                    ))
                  )}
                </div>
              </div>
            )}
          </form>
        </Card>

        {/* ONVIF Device Interrogator */}
        <Card
          title="ONVIF Device & Media Profile Interrogator"
          subtitle="Query GetDeviceInformation, GetCapabilities, and RTSP Media Profiles"
        >
          <form onSubmit={handleOnvifQuery} className="space-y-3.5">
            <div className="grid grid-cols-3 gap-2.5">
              <div className="col-span-2">
                <input
                  type="text"
                  required
                  value={onvifIp}
                  onChange={(e) => setOnvifIp(e.target.value)}
                  placeholder="Camera IP e.g. 192.168.1.64"
                  className="w-full px-3 py-2 text-sm font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                />
              </div>
              <div>
                <input
                  type="number"
                  value={onvifPort}
                  onChange={(e) => setOnvifPort(Number(e.target.value))}
                  placeholder="Port 80"
                  className="w-full px-3 py-2 text-sm font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2.5">
              <input
                type="text"
                value={onvifUser}
                onChange={(e) => setOnvifUser(e.target.value)}
                placeholder="Username (admin)"
                className="px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
              />
              <input
                type="password"
                value={onvifPass}
                onChange={(e) => setOnvifPass(e.target.value)}
                placeholder="Password (optional)"
                className="px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
              />
              <Button
                type="submit"
                variant="primary"
                size="sm"
                leftIcon={<Layers className="w-4 h-4" />}
                isLoading={onvifInterrogate.isPending}
              >
                Query ONVIF
              </Button>
            </div>

            {onvifInterrogate.data && (
              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-semibold">
                    {onvifInterrogate.data.manufacturer || 'ONVIF Endpoint'}{' '}
                    {onvifInterrogate.data.model || ''}
                  </span>
                  <Badge
                    variant={onvifInterrogate.data.reachable ? 'success' : 'warning'}
                  >
                    {onvifInterrogate.data.reachable ? 'Reachable' : 'No SOAP Response'}
                  </Badge>
                </div>
                {onvifInterrogate.data.message && (
                  <p className="text-slate-500">{onvifInterrogate.data.message}</p>
                )}
              </div>
            )}
          </form>
        </Card>
      </div>

      {/* Multicast Discovery Results */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <Card
          title={`ONVIF WS-Discovery (${results?.onvif?.length || 0})`}
          subtitle="UDP 3702 SOAP ProbeMatches"
        >
          {!results?.onvif || results.onvif.length === 0 ? (
            <p className="text-xs text-slate-500 py-6 text-center">
              No ONVIF broadcast responses yet. Click &ldquo;Run Broadcast Discovery Probe&rdquo;.
            </p>
          ) : (
            <div className="space-y-2">
              {results.onvif.map((item, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 flex items-center justify-between text-xs"
                >
                  <div>
                    <p className="font-mono font-semibold">{item.ip_address}</p>
                    <p className="text-slate-500">
                      {item.manufacturer || 'ONVIF Camera'} {item.model || ''}
                    </p>
                  </div>
                  <Button
                    size="xs"
                    variant="primary"
                    onClick={() =>
                      setActiveLiveCamera({
                        id: idx + 1,
                        ip_address: item.ip_address,
                        label: item.manufacturer || item.ip_address,
                        rtsp_port: 554,
                        http_port: item.port || 80,
                        is_online: true,
                      })
                    }
                  >
                    View Live
                  </Button>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card
          title={`mDNS / Zeroconf (${results?.mdns?.length || 0})`}
          subtitle="UDP 5353 _rtsp._tcp / _http._tcp"
        >
          {!results?.mdns || results.mdns.length === 0 ? (
            <p className="text-xs text-slate-500 py-6 text-center">
              No mDNS service announcements captured yet.
            </p>
          ) : (
            <div className="space-y-2">
              {results.mdns.map((item, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 text-xs"
                >
                  <p className="font-mono font-semibold">{item.ip_address}</p>
                  <p className="text-slate-500">
                    {item.service_name || item.hostname || item.service_type}
                  </p>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card
          title={`SSDP / UPnP (${results?.ssdp?.length || 0})`}
          subtitle="UDP 1900 M-SEARCH responses"
        >
          {!results?.ssdp || results.ssdp.length === 0 ? (
            <p className="text-xs text-slate-500 py-6 text-center">
              No UPnP/SSDP descriptors captured yet.
            </p>
          ) : (
            <div className="space-y-2">
              {results.ssdp.map((item, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 text-xs"
                >
                  <p className="font-mono font-semibold">{item.ip_address}</p>
                  <p className="text-slate-500 truncate">
                    {item.server || item.st || item.location}
                  </p>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};
