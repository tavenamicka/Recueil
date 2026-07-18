<script setup>
import ItemCard from "./ItemCard.vue";

defineProps(["items"]);
defineEmits(["open", "toggle-favori"]);
</script>

<template>
  <div v-if="items.length" class="grid grid-cols-1 gap-6 sm:grid-cols-2 md:gap-8 lg:grid-cols-3 xl:grid-cols-4">
    <ItemCard
      v-for="item in items"
      :key="item.id"
      :item="item"
      @open="$emit('open', $event)"
      @toggle-favori="$emit('toggle-favori', $event)"
    />
  </div>
  <p v-else class="mt-10 text-center text-base text-gray-500">Aucun élément pour cette sélection.</p>
</template>
