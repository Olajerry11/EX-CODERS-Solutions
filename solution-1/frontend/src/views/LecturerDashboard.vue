<template>
  <div class="space-y-8 animate-fade-in">
    <header class="mb-8">
      <h1 class="text-3xl font-black tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-teal-400 dark:from-indigo-400 dark:to-cyan-300">
        Lecturer Portal
      </h1>
      <p class="text-gray-600 dark:text-gray-400 mt-2 font-medium">Manage your courses and active attendance sessions.</p>
    </header>

    <section>
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-bold text-gray-800 dark:text-gray-200">Your Courses</h2>
      </div>

      <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <GlassCard v-for="i in 3" :key="i" class="h-40 animate-pulse bg-white/5 dark:bg-black/10"></GlassCard>
      </div>

      <div v-else-if="courses.length === 0" class="text-gray-500 italic p-4">
        You are not assigned to any courses yet.
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <GlassCard 
          v-for="course in courses" 
          :key="course.id" 
          class="flex flex-col h-full group hover:border-indigo-400/50 dark:hover:border-teal-500/50 transition-colors"
        >
          <div class="flex-grow">
            <h3 class="font-black text-xl text-indigo-800 dark:text-indigo-300 group-hover:text-teal-600 dark:group-hover:text-teal-400 transition-colors">
              {{ course.title }}
            </h3>
            <p class="text-sm text-gray-500 dark:text-gray-400 font-mono mt-1">{{ course.code }}</p>
          </div>
          
          <div class="mt-6 pt-4 border-t border-gray-200/20 dark:border-gray-700/30">
            <router-link 
              :to="{ name: 'GenerateAttendance', params: { courseId: course.id } }"
              class="flex items-center justify-center w-full py-2.5 rounded-lg font-bold text-sm text-white bg-indigo-600 hover:bg-indigo-500 dark:bg-indigo-600 dark:hover:bg-indigo-500 shadow-md transition-colors"
            >
              Start Attendance Session
            </router-link>
          </div>
        </GlassCard>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../api/axios';
import GlassCard from '../components/GlassCard.vue';

const courses = ref([]);
const loading = ref(true);

onMounted(async () => {
  try {
    const response = await api.get('/courses/');
    // If router is a DefaultRouter it returns { count, results: [...] } or direct list
    courses.value = response.data.results || response.data;
  } catch (error) {
    console.error('Failed to load courses:', error);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.5s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
