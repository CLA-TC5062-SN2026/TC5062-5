// Catálogos y padrón: categorías (RD-01), áreas comunes, unidades, responsables, usuarios y parámetros.
import { apiClient, query } from './apiClient.js'

export const catalogoService = {
  categorias: () => apiClient.get('/categories'),
  areasComunes: () => apiClient.get('/common-areas?activa=true'),
  unidades: () => apiClient.get('/units?pageSize=100&activa=true'),
  responsables: () => apiClient.get('/assignees'),
  usuarios: (filtros = {}) => apiClient.get(`/users${query({ pageSize: 100, ...filtros })}`),
  crearUsuario: (datos) => apiClient.post('/users', datos),
  reenviarActivacion: (id) => apiClient.post(`/users/${id}/activation-links`),
}
