import React from 'react'
import { useAuth } from '../context/AuthContext'
import { User, Building, Mail } from 'lucide-react'

export default function Settings() {
  const { user } = useAuth()

  return (
    <div className="space-y-6 max-w-xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-gray-500 text-sm mt-1">Manage your account and preferences.</p>
      </div>

      <div className="card border border-gray-800">
        <h2 className="text-sm font-semibold text-gray-300 mb-4">Account</h2>
        <div className="space-y-3">
          <InfoRow icon={User} label="Name" value={user?.full_name} />
          <InfoRow icon={Mail} label="Email" value={user?.email} />
          <InfoRow icon={Building} label="Company" value={user?.company || '—'} />
        </div>
      </div>

      <div className="card border border-gray-800">
        <h2 className="text-sm font-semibold text-gray-300 mb-2">Edition</h2>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-white font-medium">Community Edition</p>
            <p className="text-xs text-gray-500 mt-0.5">Free &amp; open source. Self-hosted.</p>
          </div>
          <span className="badge bg-prism-900/50 text-prism-300">Free</span>
        </div>
      </div>

      <div className="card border border-gray-800">
        <h2 className="text-sm font-semibold text-gray-300 mb-2">Upgrade</h2>
        <p className="text-sm text-gray-400 mb-3">
          Unlock integrations, advanced AI models, and team features with Professional Edition.
        </p>
        <p className="text-sm text-gray-500">
          Professional Edition starting at <span className="text-prism-300 font-medium">₹2,500/month</span>
        </p>
      </div>
    </div>
  )
}

function InfoRow({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center gap-3 py-2 border-b border-gray-800 last:border-0">
      <Icon size={15} className="text-gray-500 shrink-0" />
      <span className="text-xs text-gray-500 w-16 shrink-0">{label}</span>
      <span className="text-sm text-gray-200">{value}</span>
    </div>
  )
}
