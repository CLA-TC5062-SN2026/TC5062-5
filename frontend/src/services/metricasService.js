// Tablero (RF-13) y su exportación a PDF (RF-23): mismo endpoint, distinto Accept.
import { apiClient, query } from './apiClient.js'

export const metricasService = {
  tablero: (desde, hasta) => apiClient.get(`/metrics${query({ desde, hasta })}`),
  pdf: (desde, hasta) => apiClient.blob(`/metrics${query({ desde, hasta })}`, { headers: { Accept: 'application/pdf' } }),
}
