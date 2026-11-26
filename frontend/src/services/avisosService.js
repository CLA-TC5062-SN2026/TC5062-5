// Avisos en el sistema y bitácora de correos (RF-11).
import { apiClient, query } from './apiClient.js'

export const avisosService = {
  listar: (filtros = {}) => apiClient.get(`/notifications${query({ pageSize: 50, ...filtros })}`),
  marcarLeido: (id) => apiClient.mergePatch(`/notifications/${id}`, { leido: true }),
  correos: (filtros = {}) => apiClient.get(`/email-deliveries${query({ pageSize: 50, ...filtros })}`),
}
