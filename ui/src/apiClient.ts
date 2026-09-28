export const BASE_URL = 'http://127.0.0.1:8000/api';

export class ApiClient {
  static getToken(): string | null {
    return localStorage.getItem('token');
  }

  static async request(endpoint: string, options: RequestInit = {}) {
    const token = this.getToken();
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    };

    const url = endpoint.startsWith('http') ? endpoint : `${BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

    const response = await fetch(url, { ...options, headers });

    // Handle 401 Unauthorized globally
    if (response.status === 401) {
      localStorage.removeItem('token');
      window.dispatchEvent(new Event('auth:unauthorized'));
    }

    if (!response.ok) {
      let errorDetail = 'API request failed';
      try {
        const errorData = await response.json();
        // Handle FastAPI Pydantic validation arrays
        if (Array.isArray(errorData.detail)) {
          errorDetail = errorData.detail.map((d: any) => d.msg).join(', ');
        } else {
          errorDetail = errorData.detail || errorDetail;
        }
      } catch (e) {}
      throw new Error(errorDetail);
    }

    // Check if the response is JSON
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    }
    
    // For blob/PDF downloads
    return response;
  }

  static get(endpoint: string, headers?: any) {
    return this.request(endpoint, { method: 'GET', headers });
  }

  static post(endpoint: string, body?: any, headers?: any) {
    return this.request(endpoint, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
      headers
    });
  }
}