<script setup>
defineProps(["tasks"]);
defineEmits(["dismiss"]);
</script>

<template>
  <div v-if="tasks.length" class="mt-6 space-y-3" aria-live="polite">
    <div
      v-for="task in tasks"
      :key="task.id"
      class="rounded-lg border p-4 text-base"
      :class="{
        'border-blue-200 bg-blue-50': task.status === 'uploading' || task.status === 'processing',
        'border-green-200 bg-green-50': task.status === 'done',
        'border-red-200 bg-red-50': task.status === 'error',
      }"
    >
      <div class="flex items-start justify-between gap-4">
        <div class="flex-1">
          <p class="font-medium text-gray-800">{{ task.filename }}</p>
          <p v-if="task.status === 'uploading'" class="text-gray-600">Envoi en cours…</p>
          <p v-else-if="task.status === 'processing'" class="text-gray-600">
            Extraction des liens… {{ task.current }}/{{ task.total }}
          </p>
          <p v-else-if="task.status === 'done'" class="text-green-800">✓ {{ task.message }}</p>
          <p v-else-if="task.status === 'error'" class="text-red-800">{{ task.message }}</p>

          <div v-if="task.status === 'processing' && task.total" class="mt-2 h-2 w-full rounded-full bg-blue-100">
            <div
              class="h-2 rounded-full bg-[#1F4E78] transition-all"
              :style="{ width: `${Math.round((task.current / task.total) * 100)}%` }"
            />
          </div>
        </div>
        <button
          type="button"
          class="rounded p-1 text-gray-500 hover:text-gray-700 focus-visible:outline-none focus-visible:ring-2
                 focus-visible:ring-[#1F4E78]"
          aria-label="Fermer ce message"
          @click="$emit('dismiss', task.id)"
        >
          ✕
        </button>
      </div>
    </div>
  </div>
</template>
