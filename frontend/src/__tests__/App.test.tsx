import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppRoutes } from '../routes';
import { CameraCard } from '../components/cameras/CameraCard';
import { CameraLivePlayer } from '../components/cameras/CameraLivePlayer';
import { useSettingsStore } from '../store/settingsStore';
import type { Camera } from '../types/camera';

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
}

describe('CCTV Network Discovery & Recovery Assistant Frontend Suite', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/dashboard/summary')) {
        return Promise.resolve({
          ok: true,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => ({
            network: {
              interface_name: 'eth0',
              ip_address: '192.168.1.50',
              subnet_cidr: '192.168.1.0/24',
              netmask: '255.255.255.0',
              gateway: '192.168.1.1',
              mac_address: '00:11:22:33:44:55',
              is_connected: true,
              connection_type: 'Ethernet',
              ssid: null,
            },
            counts: {
              total_devices: 3,
              online_devices: 3,
              offline_devices: 0,
              cameras_count: 2,
              nvr_dvr_count: 1,
              unknown_devices: 0,
              monitored_devices: 2,
            },
            latest_scan: null,
            recent_devices: [
              {
                id: 1,
                ip_address: '192.168.1.64',
                mac_address: 'BC:AD:28:11:22:33',
                label: 'North Gate Camera',
                manufacturer: 'Hikvision',
                model: 'DS-2CD2143G2-I',
                category: 'ip_camera',
                confidence: 'HIGH',
                is_online: true,
                open_ports: [80, 554, 8000],
              },
            ],
            monitoring_activity: [],
            status_distribution: [{ name: 'IP Cameras', value: 2, category: 'ip_camera' }],
            recent_events: [],
          }),
        });
      }
      return Promise.resolve({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ items: [], total: 0 }),
      });
    }) as any;
  });

  it('renders Dashboard and displays discovered CCTV & network telemetry', async () => {
    const qc = createTestQueryClient();
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={['/']}>
          <AppRoutes />
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(
      await screen.findByText(/Network & CCTV Command Center/i)
    ).toBeInTheDocument();
    expect(await screen.findByText(/North Gate Camera/i)).toBeInTheDocument();
  });

  it('renders CameraCard with Connect & View Live action button', () => {
    const sampleCam: Camera = {
      id: 10,
      ip_address: '192.168.1.64',
      label: 'Warehouse Entrance Cam',
      manufacturer: 'Hikvision',
      model: 'DS-2CD2043G2',
      rtsp_port: 554,
      http_port: 80,
      onvif_port: 80,
      is_online: true,
      onvif_supported: true,
      rtsp_supported: true,
    };

    const qc = createTestQueryClient();
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <CameraCard camera={sampleCam} />
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText('Warehouse Entrance Cam')).toBeInTheDocument();
    const connectButtons = screen.getAllByRole('button', {
      name: /Connect & View Live/i,
    });
    expect(connectButtons.length).toBeGreaterThan(0);
  });

  it('renders CameraLivePlayer modal and supports RTSP stream configuration', () => {
    const sampleCam: Camera = {
      id: 12,
      ip_address: '192.168.1.108',
      label: 'Parking Lot Dome',
      manufacturer: 'Dahua',
      model: 'IPC-HDW2431T',
      rtsp_port: 554,
      http_port: 80,
      onvif_port: 80,
      is_online: true,
    };

    const qc = createTestQueryClient();
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <CameraLivePlayer
            camera={sampleCam}
            isOpen={true}
            onClose={() => {}}
          />
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(
      screen.getByText(/Live CCTV Stream — Parking Lot Dome/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Camera Stream Authentication/i)
    ).toBeInTheDocument();
  });

  it('toggles theme mode cleanly between light, dark, and system', () => {
    const store = useSettingsStore.getState();
    store.setTheme('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);

    store.setTheme('light');
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });
});
