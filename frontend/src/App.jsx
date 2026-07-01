import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Briefing from './pages/Briefing'
import Executives from './pages/Executives'
import Settings from './pages/Settings'
import Connections from './pages/Connections'
import DataSourceDetails from './pages/DataSourceDetails'
import SemanticModels from './pages/SemanticModels'
import AIAnalyst from './pages/AIAnalyst'
import Forecasting from './pages/Forecasting'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<Layout />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/briefing" element={<Briefing />} />
            <Route path="/analyst" element={<AIAnalyst />} />
            <Route path="/executives" element={<Executives />} />
            <Route path="/connections" element={<Connections />} />
            <Route path="/connections/:sourceId" element={<DataSourceDetails />} />
            <Route path="/semantic-models" element={<SemanticModels />} />
            <Route path="/forecasting" element={<Forecasting />} />
            <Route path="/forecasting/:forecastId" element={<Forecasting />} />
            <Route path="/settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
