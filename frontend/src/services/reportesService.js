// Recurso /reports del openapi_equipo.yaml.
import { apiClient, query } from './apiClient.js'

export const reportesService = {
  // GET /reports → { items: ReporteResumen[], pagination: { page, pageSize, total } }
  // filtros: estado, prioridad, categoriaId, texto, page, pageSize, ...
  listar: (filtros = {}, op) => apiClient.get(`/reports${query(filtros)}`, op),

  // GET /reports/{folio} → ReporteDetalle
  obtener: (folio, op) => apiClient.get(`/reports/${encodeURIComponent(folio)}`, op),
}
