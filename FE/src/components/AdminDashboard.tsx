import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import OrdersTable from './OrdersTable';
import MetricsCards from './MetricsCards';
import Header from './ui/Header';
import Sidebar from './ui/Sidebar';

export default function AdminDashboard() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  if (!user) return null;

  return (
    <div className="h-screen bg-gray-50 flex overflow-hidden">
      {/* Sidebar */}
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab}
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        restaurantName={user.restaurant.name}
      />

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        <Header 
          restaurantName={user.restaurant.name}
          setSidebarOpen={setSidebarOpen}
        />
        
        <main className="flex-1 relative overflow-y-auto focus:outline-none">
          <div className="py-6 px-4 sm:px-6 lg:px-8">
            {activeTab === 'overview' && (
              <div className="space-y-6">
                <MetricsCards />
                <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Recent Orders
                  </h3>
                  <OrdersTable limit={10} />
                </div>
              </div>
            )}
            
            {activeTab === 'orders' && <OrdersTable />}
            
            {activeTab === 'metrics' && (
              <div className="space-y-6">
                <MetricsCards />
                {/* Additional metrics components can be added here */}
              </div>
            )}

            {activeTab === 'settings' && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Restaurant Settings
                </h3>
                <p className="text-gray-600">Settings panel coming soon...</p>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}