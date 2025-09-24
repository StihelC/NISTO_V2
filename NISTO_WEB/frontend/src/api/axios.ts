import axios from 'axios'

export const apiClient = axios.create({
  baseURL: 'http://localhost:8002/api',
  headers: {
    'Content-Type': 'application/json',
  },
})
