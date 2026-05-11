<template>
  <div class="max-w-4xl mx-auto mt-12 animate-fade-in text-center">
    
    <button 
      @click="$router.push({ name: 'LecturerDashboard' })" 
      class="mb-6 text-sm font-bold text-gray-500 hover:text-indigo-600 dark:hover:text-teal-400 transition-colors flex items-center justify-center gap-2 mx-auto"
    >
      &larr; Back to Dashboard
    </button>

    <GlassCard class="relative overflow-hidden py-16">
      <div class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-500/20 dark:bg-cyan-500/10 rounded-full blur-[100px] pointer-events-none z-0"></div>
      
      <div class="relative z-10">
        <h2 class="text-3xl font-black text-gray-800 dark:text-gray-100 mb-2">Attendance Session</h2>
        <p class="text-gray-600 dark:text-gray-400 mb-10 font-medium">Generate a secure, time-sensitive PIN for students.</p>

        <div v-if="errorMsg" class="mb-6 text-red-500 font-bold animate-pulse">
          {{ errorMsg }}
        </div>

        <div v-if="!sessionPin && !isGenerating">
          <button 
            @click="generateSession"
            class="px-10 py-5 rounded-2xl font-black tracking-widest text-white uppercase transition-all duration-300
                   bg-gradient-to-r from-indigo-600 to-teal-500 hover:from-indigo-500 hover:to-teal-400
                   shadow-[0_10px_30px_rgba(79,70,229,0.4)] hover:shadow-[0_10px_40px_rgba(79,70,229,0.6)] transform hover:scale-105"
          >
            GENERATE PIN
          </button>
        </div>

        <div v-else-if="isGenerating" class="flex flex-col items-center justify-center space-y-4">
          <svg class="animate-spin h-12 w-12 text-teal-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p class="text-teal-600 dark:text-teal-400 font-bold tracking-widest animate-pulse">INITIALIZING SECURE SESSION...</p>
        </div>

        <div v-else class="animate-fade-in flex flex-col items-center">
          <p class="text-sm font-bold text-gray-500 dark:text-gray-400 uppercase tracking-widest mb-4">Enter this code on your device</p>
          
          <div class="flex gap-4 md:gap-6 mb-8">
            <div 
              v-for="(digit, index) in sessionPin.split('')" 
              :key="index"
              class="w-24 h-32 md:w-32 md:h-44 flex items-center justify-center text-7xl md:text-8xl font-black bg-white/60 dark:bg-black/60 border-2 border-white/50 dark:border-white/10 rounded-3xl shadow-[0_0_50px_rgba(45,212,191,0.15)] text-indigo-900 dark:text-cyan-300"
            >
              {{ digit }}
            </div>
          </div>

          <div class="inline-flex items-center gap-3 px-5 py-2.5 rounded-full bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 text-sm font-bold mt-4 shadow-inner">
            <span class="relative flex h-3 w-3">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
            </span>
            Session Active &mdash; Awaiting Students
          </div>
        </div>

      </div>
    </GlassCard>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRoute } from 'vue-router';
import api from '../api/axios';
import GlassCard from '../components/GlassCard.vue';

const route = useRoute();
const courseId = route.params.courseId;

const isGenerating = ref(false);
const sessionPin = ref('');
const errorMsg = ref('');

const generateSession = async () => {
  isGenerating.value = true;
  errorMsg.value = '';
  
  try {
    const response = await api.post('/attendance/sessions/', {
      course: courseId
    });
    
    sessionPin.value = response.data.pin.toString(); 
    
  } catch (error) {
    console.error('Failed to generate session:', error);
    errorMsg.value = 'Failed to establish session. Please check your connection and try again.';
  } finally {
    isGenerating.value = false;
  }
};
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
