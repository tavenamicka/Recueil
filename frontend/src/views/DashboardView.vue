<script setup>
import { onMounted, ref, watch } from "vue";
import {
  deleteLien,
  deleteMedia,
  fetchCategories,
  updateLienCategorie,
  updateLienFavori,
  updateLienTitre,
  updateMediaFavori,
  updateMediaFilename,
} from "../api/client";
import { useCatalog } from "../composables/useCatalog";
import { useImports } from "../composables/useImports";

import DropZone from "../components/DropZone.vue";
import ImportFeedback from "../components/ImportFeedback.vue";
import SearchBar from "../components/SearchBar.vue";
import CategoryTabs from "../components/CategoryTabs.vue";
import ItemGrid from "../components/ItemGrid.vue";
import ItemDetailModal from "../components/ItemDetailModal.vue";

const {
  tabs,
  activeTabId,
  query,
  dateDebut,
  dateFin,
  items,
  loading,
  loadingMore,
  hasMore,
  error,
  loadTabs,
  loadItems,
  loadMore,
} = useCatalog();

async function refreshAll() {
  await loadTabs();
  await loadItems();
}

const imports = useImports(refreshAll);

const importOpen = ref(false);
watch(
  () => imports.tasks.length,
  (length, previousLength) => {
    if (length > previousLength) importOpen.value = true;
  }
);

const selectedItem = ref(null);
const allCategories = ref([]);
const notice = ref("");
let noticeTimer;

function showNotice(message) {
  notice.value = message;
  clearTimeout(noticeTimer);
  noticeTimer = setTimeout(() => {
    notice.value = "";
  }, 4000);
}

function debounce(fn, delay) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

function removeItemLocally(itemId) {
  const idx = items.value.findIndex((i) => i.id === itemId);
  if (idx !== -1) items.value.splice(idx, 1);
}

function patchItemLocally(itemId, patch) {
  const idx = items.value.findIndex((i) => i.id === itemId);
  if (idx !== -1) items.value[idx] = { ...items.value[idx], ...patch };
}

onMounted(async () => {
  await refreshAll();
  allCategories.value = await fetchCategories();
});

watch(activeTabId, () => loadItems());
watch(
  query,
  debounce(() => loadItems(), 300)
);
watch([dateDebut, dateFin], () => loadItems());

function openItem(item) {
  selectedItem.value = item;
}

function closeItem() {
  selectedItem.value = null;
}

async function recategorize({ id, categorieId }) {
  const updated = await updateLienCategorie(id, categorieId);
  const itemId = `lien-${id}`;
  const tab = tabs.value.find((t) => t.id === activeTabId.value);

  if (tab?.kind === "lien" && tab.categorieId !== categorieId) {
    removeItemLocally(itemId);
    selectedItem.value = null;
  } else {
    patchItemLocally(itemId, { categorie: updated.categorie });
    selectedItem.value = items.value.find((i) => i.id === itemId) || selectedItem.value;
  }
  await loadTabs();
}

async function updateTitre({ id, kind, titre }) {
  const itemId = `${kind === "lien" ? "lien" : "media"}-${id}`;
  const title =
    kind === "lien" ? (await updateLienTitre(id, titre)).titre_page : (await updateMediaFilename(id, titre)).filename;
  patchItemLocally(itemId, { title });
  selectedItem.value = items.value.find((i) => i.id === itemId) || selectedItem.value;
}

async function toggleFavori(item) {
  const newFavori = !item.favori;
  if (item.kind === "lien") await updateLienFavori(item.rawId, newFavori);
  else await updateMediaFavori(item.rawId, newFavori);

  const tab = tabs.value.find((t) => t.id === activeTabId.value);
  if (tab?.kind === "favoris" && !newFavori) {
    removeItemLocally(item.id);
    if (selectedItem.value?.id === item.id) selectedItem.value = null;
  } else {
    patchItemLocally(item.id, { favori: newFavori });
    if (selectedItem.value?.id === item.id) selectedItem.value = { ...selectedItem.value, favori: newFavori };
  }
  await loadTabs();
}

async function deleteItem(item) {
  if (item.kind === "lien") await deleteLien(item.rawId);
  else await deleteMedia(item.rawId);
  removeItemLocally(item.id);
  closeItem();
  await loadTabs();
  showNotice("✓ Élément supprimé.");
}
</script>

<template>
  <div>
    <header class="mx-auto max-w-6xl px-4 pt-8 md:pt-12">
      <h1 class="text-3xl font-bold text-gray-900 md:text-4xl">Recueil</h1>
      <p class="mt-2 text-lg text-gray-600">
        Tous les liens et médias partagés sur WhatsApp, classés et retrouvables en un clin d'œil.
      </p>
    </header>

    <main class="mx-auto max-w-6xl px-4 pb-16">
      <section class="mt-6">
        <button
          type="button"
          :aria-expanded="importOpen"
          aria-controls="import-panel"
          class="flex w-full items-center justify-between rounded-lg border border-gray-300 bg-white px-4 py-3
                 text-left text-base font-medium text-gray-800 hover:bg-gray-50 focus-visible:outline-none
                 focus-visible:ring-2 focus-visible:ring-[#1F4E78]"
          @click="importOpen = !importOpen"
        >
          <span>
            Importer un export WhatsApp ou des médias
            <span v-if="imports.tasks.length" class="text-gray-500">({{ imports.tasks.length }} en cours)</span>
          </span>
          <span aria-hidden="true" class="text-xl leading-none transition-transform" :class="{ 'rotate-180': importOpen }">
            ▾
          </span>
        </button>
        <div id="import-panel" v-show="importOpen" class="mt-4">
          <DropZone @files="imports.addFiles" @link="imports.addLink" />
          <ImportFeedback :tasks="imports.tasks" @dismiss="imports.dismiss" />
        </div>
      </section>

      <section class="mt-10">
        <SearchBar
          v-model="query"
          :date-debut="dateDebut"
          :date-fin="dateFin"
          @update:dateDebut="dateDebut = $event"
          @update:dateFin="dateFin = $event"
        />
      </section>

      <section class="mt-6">
        <CategoryTabs :tabs="tabs" :active-tab-id="activeTabId" @select="activeTabId = $event" />
      </section>

      <section class="mt-6">
        <p v-if="notice" class="mb-4 rounded-lg border border-green-200 bg-green-50 p-4 text-base text-green-800">
          {{ notice }}
        </p>
        <p v-if="error" class="mb-4 rounded-lg border border-red-200 bg-red-50 p-4 text-base text-red-800">
          {{ error }}
        </p>
        <p v-if="loading" class="text-base text-gray-500">Chargement…</p>
        <template v-else>
          <ItemGrid :items="items" @open="openItem" @toggle-favori="toggleFavori" />
          <div v-if="hasMore" class="mt-8 flex justify-center">
            <button
              type="button"
              :disabled="loadingMore"
              class="rounded-lg border border-gray-300 bg-white px-6 py-2.5 text-base font-medium text-gray-700
                     hover:bg-gray-50 disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2
                     focus-visible:ring-[#1F4E78]"
              @click="loadMore"
            >
              {{ loadingMore ? "Chargement…" : "Charger plus" }}
            </button>
          </div>
        </template>
      </section>
    </main>

    <ItemDetailModal
      :item="selectedItem"
      :categories="allCategories"
      @close="closeItem"
      @recategorize="recategorize"
      @toggle-favori="toggleFavori"
      @delete="deleteItem"
      @update-title="updateTitre"
    />
  </div>
</template>
