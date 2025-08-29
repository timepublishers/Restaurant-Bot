import React, { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, Save, X, Upload, Star, Leaf, Flame } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface MenuItemSize {
  name: string;
  price: number;
  description?: string;
}

interface MenuItemDeal {
  name: string;
  description: string;
  discount_percentage?: number;
  discount_amount?: number;
  min_quantity?: number;
}

interface MenuItemServing {
  name: string;
  price_multiplier: number;
  description?: string;
}

interface MenuItem {
  id: string;
  menu_id: string;
  name: string;
  description?: string;
  price: number;
  category?: string;
  image_url?: string;
  is_vegetarian: boolean;
  is_vegan: boolean;
  spice_level: number;
  preparation_time: number;
  available: boolean;
  sizes: MenuItemSize[];
  deals: MenuItemDeal[];
  servings: MenuItemServing[];
  created_at: string;
  updated_at: string;
}

interface Menu {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

const API_BASE_URL = 'http://localhost:8000/api';

export default function MenuManagement() {
  const { user } = useAuth();
  const [menus, setMenus] = useState<Menu[]>([]);
  const [menuItems, setMenuItems] = useState<MenuItem[]>([]);
  const [selectedMenu, setSelectedMenu] = useState<string | null>(null);
  const [showItemForm, setShowItemForm] = useState(false);
  const [showMenuForm, setShowMenuForm] = useState(false);
  const [editingItem, setEditingItem] = useState<MenuItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [itemForm, setItemForm] = useState({
    name: '',
    description: '',
    price: 0,
    category: '',
    image_url: '',
    is_vegetarian: false,
    is_vegan: false,
    spice_level: 0,
    preparation_time: 15,
    available: true,
    sizes: [] as MenuItemSize[],
    deals: [] as MenuItemDeal[],
    servings: [] as MenuItemServing[]
  });

  const [menuForm, setMenuForm] = useState({
    name: '',
    description: ''
  });

  useEffect(() => {
    if (user) {
      fetchMenus();
    }
  }, [user]);

  useEffect(() => {
    if (selectedMenu) {
      fetchMenuItems(selectedMenu);
    }
  }, [selectedMenu]);

  const fetchMenus = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${API_BASE_URL}/admin/menus`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setMenus(data);
        if (data.length > 0 && !selectedMenu) {
          setSelectedMenu(data[0].id);
        }
      }
    } catch (err: any) {
      setError('Failed to load menus');
    } finally {
      setLoading(false);
    }
  };

  const fetchMenuItems = async (menuId: string) => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${API_BASE_URL}/admin/menu-items?menu_id=${menuId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setMenuItems(data);
      }
    } catch (err: any) {
      setError('Failed to load menu items');
    }
  };

  const createMenu = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${API_BASE_URL}/admin/menus`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(menuForm),
      });

      if (response.ok) {
        const newMenu = await response.json();
        setMenus([...menus, newMenu]);
        setMenuForm({ name: '', description: '' });
        setShowMenuForm(false);
        if (!selectedMenu) {
          setSelectedMenu(newMenu.id);
        }
      }
    } catch (err: any) {
      setError('Failed to create menu');
    }
  };

  const createMenuItem = async () => {
    if (!selectedMenu) return;

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${API_BASE_URL}/admin/menus/${selectedMenu}/items`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(itemForm),
      });

      if (response.ok) {
        const newItem = await response.json();
        setMenuItems([...menuItems, newItem]);
        resetItemForm();
        setShowItemForm(false);
      }
    } catch (err: any) {
      setError('Failed to create menu item');
    }
  };

  const updateMenuItem = async () => {
    if (!editingItem) return;

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${API_BASE_URL}/admin/menu-items/${editingItem.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(itemForm),
      });

      if (response.ok) {
        setMenuItems(menuItems.map(item => 
          item.id === editingItem.id 
            ? { ...item, ...itemForm, updated_at: new Date().toISOString() }
            : item
        ));
        resetItemForm();
        setEditingItem(null);
        setShowItemForm(false);
      }
    } catch (err: any) {
      setError('Failed to update menu item');
    }
  };

  const deleteMenuItem = async (itemId: string) => {
    if (!confirm('Are you sure you want to delete this menu item?')) return;

    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${API_BASE_URL}/admin/menu-items/${itemId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        setMenuItems(menuItems.filter(item => item.id !== itemId));
      }
    } catch (err: any) {
      setError('Failed to delete menu item');
    }
  };

  const resetItemForm = () => {
    setItemForm({
      name: '',
      description: '',
      price: 0,
      category: '',
      image_url: '',
      is_vegetarian: false,
      is_vegan: false,
      spice_level: 0,
      preparation_time: 15,
      available: true,
      sizes: [],
      deals: [],
      servings: []
    });
  };

  const editItem = (item: MenuItem) => {
    setItemForm({
      name: item.name,
      description: item.description || '',
      price: item.price,
      category: item.category || '',
      image_url: item.image_url || '',
      is_vegetarian: item.is_vegetarian,
      is_vegan: item.is_vegan,
      spice_level: item.spice_level,
      preparation_time: item.preparation_time,
      available: item.available,
      sizes: item.sizes || [],
      deals: item.deals || [],
      servings: item.servings || []
    });
    setEditingItem(item);
    setShowItemForm(true);
  };

  const addSize = () => {
    setItemForm({
      ...itemForm,
      sizes: [...itemForm.sizes, { name: '', price: 0, description: '' }]
    });
  };

  const addDeal = () => {
    setItemForm({
      ...itemForm,
      deals: [...itemForm.deals, { name: '', description: '', discount_percentage: 0 }]
    });
  };

  const addServing = () => {
    setItemForm({
      ...itemForm,
      servings: [...itemForm.servings, { name: '', price_multiplier: 1, description: '' }]
    });
  };

  const removeSize = (index: number) => {
    setItemForm({
      ...itemForm,
      sizes: itemForm.sizes.filter((_, i) => i !== index)
    });
  };

  const removeDeal = (index: number) => {
    setItemForm({
      ...itemForm,
      deals: itemForm.deals.filter((_, i) => i !== index)
    });
  };

  const removeServing = (index: number) => {
    setItemForm({
      ...itemForm,
      servings: itemForm.servings.filter((_, i) => i !== index)
    });
  };

  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-4 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Menu Management</h2>
        <div className="flex space-x-3">
          <button
            onClick={() => setShowMenuForm(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
          >
            <Plus className="h-4 w-4" />
            <span>New Menu</span>
          </button>
          <button
            onClick={() => setShowItemForm(true)}
            disabled={!selectedMenu}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Plus className="h-4 w-4" />
            <span>New Item</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {/* Menu Tabs */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {menus.map((menu) => (
              <button
                key={menu.id}
                onClick={() => setSelectedMenu(menu.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  selectedMenu === menu.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {menu.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Menu Items */}
        <div className="p-6">
          {menuItems.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {menuItems.map((item) => (
                <div key={item.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  {item.image_url && (
                    <img
                      src={item.image_url}
                      alt={item.name}
                      className="w-full h-32 object-cover rounded-lg mb-3"
                    />
                  )}
                  
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-semibold text-gray-900">{item.name}</h3>
                    <div className="flex items-center space-x-1">
                      {item.is_vegetarian && <Leaf className="h-4 w-4 text-green-500" />}
                      {item.is_vegan && <Star className="h-4 w-4 text-green-600" />}
                      {item.spice_level > 0 && (
                        <div className="flex">
                          {[...Array(item.spice_level)].map((_, i) => (
                            <Flame key={i} className="h-3 w-3 text-red-500" />
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <p className="text-gray-600 text-sm mb-2">{item.description}</p>
                  <p className="font-bold text-lg text-blue-600 mb-2">${item.price.toFixed(2)}</p>
                  
                  {item.category && (
                    <span className="inline-block bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded-full mb-2">
                      {item.category}
                    </span>
                  )}
                  
                  {item.sizes.length > 0 && (
                    <div className="mb-2">
                      <p className="text-xs font-medium text-gray-700 mb-1">Sizes:</p>
                      <div className="flex flex-wrap gap-1">
                        {item.sizes.map((size, index) => (
                          <span key={index} className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                            {size.name} (${size.price})
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {item.deals.length > 0 && (
                    <div className="mb-2">
                      <p className="text-xs font-medium text-gray-700 mb-1">Deals:</p>
                      <div className="flex flex-wrap gap-1">
                        {item.deals.map((deal, index) => (
                          <span key={index} className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded">
                            {deal.name}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <div className="flex items-center justify-between mt-4">
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      item.available 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {item.available ? 'Available' : 'Unavailable'}
                    </span>
                    
                    <div className="flex space-x-2">
                      <button
                        onClick={() => editItem(item)}
                        className="p-1 text-blue-600 hover:bg-blue-50 rounded"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => deleteMenuItem(item.id)}
                        className="p-1 text-red-600 hover:bg-red-50 rounded"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-500">No menu items found. Create your first item!</p>
            </div>
          )}
        </div>
      </div>

      {/* Menu Form Modal */}
      {showMenuForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Create New Menu</h3>
              <button
                onClick={() => setShowMenuForm(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={menuForm.name}
                  onChange={(e) => setMenuForm({ ...menuForm, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Menu name"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={menuForm.description}
                  onChange={(e) => setMenuForm({ ...menuForm, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="Menu description"
                />
              </div>
              
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowMenuForm(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={createMenu}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Create Menu
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Item Form Modal */}
      {showItemForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">
                  {editingItem ? 'Edit Menu Item' : 'Create New Menu Item'}
                </h3>
                <button
                  onClick={() => {
                    setShowItemForm(false);
                    setEditingItem(null);
                    resetItemForm();
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
            </div>
            
            <div className="p-6 space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                  <input
                    type="text"
                    value={itemForm.name}
                    onChange={(e) => setItemForm({ ...itemForm, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Item name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Price *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={itemForm.price}
                    onChange={(e) => setItemForm({ ...itemForm, price: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="0.00"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                  <input
                    type="text"
                    value={itemForm.category}
                    onChange={(e) => setItemForm({ ...itemForm, category: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., Appetizers, Main Course"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Preparation Time (minutes)</label>
                  <input
                    type="number"
                    value={itemForm.preparation_time}
                    onChange={(e) => setItemForm({ ...itemForm, preparation_time: parseInt(e.target.value) || 15 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={itemForm.description}
                  onChange={(e) => setItemForm({ ...itemForm, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="Item description"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Image URL</label>
                <input
                  type="url"
                  value={itemForm.image_url}
                  onChange={(e) => setItemForm({ ...itemForm, image_url: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="https://example.com/image.jpg"
                />
              </div>
              
              {/* Options */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={itemForm.is_vegetarian}
                    onChange={(e) => setItemForm({ ...itemForm, is_vegetarian: e.target.checked })}
                    className="mr-2"
                  />
                  Vegetarian
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={itemForm.is_vegan}
                    onChange={(e) => setItemForm({ ...itemForm, is_vegan: e.target.checked })}
                    className="mr-2"
                  />
                  Vegan
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={itemForm.available}
                    onChange={(e) => setItemForm({ ...itemForm, available: e.target.checked })}
                    className="mr-2"
                  />
                  Available
                </label>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Spice Level</label>
                  <select
                    value={itemForm.spice_level}
                    onChange={(e) => setItemForm({ ...itemForm, spice_level: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value={0}>None</option>
                    <option value={1}>Mild</option>
                    <option value={2}>Medium</option>
                    <option value={3}>Hot</option>
                    <option value={4}>Very Hot</option>
                    <option value={5}>Extremely Hot</option>
                  </select>
                </div>
              </div>
              
              {/* Sizes */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-medium text-gray-700">Sizes</h4>
                  <button
                    onClick={addSize}
                    className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                  >
                    Add Size
                  </button>
                </div>
                
                {itemForm.sizes.map((size, index) => (
                  <div key={index} className="flex items-center space-x-3 mb-2">
                    <input
                      type="text"
                      value={size.name}
                      onChange={(e) => {
                        const newSizes = [...itemForm.sizes];
                        newSizes[index].name = e.target.value;
                        setItemForm({ ...itemForm, sizes: newSizes });
                      }}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Size name"
                    />
                    <input
                      type="number"
                      step="0.01"
                      value={size.price}
                      onChange={(e) => {
                        const newSizes = [...itemForm.sizes];
                        newSizes[index].price = parseFloat(e.target.value) || 0;
                        setItemForm({ ...itemForm, sizes: newSizes });
                      }}
                      className="w-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Price"
                    />
                    <button
                      onClick={() => removeSize(index)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
              
              {/* Deals */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-medium text-gray-700">Deals</h4>
                  <button
                    onClick={addDeal}
                    className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                  >
                    Add Deal
                  </button>
                </div>
                
                {itemForm.deals.map((deal, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-3 mb-3">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                      <input
                        type="text"
                        value={deal.name}
                        onChange={(e) => {
                          const newDeals = [...itemForm.deals];
                          newDeals[index].name = e.target.value;
                          setItemForm({ ...itemForm, deals: newDeals });
                        }}
                        className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Deal name"
                      />
                      <input
                        type="number"
                        value={deal.discount_percentage || ''}
                        onChange={(e) => {
                          const newDeals = [...itemForm.deals];
                          newDeals[index].discount_percentage = parseFloat(e.target.value) || undefined;
                          setItemForm({ ...itemForm, deals: newDeals });
                        }}
                        className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Discount %"
                      />
                    </div>
                    <div className="flex items-center space-x-3">
                      <input
                        type="text"
                        value={deal.description}
                        onChange={(e) => {
                          const newDeals = [...itemForm.deals];
                          newDeals[index].description = e.target.value;
                          setItemForm({ ...itemForm, deals: newDeals });
                        }}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Deal description"
                      />
                      <button
                        onClick={() => removeDeal(index)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Servings */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-medium text-gray-700">Servings</h4>
                  <button
                    onClick={addServing}
                    className="px-3 py-1 bg-purple-600 text-white text-sm rounded hover:bg-purple-700"
                  >
                    Add Serving
                  </button>
                </div>
                
                {itemForm.servings.map((serving, index) => (
                  <div key={index} className="flex items-center space-x-3 mb-2">
                    <input
                      type="text"
                      value={serving.name}
                      onChange={(e) => {
                        const newServings = [...itemForm.servings];
                        newServings[index].name = e.target.value;
                        setItemForm({ ...itemForm, servings: newServings });
                      }}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Serving name"
                    />
                    <input
                      type="number"
                      step="0.1"
                      value={serving.price_multiplier}
                      onChange={(e) => {
                        const newServings = [...itemForm.servings];
                        newServings[index].price_multiplier = parseFloat(e.target.value) || 1;
                        setItemForm({ ...itemForm, servings: newServings });
                      }}
                      className="w-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Multiplier"
                    />
                    <button
                      onClick={() => removeServing(index)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
              
              {/* Actions */}
              <div className="flex space-x-3 pt-4 border-t border-gray-200">
                <button
                  onClick={() => {
                    setShowItemForm(false);
                    setEditingItem(null);
                    resetItemForm();
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={editingItem ? updateMenuItem : createMenuItem}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center justify-center space-x-2"
                >
                  <Save className="h-4 w-4" />
                  <span>{editingItem ? 'Update Item' : 'Create Item'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}