<script setup>
import { RouterLink, RouterView, useRouter } from "vue-router";
import { useAuth } from "./composables/useAuth";

const router = useRouter();
const { user, isAdmin, logout } = useAuth();

async function handleLogout() {
  await logout();
  router.push("/login");
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <div v-if="user" class="border-b border-gray-200 bg-white">
      <div class="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <span class="text-base text-gray-600">{{ user.email }}</span>
        <div class="flex items-center gap-4">
          <RouterLink
            v-if="isAdmin"
            to="/admin"
            class="text-base font-medium text-[#1F4E78] underline hover:text-[#173a5c] focus-visible:outline-none
                   focus-visible:ring-2 focus-visible:ring-[#1F4E78]"
          >
            Administration
          </RouterLink>
          <button
            type="button"
            class="text-base font-medium text-gray-600 hover:text-gray-800 focus-visible:outline-none
                   focus-visible:ring-2 focus-visible:ring-[#1F4E78]"
            @click="handleLogout"
          >
            Déconnexion
          </button>
        </div>
      </div>
    </div>

    <RouterView />
  </div>
</template>
