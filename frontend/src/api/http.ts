import axios, {
  AxiosError,
  type AxiosRequestConfig,
  type AxiosResponse,
} from 'axios';

export const http = axios.create({
  baseURL: '/',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiClient = async <T>(
  config: AxiosRequestConfig,
): Promise<T> => {
  try {
    const response: AxiosResponse<T> = await http.request<T>(config);
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      const detail = error.response?.data?.detail;
      throw new Error(typeof detail === 'string' ? detail : error.message);
    }
    throw error;
  }
};
