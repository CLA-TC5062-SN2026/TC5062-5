// Recurso /reports del openapi_equipo.yaml (v1.1.0): consulta, alta, corrección y transiciones de estado.
import { apiClient, query } from './apiClient.js'

const f = (folio) => `/reports/${encodeURIComponent(folio)}`

export const reportesService = {
  // GET /reports → { items, pagination }. El alcance y el orden los decide el rol (RNF-05).
  listar: (filtros = {}, op) => apiClient.get(`/reports${query(filtros)}`, op),
  // GET /reports/{folio} → { datos: ReportDetail, etag }
  obtener: (folio, op) => apiClient.get(f(folio), { ...op, conEncabezados: true }),
  historial: (folio, op) => apiClient.get(`${f(folio)}/history?pageSize=100`, op),
  archivo: (folio, id, op) => apiClient.blob(`${f(folio)}/files/${id}`, op),

  // Alta (RF-03, RF-04): multipart con la parte `datos` (JSON), `fotos` y `video`.
  // `op.headers['Idempotency-Key']`: el mismo envío reintentado no duplica el reporte (RNF-11).
  crear(datos, fotos = [], video = null, op) {
    const fd = new FormData()
    fd.append('datos', JSON.stringify(datos))
    fotos.forEach((foto) => fd.append('fotos', foto))
    if (video) fd.append('video', video)
    return apiClient.post('/reports', fd, op)
  },
  corregir: (folio, cambios, etag) => apiClient.mergePatch(f(folio), cambios, etag),

  // Flujo de estados (RF-06 a RF-09, RF-17, RF-19)
  asignar: (folio, datos) => apiClient.post(`${f(folio)}/assignments`, datos),
  reclasificar: (folio, cambios, etag) => apiClient.mergePatch(`${f(folio)}/classification`, cambios, etag),
  iniciar: (folio, comentario) => apiClient.post(`${f(folio)}/cycles`, comentario ? { comentario } : {}),
  terminar(folio, datos, fotos = [], op) {
    const fd = new FormData()
    if (datos && Object.keys(datos).length) fd.append('datos', JSON.stringify(datos))
    fotos.forEach((foto) => fd.append('fotos', foto))
    return apiClient.post(`${f(folio)}/completions`, fd, op)
  },
  responder: (folio, respuesta, comentario) => apiClient.post(`${f(folio)}/resident-responses`, { respuesta, ...(comentario ? { comentario } : {}) }),
  cerrar: (folio, motivo) => apiClient.post(`${f(folio)}/closures`, motivo ? { motivo } : {}),
  cancelar: (folio, motivo) => apiClient.post(`${f(folio)}/cancellations`, { motivo }),
  reabrir: (folio, comentario) => apiClient.post(`${f(folio)}/reopenings`, { comentario }),
  unir: (folio, reportePrincipal) => apiClient.post(`${f(folio)}/merges`, { reportePrincipal }),
  mantenerIndependiente: (folio) => apiClient.delete(`${f(folio)}/duplicate-flag`),
  indicarPersistencia: (folio, comentario) => apiClient.post(`${f(folio)}/persistence-indications`, comentario ? { comentario } : {}),

  // Seguimiento (RF-15, RF-18, RF-20)
  agregarNota: (folio, texto) => apiClient.post(`${f(folio)}/notes`, { texto }),
  programarVisita: (folio, fechaVisita, etag) => apiClient.putConVersion(`${f(folio)}/visit`, { fechaVisita }, etag),
  cancelarVisita: (folio) => apiClient.delete(`${f(folio)}/visit`),
  detener: (folio, motivo, textoOtro) => apiClient.post(`${f(folio)}/holds`, { motivo, ...(textoOtro ? { textoOtro } : {}) }),
  reanudar: (folio, holdId) => apiClient.mergePatch(`${f(folio)}/holds/${holdId}`, { reanudada: true }),
  registrarCosto: (folio, datos) => apiClient.post(`${f(folio)}/costs`, datos),
}
