import { defineStore } from "pinia";
import frappe from "./frappeSdk.js";
import axios from "axios";

axios.defaults.baseURL = frappe.url;

export const useRestaurantSystemSettings = defineStore("restaurant_system_settings", {
    state: () => ({
        restaurant_system_settings: {},
        call: frappe.call(),
    }),
    getters: {
        get_restaurant_system_settings() {
            return this.restaurant_system_settings;
        },
    },
    actions: {
        async fetch_restaurant_system_settings() {
            await this.call.get("ury.ury_pos.api.getRestaurantSystemSettings").then((result) => {
                this.restaurant_system_settings = result.message;
            })
                .catch((error) => {
                    console.error("Error fetching restaurant system settings:", error);
                });
        },
    },
});
