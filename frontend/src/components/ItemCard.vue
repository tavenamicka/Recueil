<script setup>
defineProps(["item"]);
defineEmits(["open", "toggle-favori"]);

const MEDIA_COLORS = { image: "#BE185D", video: "#7C2D12", audio: "#075985" };
const MEDIA_LABELS = { image: "Image", video: "Vidéo", audio: "Audio" };
const MEDIA_ICONS = { image: "🖼️", video: "🎬", audio: "🎧" };

function hideBrokenFavicon(event) {
  event.target.style.display = "none";
}
</script>

<template>
  <div
    role="button"
    tabindex="0"
    class="group relative flex flex-col overflow-hidden rounded-xl border border-gray-200 bg-white text-left
           shadow-sm transition-shadow hover:shadow-md focus-visible:outline-none focus-visible:ring-2
           focus-visible:ring-offset-2 focus-visible:ring-[#1F4E78]"
    @click="$emit('open', item)"
    @keydown.enter.self="$emit('open', item)"
    @keydown.space.self.prevent="$emit('open', item)"
  >
    <button
      type="button"
      class="absolute right-2 top-2 z-10 rounded-full bg-white/90 p-1.5 text-xl leading-none shadow
             hover:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#1F4E78]"
      :aria-pressed="item.favori"
      :aria-label="item.favori ? 'Retirer des favoris' : 'Ajouter aux favoris'"
      @click.stop="$emit('toggle-favori', item)"
    >
      <span aria-hidden="true">{{ item.favori ? "★" : "☆" }}</span>
    </button>

    <div v-if="item.thumbnailUrl" class="aspect-video w-full overflow-hidden bg-gray-100">
      <img :src="item.thumbnailUrl" :alt="item.title" class="h-full w-full object-cover" />
    </div>
    <div
      v-else-if="item.kind !== 'lien'"
      class="flex aspect-video w-full items-center justify-center bg-gray-100 text-4xl"
      aria-hidden="true"
    >
      {{ MEDIA_ICONS[item.kind] }}
    </div>

    <div class="flex flex-1 flex-col gap-2 p-4">
      <span
        v-if="item.categorie"
        class="inline-block w-fit rounded-full px-3 py-1 text-base font-semibold text-white"
        :style="{ backgroundColor: item.categorie.couleur }"
      >
        {{ item.categorie.nom }}
      </span>
      <span
        v-else-if="item.kind !== 'lien'"
        class="inline-block w-fit rounded-full px-3 py-1 text-base font-semibold text-white"
        :style="{ backgroundColor: MEDIA_COLORS[item.kind] }"
      >
        {{ MEDIA_LABELS[item.kind] }}
      </span>

      <p class="line-clamp-2 text-base font-medium text-gray-900">{{ item.title }}</p>

      <p v-if="item.domaine" class="flex items-center gap-1.5 text-base text-gray-600">
        <img
          :src="`https://${item.domaine}/favicon.ico`"
          alt=""
          class="h-4 w-4 rounded-sm"
          @error="hideBrokenFavicon"
        />
        {{ item.domaine }}
      </p>

      <p class="text-base text-gray-600">
        {{ item.date }}<span v-if="item.dureeLabel"> · {{ item.dureeLabel }}</span>
      </p>
    </div>
  </div>
</template>
