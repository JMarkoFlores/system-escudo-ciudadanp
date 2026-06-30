'use client';

import React, { useEffect, useState } from 'react';
import { Users, Plus, Edit, Trash2, Shield, Search } from 'lucide-react';
import { agentApi } from '@/services/api';

interface User {
  username: string;
  rol: string;
  nombre_completo: string | null;
  activo: boolean;
  created_at: string;
  last_login: string | null;
}

interface UserFormData {
  username: string;
  password: string;
  nombre_completo: string;
  rol: 'admin' | 'supervisor' | 'analista';
  activo: boolean;
}

export default function UsuariosPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [formData, setFormData] = useState<UserFormData>({
    username: '',
    password: '',
    nombre_completo: '',
    rol: 'analista',
    activo: true,
  });

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await agentApi.get('/v1/auth/users');
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingUser(null);
    setFormData({
      username: '',
      password: '',
      nombre_completo: '',
      rol: 'analista',
      activo: true,
    });
    setShowModal(true);
  };

  const handleEdit = (user: User) => {
    setEditingUser(user);
    setFormData({
      username: user.username,
      password: '',
      nombre_completo: user.nombre_completo || '',
      rol: user.rol as 'admin' | 'supervisor' | 'analista',
      activo: user.activo,
    });
    setShowModal(true);
  };

  const handleDelete = async (username: string) => {
    if (!confirm(`¿Estás seguro de eliminar al usuario ${username}?`)) return;

    try {
      await agentApi.delete(`/v1/auth/users/${username}`);
      fetchUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
      alert('Error al eliminar usuario');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      if (editingUser) {
        // Update
        await agentApi.put(`/v1/auth/users/${editingUser.username}`, {
          nombre_completo: formData.nombre_completo || undefined,
          rol: formData.rol,
          activo: formData.activo,
          password: formData.password || undefined,
        });
      } else {
        // Create
        await agentApi.post('/v1/auth/users', formData);
      }
      setShowModal(false);
      fetchUsers();
    } catch (error: any) {
      console.error('Error saving user:', error);
      alert(error.response?.data?.detail || 'Error al guardar usuario');
    }
  };

  const filteredUsers = users.filter(
    (user) =>
      user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (user.nombre_completo && user.nombre_completo.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const getRoleBadgeColor = (rol: string) => {
    switch (rol) {
      case 'admin':
        return 'bg-red-100 text-red-800';
      case 'supervisor':
        return 'bg-purple-100 text-purple-800';
      case 'analista':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center">
            <Users className="mr-2" size={28} />
            Gestión de Usuarios
          </h1>
          <p className="text-slate-500 mt-1">Administrar usuarios del sistema policial</p>
        </div>
        <button
          onClick={handleCreate}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          <Plus size={20} className="mr-2" />
          Nuevo Usuario
        </button>
      </div>

      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-4 border-b">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={20} />
            <input
              type="text"
              placeholder="Buscar por nombre o usuario..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Usuario
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Nombre Completo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Rol
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Estado
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Último Login
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {filteredUsers.map((user) => (
                <tr key={user.username} className="hover:bg-slate-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="h-10 w- rounded-full bg-slate-200 flex items-center justify-center">
                        <Shield size={20} className="text-slate-500" />
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-slate-900">{user.username}</div>
                        <div className="text-xs text-slate-500">
                          Creado: {new Date(user.created_at).toLocaleDateString('es-ES')}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-700">
                    {user.nombre_completo || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getRoleBadgeColor(
                        user.rol
                      )}`}
                    >
                      {user.rol.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        user.activo ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {user.activo ? 'ACTIVO' : 'INACTIVO'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                    {user.last_login ? new Date(user.last_login).toLocaleString('es-ES') : 'Nunca'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => handleEdit(user)}
                      className="text-blue-600 hover:text-blue-900 mr-3"
                      title="Editar"
                    >
                      <Edit size={18} />
                    </button>
                    <button
                      onClick={() => handleDelete(user.username)}
                      className="text-red-600 hover:text-red-900"
                      title="Eliminar"
                    >
                      <Trash2 size={18} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredUsers.length === 0 && (
            <div className="text-center py-12 text-slate-500">
              <Users size={48} className="mx-auto mb-4 text-slate-300" />
              <p>No se encontraron usuarios</p>
            </div>
          )}
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
            <div className="px-6 py-4 border-b">
              <h2 className="text-xl font-semibold">
                {editingUser ? 'Editar Usuario' : 'Nuevo Usuario'}
              </h2>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Usuario
                </label>
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  disabled={!!editingUser}
                  required
                  minLength={3}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-slate-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Contraseña {editingUser && '(dejar en blanco para mantener)'}
                </label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required={!editingUser}
                  minLength={8}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Nombre Completo
                </label>
                <input
                  type="text"
                  value={formData.nombre_completo}
                  onChange={(e) => setFormData({ ...formData, nombre_completo: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Rol
                </label>
                <select
                  value={formData.rol}
                  onChange={(e) => setFormData({ ...formData, rol: e.target.value as any })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="analista">Analista</option>
                  <option value="supervisor">Supervisor</option>
                  <option value="admin">Administrador</option>
                </select>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="activo"
                  checked={formData.activo}
                  onChange={(e) => setFormData({ ...formData, activo: e.target.checked })}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="activo" className="ml-2 block text-sm text-slate-700">
                  Usuario activo
                </label>
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border rounded-lg hover:bg-slate-50 transition"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                  {editingUser ? 'Actualizar' : 'Crear'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
