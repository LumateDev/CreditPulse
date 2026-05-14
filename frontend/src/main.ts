import 'element-plus/dist/index.css';
import 'element-plus/theme-chalk/dark/css-vars.css';
import './styles.scss';

import ElementPlus from 'element-plus';
import ru from 'element-plus/es/locale/lang/ru';
import { createApp } from 'vue';

import App from './App.vue';
import { router } from './router';
import { useAppStore } from './stores/AppStore';

useAppStore().initializeAppStore();

createApp(App).use(router).use(ElementPlus, { locale: ru }).mount('#app');
