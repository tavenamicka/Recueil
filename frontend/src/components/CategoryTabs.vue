<script setup>
defineProps(["tabs", "activeTabId"]);
defineEmits(["select"]);
</script>

<template>
  <div role="tablist" aria-label="Catégories" class="flex gap-2 overflow-x-auto pb-2">
    <button
      v-for="tab in tabs"
      :key="tab.id"
      type="button"
      role="tab"
      :aria-selected="tab.id === activeTabId"
      class="shrink-0 whitespace-nowrap rounded-full border px-4 py-2 text-base font-medium transition-colors
             focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[#1F4E78]"
      :class="
        tab.id === activeTabId
          ? 'border-transparent text-white'
          : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
      "
      :style="tab.id === activeTabId ? { backgroundColor: tab.couleur } : {}"
      @click="$emit('select', tab.id)"
    >
      {{ tab.nom }} ({{ tab.count }})
    </button>
  </div>
</template>
