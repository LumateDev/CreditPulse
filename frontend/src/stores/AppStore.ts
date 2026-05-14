import { computed, ref } from 'vue';

const THEME_STORAGE_KEY = 'creditpulse-theme';
const SIDEBAR_STORAGE_KEY = 'creditpulse-sidebar-collapsed';

const isDark = ref(false);
const isSidebarCollapsed = ref(false);

function applyTheme() {
  document.documentElement.classList.toggle('dark', isDark.value);
  localStorage.setItem(THEME_STORAGE_KEY, isDark.value ? 'dark' : 'light');
}

function initializeAppStore() {
  isDark.value = localStorage.getItem(THEME_STORAGE_KEY) === 'dark';
  isSidebarCollapsed.value = localStorage.getItem(SIDEBAR_STORAGE_KEY) === 'true';
  applyTheme();
}

function toggleSidebar() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value;
  localStorage.setItem(SIDEBAR_STORAGE_KEY, String(isSidebarCollapsed.value));
}

function setTheme(value: boolean) {
  isDark.value = value;
  applyTheme();
}

const sidebarWidth = computed(() => (isSidebarCollapsed.value ? '76px' : '268px'));

export function useAppStore() {
  return {
    isDark,
    isSidebarCollapsed,
    sidebarWidth,
    initializeAppStore,
    setTheme,
    toggleSidebar,
  };
}
