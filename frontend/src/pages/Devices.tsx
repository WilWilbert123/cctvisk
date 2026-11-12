import React, { useState } from 'react';
import {
  Search,
  Plus,
  LayoutGrid,
  List,
  RotateCcw,
} from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Modal } from '../components/ui/Modal';
import { DeviceTable } from '../components/devices/DeviceTable';
import { DeviceCard } from '../components/devices/DeviceCard';
import { DeviceDetails } from '../components/devices/DeviceDetails';
import { useDevices, useCreateDevice } from '../hooks/useDevices';
import { useDeviceStore } from '../store/deviceStore';
import type { Device } from '../types/device';

export const Devices: React.FC = () => {
  const filters = useDeviceStore((s) => s.filters);
  const setFilters = useDeviceStore((s) => s.setFilters);
  const resetFilters = useDeviceStore((s) => s.resetFilters);

  const { data, isLoading } = useDevices({
    search: filters.search,
    category: filters.category,
    is_online: filters.isOnline,
    confidence: filters.confidence,
    sort_by: filters.sortBy,
    page_size: 100,
  });

  const createDevice = useCreateDevice();

  const [viewMode, setViewMode] = useState<'table' | 'grid'>('table');
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [addModalOpen, setAddModalOpen] = useState(false);

  const [newIp, setNewIp] = useState('');
  const [newLabel, setNewLabel] = useState('');
  const [newCategory, setNewCategory] = useState('ip_camera');
  const [newManufacturer, setNewManufacturer] = useState('');
  const [newModel, setNewModel] = useState('');

  const handleAddDevice = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newIp.trim()) return;
    createDevice.mutate(
      {
        ip_address: newIp.trim(),
        label: newLabel.trim() || undefined,
        category: newCategory,
        manufacturer: newManufacturer.trim() || undefined,
        model: newModel.trim() || undefined,
      },
      {
        onSuccess: () => {
          setAddModalOpen(false);
          setNewIp('');
          setNewLabel('');
          setNewManufacturer('');
          setNewModel('');
        },
      }
    );
  };

  const devices = data?.items || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Network Device Inventory ({data?.total ?? devices.length})
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Inspect discovered hosts, open ports, vendor OUI classifications, and live camera streams
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="inline-flex rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-1">
            <button
              type="button"
              onClick={() => setViewMode('table')}
              className={`p-1.5 rounded-md ${
                viewMode === 'table'
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
              }`}
              aria-label="Table view"
            >
              <List className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-md ${
                viewMode === 'grid'
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
              }`}
              aria-label="Grid view"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
          </div>

          <Button
            variant="primary"
            size="sm"
            leftIcon={<Plus className="w-4 h-4" />}
            onClick={() => setAddModalOpen(true)}
          >
            Register Device
          </Button>
        </div>
      </div>

      {/* Filter Bar */}
      <Card>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          <div className="relative lg:col-span-2">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={filters.search}
              onChange={(e) => setFilters({ search: e.target.value })}
              placeholder="Search IP, MAC, hostname, vendor, or label..."
              className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
            />
          </div>

          <select
            value={filters.category}
            onChange={(e) => setFilters({ category: e.target.value })}
            className="px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
          >
            <option value="all">All Categories</option>
            <option value="ip_camera">IP Cameras</option>
            <option value="nvr_dvr">NVR / DVR Systems</option>
            <option value="network_infrastructure">Network Infrastructure</option>
            <option value="workstation_mobile">Workstations / Mobile</option>
            <option value="unknown">Unclassified</option>
          </select>

          <select
            value={filters.isOnline}
            onChange={(e) => setFilters({ isOnline: e.target.value })}
            className="px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
          >
            <option value="all">All Statuses</option>
            <option value="online">Online Only</option>
            <option value="offline">Offline Only</option>
          </select>

          <div className="flex items-center gap-2">
            <select
              value={filters.confidence}
              onChange={(e) => setFilters({ confidence: e.target.value })}
              className="flex-1 px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
            >
              <option value="all">All Confidence</option>
              <option value="HIGH">High Confidence</option>
              <option value="MEDIUM">Medium Confidence</option>
              <option value="LOW">Low Confidence</option>
            </select>
            <Button
              variant="ghost"
              size="sm"
              onClick={resetFilters}
              title="Reset Filters"
            >
              <RotateCcw className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </Card>

      {isLoading ? (
        <Card>
          <div className="py-12 text-center text-sm text-slate-500">
            Loading device inventory...
          </div>
        </Card>
      ) : viewMode === 'table' ? (
        <DeviceTable devices={devices} onSelectDevice={setSelectedDevice} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {devices.map((d) => (
            <DeviceCard
              key={d.id || d.ip_address}
              device={d}
              onSelect={setSelectedDevice}
            />
          ))}
        </div>
      )}

      <DeviceDetails
        device={selectedDevice}
        isOpen={Boolean(selectedDevice)}
        onClose={() => setSelectedDevice(null)}
      />

      <Modal
        isOpen={addModalOpen}
        onClose={() => setAddModalOpen(false)}
        title="Register Local Network Device"
        subtitle="Manually add a static IP device or camera on your LAN"
        size="md"
      >
        <form onSubmit={handleAddDevice} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              IPv4 Address *
            </label>
            <input
              type="text"
              required
              value={newIp}
              onChange={(e) => setNewIp(e.target.value)}
              placeholder="192.168.1.100"
              className="w-full px-3 py-2 text-sm font-mono rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Device Label
            </label>
            <input
              type="text"
              value={newLabel}
              onChange={(e) => setNewLabel(e.target.value)}
              placeholder="Lobby Entrance Camera"
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Category
              </label>
              <select
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
              >
                <option value="ip_camera">IP Camera</option>
                <option value="nvr_dvr">NVR / DVR</option>
                <option value="network_infrastructure">Network Infrastructure</option>
                <option value="workstation_mobile">Workstation</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Manufacturer
              </label>
              <input
                type="text"
                value={newManufacturer}
                onChange={(e) => setNewManufacturer(e.target.value)}
                placeholder="Hikvision / Dahua / Axis"
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
              Model
            </label>
            <input
              type="text"
              value={newModel}
              onChange={(e) => setNewModel(e.target.value)}
              placeholder="DS-2CD2143G2-I"
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setAddModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={createDevice.isPending}
            >
              Save Device
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
