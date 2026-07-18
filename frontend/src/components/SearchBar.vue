<script setup>
defineProps(["modelValue", "dateDebut", "dateFin"]);
defineEmits(["update:modelValue", "update:dateDebut", "update:dateFin"]);
</script>

<template>
  <div class="flex flex-col gap-3 md:flex-row md:items-center md:gap-4">
    <div class="flex-1">
      <label class="sr-only" for="search-input">Rechercher par titre, domaine ou catégorie</label>
      <input
        id="search-input"
        type="search"
        placeholder="Rechercher par titre, domaine ou catégorie…"
        class="w-full rounded-lg border border-gray-300 px-4 py-2 text-base md:max-w-sm
               focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#1F4E78]"
        :value="modelValue"
        @input="$emit('update:modelValue', $event.target.value)"
      />
    </div>
    <div class="flex items-center gap-2 text-base text-gray-600">
      <label for="date-debut">Du</label>
      <input
        id="date-debut"
        type="date"
        class="rounded-lg border border-gray-300 px-2 py-2 text-base focus-visible:outline-none
               focus-visible:ring-2 focus-visible:ring-[#1F4E78]"
        :value="dateDebut"
        @input="$emit('update:dateDebut', $event.target.value)"
      />
      <label for="date-fin">au</label>
      <input
        id="date-fin"
        type="date"
        class="rounded-lg border border-gray-300 px-2 py-2 text-base focus-visible:outline-none
               focus-visible:ring-2 focus-visible:ring-[#1F4E78]"
        :value="dateFin"
        @input="$emit('update:dateFin', $event.target.value)"
      />
    </div>
  </div>
</template>
