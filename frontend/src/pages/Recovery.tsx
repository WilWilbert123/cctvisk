import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  KeyRound,
  Lock,
  ShieldCheck,
  CheckCircle2,
  Trash2,
  ClipboardCheck,
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { RecoveryGuide } from '../components/recovery/RecoveryGuide';
import { recoveryService } from '../services/recoveryService';
import { useDevices } from '../hooks/useDevices';
import { useNetworkStore } from '../store/networkStore';

export const Recovery: React.FC = () => {
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const addNotification = useNetworkStore((s) => s.addNotification);

  const initialDeviceId = Number(searchParams.get('deviceId')) || 0;
  const [selectedDeviceId, setSelectedDeviceId] = useState<number>(initialDeviceId);
  const [selectedVendorTab, setSelectedVendorTab] = useState<string>('Hikvision');

  const [vaultUser, setVaultUser] = useState('admin');
  const [vaultPassword, setVaultPassword] = useState('');
  const [vaultPort, setVaultPort] = useState(554);
  const [vaultNotes, setVaultNotes] = useState('');
  const [vaultConsent, setVaultConsent] = useState(false);

  const [logMethod, setLogMethod] = useState('Official Vendor Reset Tool');
  const [logStatus, setLogStatus] = useState('completed');
  const [logNotes, setLogNotes] = useState('');

  const { data: devicesData } = useDevices({ page_size: 100 });
  const { data: allGuides = [] } = useQuery({
    queryKey: ['recovery', 'guides'],
    queryFn: () => recoveryService.getAllGuides(),
  });

  const { data: deviceRecovery } = useQuery({
    queryKey: ['recovery', 'device', selectedDeviceId],
    queryFn: () => recoveryService.getDeviceGuide(selectedDeviceId),
    enabled: selectedDeviceId > 0,
  });

  useEffect(() => {
    if (deviceRecovery?.manufacturer) {
      setSelectedVendorTab(deviceRecovery.manufacturer);
    }
  }, [deviceRecovery]);

  const saveVaultMutation = useMutation({
    mutationFn: recoveryService.saveVaultCredentials,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recovery'] });
      queryClient.invalidateQueries({ queryKey: ['cameras'] });
      setVaultPassword('');
      addNotification({
        type: 'success',
        title: 'Credentials Encrypted in Vault',
        message: 'Saved with AES-GCM encryption for authorized access.',
      });
    },
  });

  const deleteVaultMutation = useMutation({
    mutationFn: (id: number) => recoveryService.deleteVaultCredentials(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recovery'] });
      queryClient.invalidateQueries({ queryKey: ['cameras'] });
      addNotification({
        type: 'info',
        title: 'Vault Entry Deleted',
        message: 'Stored credentials removed from local vault.',
      });
    },
  });

  const recordRecoveryMutation = useMutation({
    mutationFn: recoveryService.createRecoveryRecord,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recovery'] });
      queryClient.invalidateQueries({ queryKey: ['history'] });
      setLogNotes('');
      addNotification({
        type: 'success',
        title: 'Recovery Audit Logged',
        message: 'Recorded recovery action in audit history.',
      });
    },
  });

  const activeGuide =
    deviceRecovery?.guide ||
    allGuides.find(
      (g) => g.manufacturer.toLowerCase() === selectedVendorTab.toLowerCase()
    ) ||
    allGuides[0];

  const handleSaveVault = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDeviceId || !vaultConsent) return;
    saveVaultMutation.mutate({
      device_id: selectedDeviceId,
      username: vaultUser,
      password: vaultPassword,
      port: Number(vaultPort) || 554,
      notes: vaultNotes,
      explicit_user_consent: vaultConsent,
    });
  };

  const handleRecordAudit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDeviceId) return;
    recordRecoveryMutation.mutate({
      device_id: selectedDeviceId,
      manufacturer: deviceRecovery?.manufacturer || selectedVendorTab,
      method_used: logMethod,
      status: logStatus,
      notes: logNotes,
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Official CCTV Password &amp; Access Recovery Assistant
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Manufacturer-sanctioned recovery workflows, hardware reset procedures, and AES-GCM Encrypted Credential Vault
          </p>
        </div>

        <Badge variant="success">
          <ShieldCheck className="w-4 h-4 mr-1" />
          100% Authorized Vendor Workflows Only
        </Badge>
      </div>

      {/* Device Selector & Vendor Tabs */}
      <Card title="Select Target CCTV / NVR Device or Manufacturer">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Select Discovered LAN Device (Optional)
            </label>
            <select
              value={selectedDeviceId}
              onChange={(e) => setSelectedDeviceId(Number(e.target.value))}
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
            >
              <option value={0}>-- Browse Manufacturer Guides Directly --</option>
              {(devicesData?.items || []).map((d) => (
                <option key={d.id} value={d.id}>
                  {d.ip_address} — {d.label || d.manufacturer || d.category}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Manufacturer Recovery Knowledgebase
            </label>
            <div className="flex flex-wrap gap-1.5">
              {(allGuides.length > 0
                ? allGuides.map((g) => g.manufacturer)
                : ['Hikvision', 'Dahua', 'Axis', 'Uniview', 'Reolink', 'Generic ONVIF']
              ).map((vendor) => (
                <button
                  key={vendor}
                  type="button"
                  onClick={() => {
                    setSelectedVendorTab(vendor);
                  }}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    selectedVendorTab.toLowerCase() === vendor.toLowerCase()
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200'
                  }`}
                >
                  {vendor}
                </button>
              ))}
            </div>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7">
          {activeGuide ? (
            <RecoveryGuide guide={activeGuide} />
          ) : (
            <Card title="Loading Official Manufacturer Guide">
              <p className="text-xs text-slate-500">
                Select a manufacturer above to view official recovery steps.
              </p>
            </Card>
          )}
        </div>

        {/* Encrypted Vault & Recovery Log (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          <Card
            title="Encrypted Credential Vault (AES-GCM)"
            subtitle="Store recovered or authorized credentials locally for 1-click Live Stream connection"
          >
            {selectedDeviceId === 0 ? (
              <p className="text-xs text-slate-500 py-4">
                Select a discovered device from the dropdown above to store or manage its encrypted Vault credentials.
              </p>
            ) : (
              <form onSubmit={handleSaveVault} className="space-y-3.5">
                {deviceRecovery?.vault_status?.has_credentials && (
                  <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2 text-emerald-800 dark:text-emerald-200">
                      <CheckCircle2 className="w-4 h-4" />
                      <span>
                        Stored Username:{' '}
                        <strong>{deviceRecovery.vault_status.username}</strong> (
                        {deviceRecovery.vault_status.encryption_algorithm})
                      </span>
                    </div>
                    <Button
                      type="button"
                      size="xs"
                      variant="danger"
                      leftIcon={<Trash2 className="w-3 h-3" />}
                      onClick={() => deleteVaultMutation.mutate(selectedDeviceId)}
                    >
                      Clear
                    </Button>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium mb-1">
                      Username
                    </label>
                    <input
                      type="text"
                      required
                      value={vaultUser}
                      onChange={(e) => setVaultUser(e.target.value)}
                      className="w-full px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium mb-1">
                      Recovered Password
                    </label>
                    <input
                      type="password"
                      required
                      value={vaultPassword}
                      onChange={(e) => setVaultPassword(e.target.value)}
                      placeholder="Enter new/recovered password"
                      className="w-full px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium mb-1">
                      RTSP / Admin Port
                    </label>
                    <input
                      type="number"
                      value={vaultPort}
                      onChange={(e) => setVaultPort(Number(e.target.value))}
                      className="w-full px-3 py-1.5 text-sm font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium mb-1">
                      Vault Note
                    </label>
                    <input
                      type="text"
                      value={vaultNotes}
                      onChange={(e) => setVaultNotes(e.target.value)}
                      placeholder="Reset via SADP Tool"
                      className="w-full px-3 py-1.5 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                    />
                  </div>
                </div>

                <label className="flex items-start gap-2 text-xs text-slate-600 dark:text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    required
                    checked={vaultConsent}
                    onChange={(e) => setVaultConsent(e.target.checked)}
                    className="mt-0.5 rounded border-slate-300 text-blue-600"
                  />
                  <span>
                    I explicitly consent to encrypting and storing these credentials in the local AES-GCM Vault on this machine.
                  </span>
                </label>

                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  className="w-full"
                  leftIcon={<Lock className="w-4 h-4" />}
                  isLoading={saveVaultMutation.isPending}
                >
                  Encrypt &amp; Save to Vault
                </Button>
              </form>
            )}
          </Card>

          <Card
            title="Log Recovery Audit Record"
            subtitle="Document completed password reset or firmware recovery actions"
          >
            {selectedDeviceId === 0 ? (
              <p className="text-xs text-slate-500 py-3">
                Select a target device above to record a recovery audit entry.
              </p>
            ) : (
              <form onSubmit={handleRecordAudit} className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium mb-1">
                      Recovery Method Used
                    </label>
                    <select
                      value={logMethod}
                      onChange={(e) => setLogMethod(e.target.value)}
                      className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                    >
                      <option value="Official Vendor Reset Tool">
                        Official Vendor Reset Tool (SADP / ConfigTool)
                      </option>
                      <option value="Physical Hardware Reset Button">
                        Physical Hardware Reset Button
                      </option>
                      <option value="Vendor Technical Support XML/QR">
                        Vendor Technical Support XML/QR Code
                      </option>
                      <option value="NVR Local Console Reset">
                        NVR Local Monitor Console Reset
                      </option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium mb-1">
                      Outcome Status
                    </label>
                    <select
                      value={logStatus}
                      onChange={(e) => setLogStatus(e.target.value)}
                      className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                    >
                      <option value="completed">Completed Successfully</option>
                      <option value="in_progress">In Progress</option>
                      <option value="requires_support">Awaiting Vendor Support</option>
                    </select>
                  </div>
                </div>
                <textarea
                  rows={2}
                  value={logNotes}
                  onChange={(e) => setLogNotes(e.target.value)}
                  placeholder="Enter technician notes..."
                  className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
                />
                <Button
                  type="submit"
                  variant="outline"
                  size="sm"
                  className="w-full"
                  leftIcon={<ClipboardCheck className="w-4 h-4" />}
                  isLoading={recordRecoveryMutation.isPending}
                >
                  Save Audit Log Entry
                </Button>
              </form>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};
