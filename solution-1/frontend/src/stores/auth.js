import { defineStore } from 'pinia';
import api from '../api/axios';

function decodeJWT(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
      return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user_profile')) || null,
    accessToken: localStorage.getItem('access_token') || null,
    refreshToken: localStorage.getItem('refresh_token') || null,
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.accessToken,
    isStudent: (state) => state.user?.is_student === true,
    isLecturer: (state) => state.user?.is_lecturer === true,
  },

  actions: {
    async login(username, password) {
      try {
        const response = await api.post('/auth/login/', { username, password });
        
        this.accessToken = response.data.access;
        this.refreshToken = response.data.refresh;
        this.user = response.data.user;
        
        localStorage.setItem('access_token', this.accessToken);
        localStorage.setItem('refresh_token', this.refreshToken);
        localStorage.setItem('user_profile', JSON.stringify(this.user));

        return true;
      } catch (error) {
        console.error('Login failed:', error);
        throw error;
      }
    },

    logout() {
      this.user = null;
      this.accessToken = null;
      this.refreshToken = null;
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_profile');
    },

    initialize() {
      if (this.accessToken) {
        const payload = decodeJWT(this.accessToken);
        if (!payload || payload.exp * 1000 < Date.now()) {
          this.user = null;
        }
      }
    }
  }
});
