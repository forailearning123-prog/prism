import React from 'react';
import { NavLink } from 'react-router-dom';

export default function Sidebar() {
  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/agents', label: 'AI Agents', icon: '🤖' },
    { path: '/integrations', label: 'Integrations', icon: '🔗' },
    { path: '/monitoring', label: 'Monitoring', icon: '📈' },
    { path: '/collaboration', label: 'Collaboration', icon: '👥' },
  ];

  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col">
      <div className="p-6 border-b border-gray-800">
        <h1 className="text-xl font-bold">Prism Platform</h1>
        <p className="text-sm text-gray-400 mt-1">Business Intelligence</p>
      </div>

      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  }`
                }
              >
                <span className="text-xl">{item.icon}</span>
                <span className="font-medium">{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="p-4 border-t border-gray-800">
        <div className="text-xs text-gray-400">
          <p>Enterprise Integration Hub</p>
          <p className="mt-1">Version 1.0.0</p>
        </div>
      </div>
    </aside>
  );
}