import { createRouter, createWebHistory } from "vue-router";
import { useAuth } from "../composables/useAuth";

const routes = [
  {
    path: "/login",
    name: "login",
    component: () => import("../views/LoginView.vue"),
    meta: { public: true },
  },
  {
    path: "/register",
    name: "register",
    component: () => import("../views/RegisterView.vue"),
    meta: { public: true },
  },
  {
    path: "/forgot-password",
    name: "forgot-password",
    component: () => import("../views/ForgotPasswordView.vue"),
    meta: { public: true },
  },
  {
    path: "/admin",
    name: "admin",
    component: () => import("../views/AdminView.vue"),
    meta: { adminOnly: true },
  },
  {
    path: "/",
    name: "dashboard",
    component: () => import("../views/DashboardView.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const { user, initialized, refreshMe } = useAuth();
  if (!initialized.value) {
    await refreshMe();
  }

  if (!to.meta.public && !user.value) {
    return { name: "login", query: { redirect: to.fullPath } };
  }
  if (to.meta.public && user.value) {
    return { name: "dashboard" };
  }
  if (to.meta.adminOnly && user.value?.role !== "admin") {
    return { name: "dashboard" };
  }
  return true;
});

export default router;
