import './index.css';
import { createApp, reactive } from "vue";
import App from "./App.vue";

import router from './router';
import resourceManager from "../../../doppio/libs/resourceManager";
import call from "../../../doppio/libs/controllers/call";
// import socket from "../../../doppio/libs/controllers/socket";
import Auth from "../../../doppio/libs/controllers/auth";
import { createPinia } from 'pinia';

const pinia = createPinia();
const app = createApp(App);
const auth = reactive(new Auth());

// Plugins
app.use(router);
app.use(resourceManager);
app.use(pinia);

// Translation
import { createI18n } from 'vue-i18n';
import ar from './locales/ar.json';
import en from './locales/en.json';
import aren from './locales/aren.json';

const i18n = createI18n({
	locale: localStorage.getItem('lang') || 'ar',
	fallbackLocale: 'ar',
	messages: {
		ar,
		en,
		aren,
	}
});
app.use(i18n);

// Global Properties,
// components can inject this
app.provide("$auth", auth);
app.provide("$call", call);
// app.provide("$socket", socket);


// Configure route gaurds
router.beforeEach(async (to, from, next) => {
	if (to.matched.some((record) => !record.meta.isLoginPage)) {
		// this route requires auth, check if logged in
		// if not, redirect to login page.
		if (!auth.isLoggedIn) {
			next({ name: 'Login', query: { route: to.path } });
		} else {
			next();
		}
	} else {
		if (auth.isLoggedIn) {
			next({ name: 'Home' });
		} else {
			next();
		}
	}
});

app.mount("#app");
