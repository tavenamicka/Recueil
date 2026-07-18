<script setup>
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import {
  approvePasswordReset,
  approveUser,
  deleteUser,
  fetchPasswordResets,
  fetchUsers,
  rejectPasswordReset,
  rejectUser,
} from "../api/client";
import { useAuth } from "../composables/useAuth";

const { user: currentUser } = useAuth();

const users = ref([]);
const resets = ref([]);
const error = ref("");
const notice = ref("");
const confirmingDeleteId = ref(null);
let noticeTimer;

function showNotice(message) {
  notice.value = message;
  clearTimeout(noticeTimer);
  noticeTimer = setTimeout(() => {
    notice.value = "";
  }, 4000);
}

async function refresh() {
  error.value = "";
  try {
    [users.value, resets.value] = await Promise.all([fetchUsers(), fetchPasswordResets()]);
  } catch (e) {
    error.value = e.message || "Impossible de charger les données d'administration.";
  }
}

onMounted(refresh);

const pendingUsers = computed(() => users.value.filter((u) => u.status === "pending"));
const otherUsers = computed(() => users.value.filter((u) => u.status !== "pending"));
const pendingResets = computed(() => resets.value.filter((r) => r.status === "pending"));

const STATUS_LABELS = { pending: "En attente", approved: "Approuvé", rejected: "Refusé" };
const STATUS_COLORS = { pending: "#B45309", approved: "#15803D", rejected: "#B91C1C" };

async function handleApproveUser(id) {
  await approveUser(id);
  await refresh();
  showNotice("✓ Compte approuvé.");
}

async function handleRejectUser(id) {
  await rejectUser(id);
  await refresh();
  showNotice("✓ Compte refusé.");
}

async function handleApproveReset(id) {
  await approvePasswordReset(id);
  await refresh();
  showNotice("✓ Nouveau mot de passe activé.");
}

async function handleRejectReset(id) {
  await rejectPasswordReset(id);
  await refresh();
  showNotice("✓ Demande de réinitialisation refusée.");
}

async function handleDeleteUser(id) {
  try {
    await deleteUser(id);
    confirmingDeleteId.value = null;
    await refresh();
    showNotice("✓ Compte supprimé.");
  } catch (e) {
    error.value = e.message || "Impossible de supprimer ce compte.";
  }
}
</script>

<template>
  <div class="mx-auto max-w-4xl px-4 py-10">
    <RouterLink
      to="/"
      class="inline-block text-base text-gray-600 underline hover:text-gray-800 focus-visible:outline-none
             focus-visible:ring-2 focus-visible:ring-[#1F4E78]"
    >
      ← Retour au tableau de bord
    </RouterLink>
    <h1 class="mt-4 text-3xl font-bold text-gray-900">Administration</h1>
    <p class="mt-2 text-lg text-gray-600">Valide les demandes de compte et de réinitialisation de mot de passe.</p>

    <p v-if="notice" class="mt-4 rounded-lg border border-green-200 bg-green-50 p-4 text-base text-green-800">
      {{ notice }}
    </p>
    <p v-if="error" class="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-base text-red-800">
      {{ error }}
    </p>

    <section class="mt-10">
      <h2 class="text-xl font-semibold text-gray-900">Comptes en attente ({{ pendingUsers.length }})</h2>
      <p v-if="!pendingUsers.length" class="mt-3 text-base text-gray-500">Aucune demande en attente.</p>
      <ul v-else class="mt-4 flex flex-col gap-3">
        <li
          v-for="u in pendingUsers"
          :key="u.id"
          class="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-gray-200 bg-white p-4"
        >
          <div>
            <p class="text-base font-medium text-gray-900">{{ u.email }}</p>
            <p class="text-base text-gray-500">Demande envoyée le {{ u.created_at.slice(0, 10) }}</p>
          </div>
          <div class="flex gap-2">
            <button
              type="button"
              class="rounded-lg bg-[#1F4E78] px-4 py-2 text-base font-semibold text-white hover:bg-[#173a5c]
                     focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2
                     focus-visible:ring-[#1F4E78]"
              @click="handleApproveUser(u.id)"
            >
              Approuver
            </button>
            <button
              type="button"
              class="rounded-lg border border-red-300 px-4 py-2 text-base font-medium text-red-700
                     hover:bg-red-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-700"
              @click="handleRejectUser(u.id)"
            >
              Refuser
            </button>
          </div>
        </li>
      </ul>
    </section>

    <section class="mt-10">
      <h2 class="text-xl font-semibold text-gray-900">
        Demandes de réinitialisation de mot de passe ({{ pendingResets.length }})
      </h2>
      <p v-if="!pendingResets.length" class="mt-3 text-base text-gray-500">Aucune demande en attente.</p>
      <ul v-else class="mt-4 flex flex-col gap-3">
        <li
          v-for="r in pendingResets"
          :key="r.id"
          class="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-gray-200 bg-white p-4"
        >
          <div>
            <p class="text-base font-medium text-gray-900">{{ r.user_email }}</p>
            <p class="text-base text-gray-500">Demandée le {{ r.created_at.slice(0, 10) }}</p>
          </div>
          <div class="flex gap-2">
            <button
              type="button"
              class="rounded-lg bg-[#1F4E78] px-4 py-2 text-base font-semibold text-white hover:bg-[#173a5c]
                     focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2
                     focus-visible:ring-[#1F4E78]"
              @click="handleApproveReset(r.id)"
            >
              Activer le nouveau mot de passe
            </button>
            <button
              type="button"
              class="rounded-lg border border-red-300 px-4 py-2 text-base font-medium text-red-700
                     hover:bg-red-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-700"
              @click="handleRejectReset(r.id)"
            >
              Refuser
            </button>
          </div>
        </li>
      </ul>
    </section>

    <section class="mt-10">
      <h2 class="text-xl font-semibold text-gray-900">Tous les comptes</h2>
      <ul class="mt-4 flex flex-col gap-2">
        <li
          v-for="u in otherUsers"
          :key="u.id"
          class="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-gray-200 bg-white p-3"
        >
          <div class="flex items-center gap-3">
            <span class="text-base text-gray-900">{{ u.email }}</span>
            <span
              class="rounded-full px-3 py-1 text-base font-semibold text-white"
              :style="{ backgroundColor: STATUS_COLORS[u.status] }"
            >
              {{ STATUS_LABELS[u.status] }}{{ u.role === "admin" ? " · admin" : "" }}
            </span>
          </div>

          <div v-if="u.id !== currentUser?.id">
            <button
              v-if="confirmingDeleteId !== u.id"
              type="button"
              class="text-base font-medium text-red-700 hover:text-red-800 focus-visible:outline-none
                     focus-visible:ring-2 focus-visible:ring-red-700"
              @click="confirmingDeleteId = u.id"
            >
              Supprimer
            </button>
            <div v-else class="flex items-center gap-2">
              <span class="text-base text-red-800">Confirmer ?</span>
              <button
                type="button"
                class="rounded-lg bg-red-700 px-3 py-1.5 text-base font-semibold text-white hover:bg-red-800
                       focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2
                       focus-visible:ring-red-700"
                @click="handleDeleteUser(u.id)"
              >
                Oui
              </button>
              <button
                type="button"
                class="rounded-lg border border-gray-300 px-3 py-1.5 text-base font-medium text-gray-700
                       hover:bg-gray-50 focus-visible:outline-none focus-visible:ring-2
                       focus-visible:ring-[#1F4E78]"
                @click="confirmingDeleteId = null"
              >
                Annuler
              </button>
            </div>
          </div>
        </li>
      </ul>
    </section>
  </div>
</template>
