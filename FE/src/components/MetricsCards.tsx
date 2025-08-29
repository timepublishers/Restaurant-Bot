import React, { useState, useEffect } from 'react';
import { DollarSign, ShoppingBag, Clock, TrendingUp, Users, Package } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface Metric {
  id: string;
  title: string;
  value: string;
  change: string;
  changeType: 'increase' | 'decrease' | 'neutral';
  icon: React.ComponentType<any>;
  color: string;
}

const API_BASE_URL = 'http://localhost:8000/api';

export default function MetricsCards() {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (user) {
      fetchMetrics();
    }
  }, [user]);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      setError('');
      
      const token = localStorage.getItem('auth_token');
      if (!token) {
        throw new Error('No authentication token');
      }

      const response = await fetch(`${API_BASE_URL}/admin/metrics/24h`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch metrics');
      }

      const data = await response.json();
      
      const metricsData: Metric[] = [
        {
          id: '1',
          title: 'Revenue (24h)',
          value: `$${data.revenue_24h.toFixed(2)}`,
          change: '+12.5%',
          changeType: 'increase',
          icon: DollarSign,
          color: 'bg-green-500'
        },
        {
          id: '2',
          title: 'Orders (24h)',
          value: data.total_orders_24h.toString(),
          change: '+8.2%',
          changeType: 'increase',
          icon: ShoppingBag,
          color: 'bg-blue-500'
        },
        {
          id: '3',
          title: 'Delivered (24h)',
          value: data.delivered_24h.toString(),
          change: '+15.3%',
          changeType: 'increase',
          icon: Package,
          color: 'bg-purple-500'
        },
        {
          id: '4',
          title: 'Pending Orders',
          value: data.pending_orders.toString(),
          change: '-2.1%',
          changeType: 'decrease',
          icon: Clock,
          color: 'bg-amber-500'
        },
        {
          id: '5',
          title: 'Avg Order Value',
          value: data.total_orders_24h > 0 ? `$${(data.revenue_24h / data.total_orders_24h).toFixed(2)}` : '$0.00',
          change: '+5.7%',
          changeType: 'increase',
          icon: TrendingUp,
          color: 'bg-indigo-500'
        },
        {
          id: '6',
          title: 'Active Sessions',
          value: '23',
          change: '+18.9%',
          changeType: 'increase',
          icon: Users,
          color: 'bg-pink-500'
        }
      ];
      
      setMetrics(metricsData);
    } catch (err: any) {
      setError(err.message || 'Failed to load metrics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, index) => (
          <div key={index} className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            <div className="animate-pulse">
              <div className="flex items-center justify-between mb-4">
                <div className="h-4 bg-gray-200 rounded w-24"></div>
                <div className="h-10 w-10 bg-gray-200 rounded-xl"></div>
              </div>
              <div className="h-8 bg-gray-200 rounded w-20 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-16"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button 
            onClick={fetchMetrics}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {metrics.map((metric) => {
        const Icon = metric.icon;
        return (
          <div
            key={metric.id}
            className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 hover:shadow-lg transition-all duration-300 hover:scale-105"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-600">{metric.title}</h3>
              <div className={`p-2 rounded-xl ${metric.color} bg-opacity-10`}>
                <Icon className={`h-6 w-6 ${metric.color.replace('bg-', 'text-')}`} />
              </div>
            </div>
            
            <div className="flex items-end justify-between">
              <div>
                <p className="text-3xl font-bold text-gray-900 mb-1">{metric.value}</p>
                <div className="flex items-center">
                  <span
                    className={`text-sm font-medium ${
                      metric.changeType === 'increase'
                        ? 'text-green-600'
                        : metric.changeType === 'decrease'
                        ? 'text-red-600'
                        : 'text-gray-600'
                    }`}
                  >
                    {metric.change}
                  </span>
                  <span className="text-sm text-gray-500 ml-1">vs yesterday</span>
                </div>
              </div>
              
              {/* Mini trend indicator */}
              <div className="flex items-center">
                {metric.changeType === 'increase' && (
                  <TrendingUp className="h-4 w-4 text-green-500" />
                )}
                {metric.changeType === 'decrease' && (
                  <TrendingUp className="h-4 w-4 text-red-500 transform rotate-180" />
                )}
              </div>
            </div>
            
            {/* Progress bar for visual appeal */}
            <div className="mt-4">
              <div className="w-full bg-gray-200 rounded-full h-1">
                <div
                  className={`h-1 rounded-full ${metric.color} transition-all duration-1000 ease-out`}
                  style={{
                    width: `${Math.min(
                      100,
                      Math.max(20, Math.abs(parseFloat(metric.change)) * 5)
                    )}%`
                  }}
                ></div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}