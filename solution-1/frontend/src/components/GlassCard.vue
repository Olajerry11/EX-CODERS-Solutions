<template>
  <div class="glass-panel p-6 transition-all duration-300 hover:shadow-[0_8px_32px_0_rgba(31,38,135,0.45)]">
    <div v-if="$slots.header" class="mb-4 border-b border-glass-borderLight dark:border-glass-borderDark pb-3">
      <slot name="header"></slot>
    </div>
    
    <div class="text-gray-800 dark:text-gray-100">
      <slot></slot>
    </div>

    <div v-if="$slots.footer" class="mt-4 pt-3 border-t border-glass-borderLight dark:border-glass-borderDark">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script setup>
</script>
