import { defineConfig } from 'orval';

export default defineConfig({
  creditpulse: {
    input: 'http://127.0.0.1:8000/openapi.json',
    output: {
      target: './src/api/generated/creditpulse.ts',
      client: 'axios',
      mode: 'single',
      clean: true,
      prettier: false,
      override: {
        mutator: {
          path: './src/api/http.ts',
          name: 'apiClient',
        },
      },
    },
  },
});
