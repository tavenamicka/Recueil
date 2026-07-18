import { computed, ref } from "vue";
import { fetchMe, login as apiLogin, logout as apiLogout, registerAccount, forgotPassword } from "../api/client";

const user = ref(null);
const initialized = ref(false);

const isAdmin = computed(() => user.value?.role === "admin");

async function refreshMe() {
  try {
    user.value = await fetchMe();
  } catch {
    user.value = null;
  } finally {
    initialized.value = true;
  }
}

async function login(email, password) {
  user.value = await apiLogin(email, password);
  return user.value;
}

async function logout() {
  await apiLogout();
  user.value = null;
}

export function useAuth() {
  return {
    user,
    isAdmin,
    initialized,
    refreshMe,
    login,
    logout,
    register: registerAccount,
    forgotPassword,
  };
}
