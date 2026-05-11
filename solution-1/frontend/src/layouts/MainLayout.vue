<template>
  <div class="min-h-screen flex flex-col relative overflow-hidden">
    <div class="absolute top-[-10%] left-[-10%] w-96 h-96 bg-purple-500/30 dark:bg-purple-600/20 rounded-full mix-blend-multiply filter blur-[100px] opacity-60 z-0 pointer-events-none"></div>
    <div class="absolute top-[20%] right-[-10%] w-72 h-72 bg-teal-400/30 dark:bg-cyan-500/20 rounded-full mix-blend-multiply filter blur-[100px] opacity-60 z-0 pointer-events-none"></div>

    <nav class="sticky top-0 z-50 glass-panel rounded-none border-x-0 border-t-0 px-6 py-4 flex items-center justify-between">
      <div class="flex items-center space-x-4">
        <span class="text-2xl font-black tracking-wider bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-teal-400 dark:from-indigo-400 dark:to-cyan-300">
          X-CODERS
        </span>
      </div>

      <div class="flex items-center space-x-6">
        <div class="hidden md:flex space-x-6 text-sm font-semibold tracking-wide">
          <router-link to="/" class="hover:text-indigo-500 dark:hover:text-cyan-300 transition-colors">
            Dashboard
          </router-link>
        </div>

        <ThemeToggle />

        <!-- We will integrate authStore later in Phase 3 -->
        <button 
          @click="handleLogout" 
          class="text-sm font-bold text-gray-600 dark:text-gray-300 hover:text-red-500 dark:hover:text-red-400 transition-colors"
        >
          LOGOUT
        </button>
      </div>
    </nav>

    <main class="flex-grow container mx-auto px-4 py-8 relative z-10">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import ThemeToggle from '../components/ThemeToggle.vue';
// import { useAuthStore } from '../stores/auth';

const router = useRouter();

const handleLogout = () => {
  // const authStore = useAuthStore();
  // authStore.logout();
  router.push('/login');
};
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
