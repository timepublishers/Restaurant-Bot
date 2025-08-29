import React from 'react';
import { X, BarChart3, ShoppingBag, Settings, Home, Store, Menu } from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  restaurantName: string;
}

const navigation = [
  { id: 'overview', name: 'Overview', icon: Home },
  { id: 'orders', name: 'Orders', icon: ShoppingBag },
  { id: 'menu', name: 'Menu', icon: Menu },
  { id: 'metrics', name: 'Analytics', icon: BarChart3 },
  { id: 'settings', name: 'Settings', icon: Settings },
];

export default function Sidebar({ 
  activeTab, 
  setActiveTab, 
  sidebarOpen, 
  setSidebarOpen, 
  restaurantName 
}: SidebarProps) {
  return (
    <>
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 flex z-40 md:hidden">
          <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
          
          <div className="relative flex-1 flex flex-col max-w-xs w-full bg-white">
            <div className="absolute top-0 right-0 -mr-12 pt-2">
              <button
                type="button"
                className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
                onClick={() => setSidebarOpen(false)}
              >
                <X className="h-6 w-6 text-white" />
              </button>
            </div>
            
            <SidebarContent 
              activeTab={activeTab}
              setActiveTab={setActiveTab}
              restaurantName={restaurantName}
              onItemClick={() => setSidebarOpen(false)}
            />
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <div className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0">
        <SidebarContent 
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          restaurantName={restaurantName}
        />
      </div>
    </>
  );
}

function SidebarContent({ 
  activeTab, 
  setActiveTab, 
  restaurantName, 
  onItemClick 
}: {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  restaurantName: string;
  onItemClick?: () => void;
}) {
  return (
    <div className="flex-1 flex flex-col min-h-0 bg-white border-r border-gray-200">
      {/* Logo */}
      <div className="flex items-center h-16 flex-shrink-0 px-4 bg-gradient-to-r from-blue-600 to-indigo-600">
        <div className="flex items-center">
          <div className="h-8 w-8 bg-white bg-opacity-20 rounded-lg flex items-center justify-center">
            <Store className="h-5 w-5 text-white" />
          </div>
          <div className="ml-3">
            <h2 className="text-white font-semibold text-sm truncate">
              {restaurantName}
            </h2>
            <p className="text-blue-100 text-xs">Admin Panel</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        {navigation.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => {
                setActiveTab(item.id);
                onItemClick?.();
              }}
              className={`group flex items-center px-2 py-2 text-sm font-medium rounded-lg w-full text-left transition-all duration-200 ${
                isActive
                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`}
            >
              <Icon
                className={`mr-3 flex-shrink-0 h-5 w-5 transition-colors ${
                  isActive ? 'text-white' : 'text-gray-400 group-hover:text-gray-500'
                }`}
              />
              {item.name}
              
              {/* Active indicator */}
              {isActive && (
                <div className="ml-auto">
                  <div className="h-2 w-2 bg-white rounded-full"></div>
                </div>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="flex-shrink-0 p-4 border-t border-gray-200">
        <div className="flex items-center">
          <div className="h-8 w-8 bg-gradient-to-br from-green-400 to-green-600 rounded-lg flex items-center justify-center">
            <div className="h-2 w-2 bg-white rounded-full"></div>
          </div>
          <div className="ml-3">
            <p className="text-sm font-medium text-gray-900">System Online</p>
            <p className="text-xs text-gray-500">All services running</p>
          </div>
        </div>
      </div>
    </div>
  );
}