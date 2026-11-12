import React, { useState, useEffect } from 'react';
import {
  Radar,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Sliders,
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { NetworkInfoCard } from '../components/network/NetworkInfoCard';
import { ScanProgress } from '../components/network/ScanProgress';
import { DeviceCard } from '../components/devices/DeviceCard';
import { DeviceDetails } from '../components/devices/DeviceDetails';
import {
  useNetworkInfo,
  useNetworkInterfaces,
  useStartScan,
  useCancelScan,
  useValidateSubnet,
} from '../hooks/useNetwork';
import { useDevices } from '../hooks/useDevices';
import { useNetworkStore } from '../store/networkStore';
import type { Device } from '../types/device';

export const NetworkScanner: React.FC = () => {
  const { data: netInfo, isLoading: infoLoading } = useNetworkInfo();
  const { data: interfaces = [] } = useNetworkInterfaces();
  const { data: devicesData } = useDevices({ page_size: 100 });
  const scanStatus = useNetworkStore((s) => s.scanStatus);

  const startScan = useStartScan();
  const cancelScan = useCancelScan();
  const validateSubnet = useValidateSubnet();

  const [subnetCidr, setSubnetCidr] = useState('');
  const [selectedIface, setSelectedIface] = useState('');
  const [authorizedConfirm, setAuthorizedConfirm] = useState(true);
  const [scanPorts, setScanPorts] = useState(true);
  const [enableOnvif, setEnableOnvif] = useState(true);
  const [enableMdns, setEnableMdns] = useState(true);
  const [enableSsdp, setEnableSsdp] = useState(true);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);

  useEffect(() => {
    if (netInfo?.subnet_cidr && !subnetCidr) {
      setSubnetCidr(netInfo.subnet_cidr);
    }
    if (netInfo?.interface_name && !selectedIface) {
      setSelectedIface(netInfo.interface_name);
    }
  }, [netInfo, subnetCidr, selectedIface]);

  const handleValidate = () => {
    if (!subnetCidr.trim()) return;
    validateSubnet.mutate(subnetCidr.trim());
  };

  const handleStartScan = (e: React.FormEvent) => {
    e.preventDefault();
    if (!authorizedConfirm) return;
    startScan.mutate({
      subnet_cidr: subnetCidr.trim() || netInfo?.subnet_cidr || null,
      interface_name: selectedIface || netInfo?.interface_name || null,
      authorized_confirmation: authorizedConfirm,
      scan_ports: scanPorts,
      enable_onvif: enableOnvif,
      enable_mdns: enableMdns,
      enable_ssdp: enableSsdp,
    });
  };

  const discoveredDevices = devicesData?.items || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          LAN &amp; CCTV Network Scanner
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
          Multi-stage active ARP, TCP/UDP port, ONVIF WS-Discovery, mDNS, and SSDP scanner
        </p>
      </div>

      <NetworkInfoCard info={netInfo} isLoading={infoLoading} />

      <ScanProgress
        status={scanStatus}
        onCancel={() => cancelScan.mutate()}
        isCancelling={cancelScan.isPending}
      />

      <Card
        title="Configure & Launch Network Scan"
        subtitle="Restricted strictly to RFC1918 private local network subnets"
        action={
          <Badge variant="info">
            <ShieldCheck className="w-3.5 h-3.5 mr-1" />
            Safe Rate-Limited Discovery
          </Badge>
        }
      >
        <form onSubmit={handleStartScan} className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Target Subnet CIDR (RFC1918 Private Range)
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={subnetCidr}
                  onChange={(e) => setSubnetCidr(e.target.value)}
                  placeholder="e.g. 192.168.1.0/24"
                  className="flex-1 px-3 py-2 text-sm font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleValidate}
                  isLoading={validateSubnet.isPending}
                >
                  Validate CIDR
                </Button>
              </div>
              {validateSubnet.data && (
                <div
                  className={`flex items-center gap-1.5 text-xs mt-1.5 ${
                    validateSubnet.data.valid
                      ? 'text-emerald-600 dark:text-emerald-400'
                      : 'text-red-600 dark:text-red-400'
                  }`}
                >
                  {validateSubnet.data.valid ? (
                    <CheckCircle2 className="w-3.5 h-3.5" />
                  ) : (
                    <AlertTriangle className="w-3.5 h-3.5" />
                  )}
                  <span>
                    {validateSubnet.data.message} (
                    {validateSubnet.data.host_count} hosts)
                  </span>
                </div>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Network Interface Adapter
              </label>
              <select
                value={selectedIface}
                onChange={(e) => setSelectedIface(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
              >
                <option value="">
                  Auto-Select Primary ({netInfo?.interface_name || 'Default'})
                </option>
                {interfaces.map((iface) => {
                  const name = iface.name || iface.interface_name || 'eth0';
                  return (
                    <option key={`${name}-${iface.ip_address}`} value={name}>
                      {name} — {iface.ip_address} ({iface.subnet_cidr})
                    </option>
                  );
                })}
              </select>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 space-y-3">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-700 dark:text-slate-300">
              <Sliders className="w-4 h-4 text-blue-600" />
              <span>Discovery Stages &amp; Protocol Probes</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={scanPorts}
                  onChange={(e) => setScanPorts(e.target.checked)}
                  className="rounded border-slate-300 text-blue-600"
                />
                <span>CCTV &amp; Admin Port Scan (80, 443, 554, 8000, 37777)</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={enableOnvif}
                  onChange={(e) => setEnableOnvif(e.target.checked)}
                  className="rounded border-slate-300 text-blue-600"
                />
                <span>ONVIF WS-Discovery Multicast Probe</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={enableMdns}
                  onChange={(e) => setEnableMdns(e.target.checked)}
                  className="rounded border-slate-300 text-blue-600"
                />
                <span>mDNS / Zeroconf Service Discovery</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={enableSsdp}
                  onChange={(e) => setEnableSsdp(e.target.checked)}
                  className="rounded border-slate-300 text-blue-600"
                />
                <span>SSDP / UPnP Media Device Discovery</span>
              </label>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-slate-200 dark:border-slate-800">
            <label className="flex items-center gap-2.5 text-xs text-slate-700 dark:text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={authorizedConfirm}
                onChange={(e) => setAuthorizedConfirm(e.target.checked)}
                required
                className="w-4 h-4 rounded border-slate-300 text-blue-600"
              />
              <span>
                I confirm I am authorized to scan this local private network for device administration and recovery.
              </span>
            </label>

            <Button
              type="submit"
              variant="primary"
              leftIcon={<Radar className="w-4 h-4" />}
              disabled={!authorizedConfirm || scanStatus.is_running}
              isLoading={startScan.isPending}
            >
              {scanStatus.is_running ? 'Scan in Progress...' : 'Start Full LAN Scan'}
            </Button>
          </div>
        </form>
      </Card>

      {/* Live Discovered Results */}
      <Card
        title={`Discovered Network Hosts (${discoveredDevices.length})`}
        subtitle="Click Connect & View Live on any discovered IP camera to view its real-time stream"
      >
        {discoveredDevices.length === 0 ? (
          <div className="py-10 text-center text-sm text-slate-500 dark:text-slate-400">
            No hosts discovered yet. Click &ldquo;Start Full LAN Scan&rdquo; above to scan your subnet.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {discoveredDevices.map((dev) => (
              <DeviceCard
                key={dev.id || dev.ip_address}
                device={dev}
                onSelect={setSelectedDevice}
              />
            ))}
          </div>
        )}
      </Card>

      <DeviceDetails
        device={selectedDevice}
        isOpen={Boolean(selectedDevice)}
        onClose={() => setSelectedDevice(null)}
      />
    </div>
  );
};
