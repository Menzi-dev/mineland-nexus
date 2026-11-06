import axios from 'axios';
export const baseURL = import.meta.env.VITE_API_BASE_URL || '';
export const client = axios.create({ baseURL, timeout: 60000 });
export const asset = (path) => `${baseURL}${path}`;
export function errorText(error) {
  const detail = error.response?.data?.detail;
  if (Array.isArray(detail)) return detail.map((row) => row.msg).join('; ');
  return typeof detail === 'string' ? detail : error.message || 'The request failed. Please try again.';
}
