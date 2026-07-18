<script setup>
import { ref } from "vue";

const emit = defineEmits(["files", "link"]);
const dragActive = ref(false);
const linkInput = ref("");

function onDrop(e) {
  dragActive.value = false;
  const files = Array.from(e.dataTransfer?.files || []);
  if (files.length) emit("files", files);
}

function onChange(e) {
  const files = Array.from(e.target.files || []);
  if (files.length) emit("files", files);
  e.target.value = "";
}

function onSubmitLink() {
  const url = linkInput.value.trim();
  if (!url) return;
  emit("link", url);
  linkInput.value = "";
}
</script>

<template>
  <div
    class="rounded-2xl border-4 border-dashed p-10 text-center transition-colors md:p-14"
    :class="dragActive ? 'border-[#1F4E78] bg-blue-50' : 'border-gray-300 bg-white'"
    @dragover.prevent="dragActive = true"
    @dragleave.prevent="dragActive = false"
    @drop.prevent="onDrop"
  >
    <p class="text-lg font-medium text-gray-800 md:text-xl">
      Dépose ton export WhatsApp (.txt) ou tes fichiers médias ici
    </p>
    <p class="mt-1 text-base text-gray-500">Images, vidéos, audio — tout est détecté automatiquement.</p>

    <label
      class="mt-6 inline-block cursor-pointer rounded-lg bg-[#1F4E78] px-6 py-3 text-base font-semibold text-white
             hover:bg-[#173a5c] focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2
             focus-within:ring-[#1F4E78]"
    >
      Choisir un fichier
      <input
        type="file"
        multiple
        class="sr-only"
        accept=".txt,.jpg,.jpeg,.png,.webp,.mp4,.mov,.mp3,.wav"
        @change="onChange"
      />
    </label>

    <form class="mx-auto mt-6 flex max-w-md items-center gap-2" @submit.prevent="onSubmitLink">
      <label class="sr-only" for="link-input">Ou colle un lien depuis une autre source</label>
      <input
        id="link-input"
        v-model="linkInput"
        type="url"
        placeholder="Ou colle un lien ici (n'importe quelle source)…"
        class="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-base
               focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#1F4E78]"
      />
      <button
        type="submit"
        class="shrink-0 rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-base font-medium text-gray-700
               hover:bg-gray-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#1F4E78]"
      >
        Ajouter
      </button>
    </form>
  </div>
</template>
