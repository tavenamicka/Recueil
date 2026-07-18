<script setup>
import { ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import { useAuth } from "../composables/useAuth";

const router = useRouter();
const route = useRoute();
const { login } = useAuth();

const email = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);

async function onSubmit() {
  error.value = "";
  loading.value = true;
  try {
    await login(email.value, password.value);
    router.push(route.query.redirect || "/");
  } catch (e) {
    error.value = e.message || "Impossible de se connecter.";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-gray-50 px-4">
    <div class="w-full max-w-md rounded-xl bg-white p-8 shadow-sm">
      <h1 class="text-2xl font-bold text-gray-900">Recueil</h1>
      <p class="mt-1 text-base text-gray-600">Connecte-toi pour accéder à tes liens et médias.</p>

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
          <label for="password" class="block text-base font-medium text-gray-700">Mot de passe</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            autocomplete="current-password"
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
          {{ loading ? "Connexion…" : "Se connecter" }}
        </button>
      </form>

      <div class="mt-6 flex flex-col gap-2 text-base text-gray-600">
        <RouterLink
          to="/register"
          class="underline hover:text-gray-800 focus-visible:outline-none focus-visible:ring-2
                 focus-visible:ring-[#1F4E78]"
        >
          Créer un compte
        </RouterLink>
        <RouterLink
          to="/forgot-password"
          class="underline hover:text-gray-800 focus-visible:outline-none focus-visible:ring-2
                 focus-visible:ring-[#1F4E78]"
        >
          Mot de passe oublié ?
        </RouterLink>
      </div>
    </div>
  </div>
</template>
