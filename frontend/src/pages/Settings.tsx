import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import {
  Sun,
  Moon,
  Monitor,
  Database,
  Download,
  Shield,
  Key,
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { useTheme } from '../hooks/useTheme';
import { useAppSettings } from '../hooks/useMonitoring';
import { monitoringService } from '../services/monitoringService';
import { useSettingsStore } from '../store/settingsStore';
import { useNetworkStore } from '../store/networkStore';

export const Settings: React.FC = () => {
  const { theme, setTheme } = useTheme();
  const { data: settingsData } = useAppSettings();
  const apiToken = useSettingsStore((s) => s.apiToken);
  const setApiToken = useSettingsStore((s) => s.setApiToken);
  const addNotification = useNetworkStore((s) => s.addNotification);

  const [tokenInput, setTokenInput] = useState(apiToken);

  const backupMutation = useMutation({
    mutationFn: () => monitoringService.createBackup(),
    onSuccess: (res) => {
      addNotification({
        type: 'success',
        title: 'Database Backup Created',
        message: res.backup_path || 'SQLite backup saved successfully.',
      });
    },
  });

  const exportMutation = useMutation({
    mutationFn: () => monitoringService.exportInventory(),
    onSuccess: (data) => {
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cctv-inventory-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      addNotification({
        type: 'success',
        title: 'Inventory Exported',
        message: `Exported ${data.total_devices ?? 0} devices to JSON.`,
      });
    },
  });

  const handleSaveToken = (e: React.FormEvent) => {
    e.preventDefault();
    setApiToken(tokenInput.trim());
    addNotification({
      type: 'success',
      title: 'LAN Pairing Token Updated',
      message: 'API token saved to local browser session.',
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          System Settings, Security &amp; Database Backup
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
          Appearance preferences, LAN pairing token, AES-GCM Vault status, and inventory export
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Appearance & Theme */}
        <Card
          title="Interface Appearance"
          subtitle="Default Light Mode with full Dark Mode & System sync support"
        >
          <div className="grid grid-cols-3 gap-3">
            {[
              { id: 'light', label: 'Light Mode', icon: Sun },
              { id: 'dark', label: 'Dark Mode', icon: Moon },
              { id: 'system', label: 'System Sync', icon: Monitor },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                type="button"
                onClick={() => setTheme(id as any)}
                className={`flex flex-col items-center justify-center gap-2 p-4 rounded-xl border text-xs font-semibold transition-all ${
                  theme === id
                    ? 'border-blue-600 bg-blue-50/70 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 dark:border-blue-500'
                    : 'border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span>{label}</span>
              </button>
            ))}
          </div>
        </Card>

        {/* LAN Access & Pairing Token */}
        <Card
          title="Mobile / LAN Pairing Token"
          subtitle="Optional X-API-Token for authenticated mobile LAN access"
        >
          <form onSubmit={handleSaveToken} className="space-y-3">
            <div className="flex gap-2">
              <input
                type="password"
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                placeholder="Paste optional LAN Pairing Token..."
                className="flex-1 px-3 py-2 text-sm font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
              />
              <Button
                type="submit"
                variant="primary"
                size="sm"
                leftIcon={<Key className="w-4 h-4" />}
              >
                Save Token
              </Button>
            </div>
            <p className="text-xs text-slate-500">
              Localhost access is trusted automatically. When accessing from a mobile phone on the same Wi-Fi LAN, enter the pairing token if enabled.
            </p>
          </form>
        </Card>

        {/* Vault & Security Status */}
        <Card
          title="AES-GCM Encrypted Vault & Security Boundary"
          subtitle="Zero plaintext credential exposure policy"
        >
          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60">
              <span className="flex items-center gap-2 font-medium">
                <Shield className="w-4 h-4 text-emerald-600" />
                Encryption Algorithm
              </span>
              <Badge variant="success">
                {settingsData?.vault_status?.algorithm || 'AES-256-GCM / Fernet'}
              </Badge>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60">
              <span>Stored Encrypted Device Entries</span>
              <span className="font-mono font-bold">
                {settingsData?.vault_status?.encrypted_entries_count ?? 0}
              </span>
            </div>
          </div>
        </Card>

        {/* Database & Inventory Export */}
        <Card
          title="SQLite Database & Inventory Export"
          subtitle="Create a local SQLite snapshot backup or download sanitized JSON inventory"
        >
          <div className="space-y-4">
            <div className="flex items-center justify-between text-xs p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60">
              <span>Database Engine Status</span>
              <Badge variant="success">
                {settingsData?.database_health?.status || 'Healthy (SQLite WAL)'}
              </Badge>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button
                variant="primary"
                size="sm"
                leftIcon={<Database className="w-4 h-4" />}
                isLoading={backupMutation.isPending}
                onClick={() => backupMutation.mutate()}
              >
                Create SQLite Backup
              </Button>
              <Button
                variant="outline"
                size="sm"
                leftIcon={<Download className="w-4 h-4" />}
                isLoading={exportMutation.isPending}
                onClick={() => exportMutation.mutate()}
              >
                Export Inventory JSON
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
