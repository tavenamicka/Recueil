<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";

const props = defineProps(["item", "categories"]);
const emit = defineEmits(["close", "recategorize", "toggle-favori", "delete", "update-title"]);

const selectedCategorieId = ref(props.item?.categorie?.id ?? null);
const confirmingDelete = ref(false);
const editingTitle = ref(false);
const titleDraft = ref(props.item?.title ?? "");
const titleInput = ref(null);
const dialogRef = ref(null);
const closeButtonRef = ref(null);
let previouslyFocusedElement = null;

const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

function getFocusableElements() {
  if (!dialogRef.value) return [];
  return Array.from(dialogRef.value.querySelectorAll(FOCUSABLE_SELECTOR)).filter((el) => el.offsetParent !== null);
}

const titleFieldLabel = computed(() => (props.item?.kind === "lien" ? "Titre" : "Nom"));

watch(
  () => props.item,
  async (item) => {
    selectedCategorieId.value = item?.categorie?.id ?? null;
    confirmingDelete.value = false;
    editingTitle.value = false;
    titleDraft.value = item?.title ?? "";

    if (item) {
      previouslyFocusedElement = document.activeElement;
      await nextTick();
      closeButtonRef.value?.focus();
    } else if (previouslyFocusedElement && document.body.contains(previouslyFocusedElement)) {
      previouslyFocusedElement.focus();
      previouslyFocusedElement = null;
    }
  }
);

function onCategorieChange(event) {
  emit("recategorize", { id: props.item.rawId, categorieId: Number(event.target.value) });
}

async function startEditTitle() {
  titleDraft.value = props.item.title;
  editingTitle.value = true;
  await nextTick();
  titleInput.value?.focus();
}

function cancelEditTitle() {
  editingTitle.value = false;
}

function saveTitle() {
  const trimmed = titleDraft.value.trim();
  if (!trimmed) return;
  emit("update-title", { id: props.item.rawId, kind: props.item.kind, titre: trimmed });
  editingTitle.value = false;
}

function confirmDelete() {
  emit("delete", props.item);
}

function handleKeydown(event) {
  if (!props.item) return;

  if (event.key === "Escape") {
    emit("close");
    return;
  }

  if (event.key === "Tab") {
    const focusable = getFocusableElements();
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }
}

onMounted(() => window.addEventListener("keydown", handleKeydown));
onUnmounted(() => window.removeEventListener("keydown", handleKeydown));
</script>

<template>
  <div v-if="item" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" @click.self="$emit('close')">
    <div
      ref="dialogRef"
      role="dialog"
      aria-modal="true"
      :aria-label="item.title"
      class="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl bg-white p-6 shadow-xl"
    >
      <div class="flex items-start justify-between gap-4">
        <div class="flex-1">
          <h2 v-if="!editingTitle" class="text-xl font-semibold text-gray-900">
            {{ item.title }}
            <button
              type="button"
              class="ml-2 align-middle text-base font-normal text-gray-500 underline hover:text-gray-700
                     focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#1F4E78]"
              @click="startEditTitle"
            >
              Modifier
            </button>
          </h2>
          <div v-else class="flex flex-col gap-2">
            <label for="titre-input" class="sr-only">{{ titleFieldLabel }}</label>
            <input
              id="titre-input"
              ref="titleInput"
              v-model="titleDraft"
              type="text"
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-xl font-semibold text-gray-900
                     focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#1F4E78]"
              @keydown.enter="saveTitle"
              @keydown.escape.stop="cancelEditTitle"
            />
            <div class="flex gap-2">
              <button
                type="button"
                class="rounded-lg bg-[#1F4E78] px-3 py-1.5 text-base font-semibold text-white hover:bg-[#173a5c]
                       focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2
                       focus-visible:ring-[#1F4E78]"
                @click="saveTitle"
              >
                Enregistrer
              </button>
              <button
                type="button"
                class="rounded-lg border border-gray-300 px-3 py-1.5 text-base font-medium text-gray-700
                       hover:bg-gray-50 focus-visible:outline-none focus-visible:ring-2
                       focus-visible:ring-[#1F4E78]"
                @click="cancelEditTitle"
              >
                Annuler
              </button>
            </div>
          </div>
        </div>
        <div class="flex shrink-0 items-center gap-1">
          <button
            type="button"
            class="rounded p-1 text-xl leading-none text-amber-600 hover:text-amber-700 focus-visible:outline-none
                   focus-visible:ring-2 focus-visible:ring-[#1F4E78]"
            :aria-pressed="item.favori"
            :aria-label="item.favori ? 'Retirer des favoris' : 'Ajouter aux favoris'"
            @click="$emit('toggle-favori', item)"
          >
            <span aria-hidden="true">{{ item.favori ? "★" : "☆" }}</span>
          </button>
          <button
            ref="closeButtonRef"
            type="button"
            class="rounded p-1 text-gray-500 hover:text-gray-700 focus-visible:outline-none focus-visible:ring-2
                   focus-visible:ring-[#1F4E78]"
            aria-label="Fermer"
            @click="$emit('close')"
          >
            ✕
          </button>
        </div>
      </div>

      <p class="mt-2 text-base text-gray-500">
        {{ item.date }}<span v-if="item.dureeLabel"> · {{ item.dureeLabel }}</span>
      </p>

      <template v-if="item.kind === 'lien'">
        <p class="mt-4 text-base text-gray-600">{{ item.domaine }}</p>
        <a
          :href="item.url"
          target="_blank"
          rel="noopener noreferrer"
          class="mt-1 block break-all text-base text-blue-700 underline focus-visible:outline-none
                 focus-visible:ring-2 focus-visible:ring-[#1F4E78]"
        >
          {{ item.url }}
        </a>
      </template>

      <template v-else-if="item.kind === 'image'">
        <img :src="item.fileUrl" :alt="item.title" class="mt-4 max-h-[60vh] w-full rounded-lg object-contain" />
      </template>
      <template v-else-if="item.kind === 'video'">
        <video :src="item.fileUrl" controls class="mt-4 max-h-[60vh] w-full rounded-lg">
          Ton navigateur ne supporte pas la lecture vidéo.
        </video>
      </template>
      <template v-else-if="item.kind === 'audio'">
        <audio :src="item.fileUrl" controls class="mt-4 w-full">
          Ton navigateur ne supporte pas la lecture audio.
        </audio>
      </template>

      <div v-if="item.kind === 'lien'" class="mt-6">
        <label for="categorie-select" class="block text-base font-medium text-gray-700">Catégorie</label>
        <select
          id="categorie-select"
          class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-base focus-visible:outline-none
                 focus-visible:ring-2 focus-visible:ring-[#1F4E78]"
          :value="selectedCategorieId"
          @change="onCategorieChange"
        >
          <option v-for="categorie in categories" :key="categorie.id" :value="categorie.id">
            {{ categorie.nom }}
          </option>
        </select>
      </div>

      <div class="mt-6 border-t border-gray-200 pt-4">
        <button
          v-if="!confirmingDelete"
          type="button"
          class="text-base font-medium text-red-700 hover:text-red-800 focus-visible:outline-none
                 focus-visible:ring-2 focus-visible:ring-red-700"
          @click="confirmingDelete = true"
        >
          Supprimer cet élément
        </button>
        <div v-else class="flex flex-wrap items-center gap-3">
          <p class="text-base font-medium text-red-800">Confirmer la suppression ? Cette action est définitive.</p>
          <button
            type="button"
            class="rounded-lg bg-red-700 px-4 py-2 text-base font-semibold text-white hover:bg-red-800
                   focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2
                   focus-visible:ring-red-700"
            @click="confirmDelete"
          >
            Oui, supprimer
          </button>
          <button
            type="button"
            class="rounded-lg border border-gray-300 px-4 py-2 text-base font-medium text-gray-700
                   hover:bg-gray-50 focus-visible:outline-none focus-visible:ring-2
                   focus-visible:ring-[#1F4E78]"
            @click="confirmingDelete = false"
          >
            Annuler
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
