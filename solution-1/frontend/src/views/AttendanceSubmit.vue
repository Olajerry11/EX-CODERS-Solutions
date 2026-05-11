<template>
  <div class="max-w-md mx-auto mt-16 animate-fade-in">
    <GlassCard class="relative overflow-hidden">
      <div class="absolute -top-20 -right-20 w-48 h-48 bg-teal-400/20 dark:bg-cyan-500/20 rounded-full blur-[60px] pointer-events-none z-0"></div>
      
      <div class="text-center mb-10 relative z-10">
        <h2 class="text-2xl font-black text-gray-800 dark:text-gray-100 mb-2 tracking-wide">VERIFY ATTENDANCE</h2>
        <p class="text-sm text-gray-600 dark:text-gray-400 font-medium">Enter the 4-digit PIN projected by your lecturer.</p>
      </div>

      <form @submit.prevent="submitAttendance" class="relative z-10">
        <div class="flex justify-center gap-4 mb-8">
          <input 
            v-for="(digit, index) in pinDigits" 
            :key="index"
            ref="pinInputs"
            v-model="pinDigits[index]"
            @input="handleInput($event, index)"
            @keydown="handleKeydown($event, index)"
            @paste="handlePaste"
            type="text" 
            inputmode="numeric"
            maxlength="1"
            class="w-16 h-20 text-center text-4xl font-black bg-white/40 dark:bg-black/40 border-2 border-white/50 dark:border-white/10 rounded-2xl focus:border-teal-500 dark:focus:border-cyan-400 focus:outline-none transition-all duration-300 shadow-inner text-indigo-900 dark:text-cyan-300 placeholder-gray-400 focus:shadow-[0_0_15px_rgba(45,212,191,0.3)]"
          />
        </div>

        <div v-if="errorMsg" class="mb-6 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-600 dark:text-red-400 text-sm text-center font-bold animate-pulse backdrop-blur-sm">
          {{ errorMsg }}
        </div>
        <div v-if="successMsg" class="mb-6 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 text-sm text-center font-bold backdrop-blur-sm">
          {{ successMsg }}
        </div>

        <button 
          type="submit" 
          :disabled="isSubmitting || fullPin.length !== 4"
          class="w-full py-4 rounded-xl font-black tracking-widest text-white uppercase transition-all duration-300
                 bg-gradient-to-r from-indigo-600 to-teal-500 hover:from-indigo-500 hover:to-teal-400
                 disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_4px_20px_rgba(20,184,166,0.3)] hover:shadow-[0_4px_25px_rgba(20,184,166,0.5)] disabled:shadow-none"
        >
          <span v-if="isSubmitting" class="flex items-center justify-center gap-2">
            <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            VERIFYING...
          </span>
          <span v-else>SUBMIT PIN</span>
        </button>
      </form>
    </GlassCard>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRoute } from 'vue-router';
import api from '../api/axios';
import GlassCard from '../components/GlassCard.vue';

const route = useRoute();
const courseId = route.query.course;

const pinDigits = ref(['', '', '', '']);
const pinInputs = ref([]);
const isSubmitting = ref(false);
const errorMsg = ref('');
const successMsg = ref('');

const fullPin = computed(() => pinDigits.value.join(''));

const handleInput = (event, index) => {
  const value = event.target.value;
  if (!/^\d*$/.test(value)) {
    pinDigits.value[index] = '';
    return;
  }
  if (value && index < 3) {
    pinInputs.value[index + 1].focus();
  }
};

const handleKeydown = (event, index) => {
  if (event.key === 'Backspace' && !pinDigits.value[index] && index > 0) {
    pinInputs.value[index - 1].focus();
  }
};

const handlePaste = (event) => {
  event.preventDefault();
  const pasteData = (event.clipboardData || window.clipboardData).getData('text');
  const numbersOnly = pasteData.replace(/\D/g, '').slice(0, 4);
  
  for (let i = 0; i < numbersOnly.length; i++) {
    pinDigits.value[i] = numbersOnly[i];
  }
  
  if (numbersOnly.length > 0) {
    const focusIndex = Math.min(numbersOnly.length, 3);
    pinInputs.value[focusIndex].focus();
  }
};

const submitAttendance = async () => {
  if (fullPin.value.length !== 4) return;
  
  isSubmitting.value = true;
  errorMsg.value = '';
  successMsg.value = '';

  try {
    const payload = { pin: fullPin.value };
    if (courseId) payload.course_id = courseId;

    await api.post('/attendance/submit/', payload);
    
    successMsg.value = 'Identity confirmed. Attendance recorded.';
    pinDigits.value = ['', '', '', ''];
    
  } catch (error) {
    if (error.response?.status === 400 || error.response?.status === 404) {
      errorMsg.value = 'Invalid or expired PIN. Please try again.';
    } else {
      errorMsg.value = 'System error. Please contact administration.';
    }
    pinDigits.value = ['', '', '', ''];
    pinInputs.value[0].focus();
  } finally {
    isSubmitting.value = false;
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
