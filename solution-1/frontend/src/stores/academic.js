import { defineStore } from 'pinia';
import api from '../api/axios';

export const useAcademicStore = defineStore('academic', {
  state: () => ({
    timetable: [],
    notices: [],
    materials: [],
    loading: false,
    error: null,
  }),

  actions: {
    async fetchTimetable() {
      this.loading = true;
      try {
        const response = await api.get('/timetable/');
        this.timetable = response.data.results || response.data;
      } catch (err) {
        this.error = 'Failed to fetch timetable';
        console.error(err);
      } finally {
        this.loading = false;
      }
    },

    async fetchNotices() {
      this.loading = true;
      try {
        const response = await api.get('/notices/');
        this.notices = response.data.results || response.data;
      } catch (err) {
        this.error = 'Failed to fetch notices';
        console.error(err);
      } finally {
        this.loading = false;
      }
    },

    async fetchMaterials() {
      this.loading = true;
      try {
        const response = await api.get('/materials/');
        this.materials = response.data.results || response.data;
      } catch (err) {
        this.error = 'Failed to fetch materials';
        console.error(err);
      } finally {
        this.loading = false;
      }
    }
  }
});
