import { createRouter, createWebHistory } from 'vue-router';

import AppShell from '@/components/AppShell.vue';
import AssistantPage from '@/pages/assistant/AssistantPage.vue';
import ClientsPage from '@/pages/clients/ClientsPage.vue';
import SettingsPage from '@/pages/settings/SettingsPage.vue';

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: AppShell,
      children: [
        {
          path: '',
          name: 'assistant',
          component: AssistantPage,
          meta: { title: 'Ассистент' },
        },
        {
          path: 'clients',
          name: 'clients',
          component: ClientsPage,
          meta: { title: 'Клиентская база' },
        },
        {
          path: 'settings',
          name: 'settings',
          component: SettingsPage,
          meta: { title: 'Настройки' },
        },
      ],
    },
  ],
});
