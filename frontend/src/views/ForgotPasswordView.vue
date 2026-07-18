<script setup>
import { ref } from "vue";
import { RouterLink } from "vue-router";
import { useAuth } from "../composables/useAuth";

const { forgotPassword } = useAuth();

const email = ref("");
const newPassword = ref("");
const confirmPassword = ref("");
const error = ref("");
const success = ref("");
const loading = ref(false);

async function onSubmit() {
  error.value = "";
  success.value = "";

  if (newPassword.value !== confirmPassword.value) {
    error.value = "Les deux mots de passe ne correspondent pas.";
    return;
  }

  loading.value = true;
  try {
    const res = await forgotPassword(email.value, newPassword.value);
    success.value = res.message;
    email.value = "";
    newPassword.value = "";
    confirmPassword.value = "";
  } catch (e) {
    error.value = e.message || "Impossible d'envoyer la demande.";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-gray-50 px-4">
    <div class="w-full max-w-md rounded-xl bg-white p-8 shadow-sm">
      <h1 class="text-2xl font-bold text-gray-900">Mot de passe oublié</h1>
      <p class="mt-1 text-base text-gray-600">
        Propose un nouveau mot de passe : il sera activé une fois validé par l'administrateur.
      </p>

      <p v-if="success" class="mt-4 rounded-lg border border-green-200 bg-green-50 p-3 text-base text-green-800">
        ✓ {{ success }}
      </p>

      <form class="mt-6 flex flex-col gap-4" @submit.prevent="onSubmit">
        <div>
          <label for="email" class="block text-base font-medium text-gray-700">Email</label>
          <input
            id="email"
            v-model="email"
            type="email"
            required
            autocomplete="username"
            class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-base focus-visible:outline-none
                   focus-visible:ring-2 focus-visible:ring-[#1F4E78]"
          />
        </div>
        <div>
          <label for="new-password" class="block text-base font-medium text-gray-700">Nouveau mot de passe</label>
          <input
            id="new-password"
            v-model="newPassword"
            type="password"
            required
            autocomplete="new-password"
            class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-base focus-visible:outline-none
                   focus-visible:ring-2 focus-visible:ring-[#1F4E78]"
          />
        </div>
        <div>
          <label for="confirm-password" class="block text-base font-medium text-gray-700">
            Confirmer le nouveau mot de passe
          </label>
          <input
            id="confirm-password"
            v-model="confirmPassword"
            type="password"
            required
            autocomplete="new-password"
            class="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-base focus-visible:outline-none
                   focus-visible:ring-2 focus-visible:ring-[#1F4E78]"
          />
        </div>

        <p v-if="error" class="rounded-lg border border-red-200 bg-red-50 p-3 text-base text-red-800">{{ error }}</p>

        <button
          type="submit"
          :disabled="loading"
          class="mt-2 rounded-lg bg-[#1F4E78] px-4 py-2 text-base font-semibold text-white hover:bg-[#173a5c]
                 disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2
                 focus-visible:ring-[#1F4E78]"
        >
          {{ loading ? "Envoi…" : "Envoyer la demande" }}
        </button>
      </form>

      <RouterLink
        to="/login"
        class="mt-6 block text-base text-gray-600 underline hover:text-gray-800 focus-visible:outline-none
               focus-visible:ring-2 focus-visible:ring-[#1F4E78]"
      >
        ← Retour à la connexion
      </RouterLink>
    </div>
  </div>
</template>
