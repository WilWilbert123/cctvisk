import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { PageLayout } from './components/layout/PageLayout';
import { Dashboard } from './pages/Dashboard';
import { NetworkScanner } from './pages/NetworkScanner';
import { Devices } from './pages/Devices';
import { Cameras } from './pages/Cameras';
import { NVRDevices } from './pages/NVRDevices';
import { Discovery } from './pages/Discovery';
import { Monitoring } from './pages/Monitoring';
import { Recovery } from './pages/Recovery';
import { History } from './pages/History';
import { Settings } from './pages/Settings';
import { NotFound } from './pages/NotFound';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route element={<PageLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/scanner" element={<NetworkScanner />} />
        <Route path="/devices" element={<Devices />} />
        <Route path="/cameras" element={<Cameras />} />
        <Route path="/nvr" element={<NVRDevices />} />
        <Route path="/discovery" element={<Discovery />} />
        <Route path="/monitoring" element={<Monitoring />} />
        <Route path="/recovery" element={<Recovery />} />
        <Route path="/history" element={<History />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
};
