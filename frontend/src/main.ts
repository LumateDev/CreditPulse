import 'element-plus/dist/index.css';
import './styles.css';

import ElementPlus from 'element-plus';
import ru from 'element-plus/es/locale/lang/ru';
import { createApp } from 'vue';

import App from './App.vue';

createApp(App).use(ElementPlus, { locale: ru }).mount('#app');
