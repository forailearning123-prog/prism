import React from 'react'
import { useAuth } from '../context/AuthContext'
import { LogOut, Bell } from 'lucide-react'

export default function Header() {
  const { user, logout } = useAuth()

  return (
    <header className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center justify-between">
      <div>
        <p className="text-xs text-gray-500">
          {new Date().toLocaleDateString('en-IN', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}
        </p>
      </div>
      <div className="flex items-center gap-4">
        <button className="text-gray-400 hover:text-gray-200 transition-colors relative">
          <Bell size={18} />
          <span className="absolute -top-1 -right-1 w-2 h-2 bg-prism-500 rounded-full" />
        </button>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-prism-700 rounded-full flex items-center justify-center text-sm font-semibold text-prism-200">
            {user?.full_name?.charAt(0) ?? 'U'}
          </div>
          <div className="hidden sm:block">
            <p className="text-sm font-medium text-gray-200">{user?.full_name}</p>
            <p className="text-xs text-gray-500">{user?.company || user?.email}</p>
          </div>
          <button
            onClick={logout}
            className="text-gray-500 hover:text-gray-300 transition-colors"
            title="Logout"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </header>
  )
}
