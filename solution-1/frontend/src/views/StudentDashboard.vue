<template>
  <div class="space-y-8 animate-fade-in">
    <header class="mb-8">
      <h1 class="text-3xl font-black tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-teal-400 dark:from-indigo-400 dark:to-cyan-300">
        Student Portal
      </h1>
      <p class="text-gray-600 dark:text-gray-400 mt-2 font-medium">Welcome back. Here is your overview for today.</p>
    </header>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      
      <section>
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-bold text-gray-800 dark:text-gray-200">Today's Schedule</h2>
        </div>
        
        <div v-if="academicStore.loading" class="space-y-4">
          <GlassCard class="h-24 animate-pulse bg-white/5 dark:bg-black/10"></GlassCard>
          <GlassCard class="h-24 animate-pulse bg-white/5 dark:bg-black/10"></GlassCard>
        </div>
        
        <div v-else-if="academicStore.timetable.length === 0" class="text-gray-500 italic p-4">
          No classes scheduled for today.
        </div>
        
        <div v-else class="space-y-4">
          <GlassCard 
            v-for="slot in academicStore.timetable" 
            :key="slot.id" 
            class="hover:border-indigo-400/50 dark:hover:border-teal-500/50 transition-colors group"
          >
            <div class="flex justify-between items-start">
              <div>
                <h3 class="font-bold text-lg text-indigo-700 dark:text-indigo-300 group-hover:text-teal-600 dark:group-hover:text-teal-400 transition-colors">
                  {{ slot.course.title }}
                </h3>
                <p class="text-sm text-gray-600 dark:text-gray-400 mt-1 font-medium">
                  {{ slot.course.code }} &bull; {{ slot.venue || slot.location }}
                </p>
              </div>
              <div class="text-right flex flex-col items-end">
                <span class="inline-block px-3 py-1 rounded-full text-xs font-bold tracking-wider bg-indigo-100 text-indigo-800 dark:bg-indigo-900/50 dark:text-indigo-200 border border-indigo-200 dark:border-indigo-800">
                  {{ formatTime(slot.start_time) }} - {{ formatTime(slot.end_time) }}
                </span>
                
                <router-link 
                  :to="{ name: 'AttendanceSubmit', query: { course: slot.course.id } }"
                  class="mt-4 text-sm text-teal-600 dark:text-teal-400 hover:text-teal-800 dark:hover:text-teal-200 font-bold transition-colors flex items-center gap-1"
                >
                  Verify Attendance <span class="text-lg leading-none">&rarr;</span>
                </router-link>
              </div>
            </div>
          </GlassCard>
        </div>
      </section>

      <section>
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-bold text-gray-800 dark:text-gray-200">Recent Notices</h2>
        </div>

        <div v-if="academicStore.loading" class="space-y-4">
          <GlassCard class="h-32 animate-pulse bg-white/5 dark:bg-black/10"></GlassCard>
        </div>

        <div v-else-if="academicStore.notices.length === 0" class="text-gray-500 italic p-4">
          No recent notices.
        </div>

        <div v-else class="space-y-4">
          <GlassCard v-for="notice in academicStore.notices" :key="notice.id">
            <template #header>
              <div class="flex justify-between items-center">
                <h3 class="font-bold text-gray-800 dark:text-gray-100">{{ notice.title }}</h3>
                <span class="text-xs font-mono text-gray-500 dark:text-gray-400">{{ formatDate(notice.created_at) }}</span>
              </div>
            </template>
            <p class="text-gray-700 dark:text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
              {{ notice.content }}
            </p>
          </GlassCard>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useAcademicStore } from '../stores/academic';
import GlassCard from '../components/GlassCard.vue';

const academicStore = useAcademicStore();

onMounted(() => {
  academicStore.fetchTimetable();
  academicStore.fetchNotices();
});

const formatTime = (timeStr) => timeStr ? timeStr.substring(0, 5) : '';
const formatDate = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
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
