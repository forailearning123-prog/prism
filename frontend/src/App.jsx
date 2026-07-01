import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Agents from './pages/Agents';
import Integrations from './pages/Integrations';
import Monitoring from './pages/Monitoring';
import Collaboration from './pages/Collaboration';

export default function App() {
  return (
    <Router>
      <div className="flex h-screen bg-gray-50">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/agents" element={<Agents />} />
            <Route path="/integrations" element={<Integrations />} />
            <Route path="/monitoring" element={<Monitoring />} />
            <Route path="/collaboration" element={<Collaboration />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}