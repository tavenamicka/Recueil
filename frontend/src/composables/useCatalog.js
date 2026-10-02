import { computed, ref } from "vue";
import { fetchCategories, fetchLiens, fetchMedias } from "../api/client";

// Ces trois catégories du référentiel ne servent jamais à classer un lien :
// elles représentent les médias (images/vidéos/audio), dont le compte réel
// vient de la table medias, pas des liens rattachés à la catégorie.
const MEDIA_CATEGORY_TYPE = {
  Images: "image",
  "Vidéos": "video",
  Audio: "audio",
};

const PAGE_SIZE = 24;

function formatDuration(seconds) {
  if (seconds == null) return null;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function mergeSortedByDate(a, b) {
  return [...a, ...b].sort((x, y) => (y.date || "").localeCompare(x.date || ""));
}

export function useCatalog() {
  const tabs = ref([]);
  const activeTabId = ref("all");
  const query = ref("");
  const dateDebut = ref("");
  const dateFin = ref("");
  const items = ref([]);
  const loading = ref(false);
  const loadingMore = ref(false);
  const error = ref("");

  // pagination : offsets/totaux par source, pour les onglets à source unique
  // (lien/media) comme pour les onglets combinés (tous/favoris)
  const liensOffset = ref(0);
  const mediasOffset = ref(0);
  const liensTotal = ref(0);
  const mediasTotal = ref(0);
  const singleTotal = ref(0);

  async function loadTabs() {
    const [categories, mediasResp, liensFavorisResp, mediasFavorisResp] = await Promise.all([
      fetchCategories(),
      fetchMedias({ limit: 500 }),
      fetchLiens({ favori: true, limit: 1 }),
      fetchMedias({ favori: true, limit: 1 }),
    ]);

    const mediaCounts = { image: 0, video: 0, audio: 0 };
    for (const media of mediasResp.items) {
      mediaCounts[media.type] = (mediaCounts[media.type] || 0) + 1;
    }

    const builtTabs = categories.map((categorie) => {
      const mediaType = MEDIA_CATEGORY_TYPE[categorie.nom];
      if (mediaType) {
        return {
          id: `media-${mediaType}`,
          nom: categorie.nom,
          couleur: categorie.couleur,
          count: mediaCounts[mediaType],
          kind: "media",
          mediaType,
        };
      }
      return {
        id: `lien-${categorie.id}`,
        nom: categorie.nom,
        couleur: categorie.couleur,
        count: categorie.nombre_liens,
        kind: "lien",
        categorieId: categorie.id,
      };
    });

    const total = builtTabs.reduce((sum, tab) => sum + tab.count, 0);
    const favorisCount = liensFavorisResp.total + mediasFavorisResp.total;

    tabs.value = [
      { id: "all", nom: "Tous", couleur: "#1F4E78", count: total, kind: "all" },
      { id: "favoris", nom: "★ Favoris", couleur: "#B45309", count: favorisCount, kind: "favoris" },
      ...builtTabs,
    ];
  }

  function normalizeLien(lien) {
    return {
      kind: "lien",
      id: `lien-${lien.id}`,
      rawId: lien.id,
      title: lien.titre_page || lien.titre_brut || lien.url,
      domaine: lien.domaine,
      date: lien.date || "",
      url: lien.url,
      categorie: lien.categorie,
      favori: lien.favori,
      thumbnailUrl: lien.vignette_path ? `/media/${lien.vignette_path}` : null,
    };
  }

  function normalizeMedia(media) {
    return {
      kind: media.type,
      id: `media-${media.id}`,
      rawId: media.id,
      title: media.filename,
      date: (media.date_originale || media.date_upload || "").slice(0, 10),
      thumbnailUrl: media.vignette_path ? `/media/${media.vignette_path}` : null,
      fileUrl: `/media/${media.chemin_stockage}`,
      favori: media.favori,
      dureeLabel: formatDuration(media.duree_secondes),
    };
  }

  function currentTab() {
    return tabs.value.find((t) => t.id === activeTabId.value);
  }

  function commonParams() {
    return {
      q: query.value || undefined,
      date_debut: dateDebut.value || undefined,
      date_fin: dateFin.value || undefined,
    };
  }

  const hasMore = computed(() => {
    const tab = currentTab();
    if (!tab || tab.kind === "all" || tab.kind === "favoris") {
      return liensOffset.value < liensTotal.value || mediasOffset.value < mediasTotal.value;
    }
    if (tab.kind === "lien") return liensOffset.value < singleTotal.value;
    if (tab.kind === "media") return mediasOffset.value < singleTotal.value;
    return false;
  });

  async function loadItems() {
    loading.value = true;
    error.value = "";
    items.value = [];
    liensOffset.value = 0;
    mediasOffset.value = 0;
    liensTotal.value = 0;
    mediasTotal.value = 0;
    singleTotal.value = 0;

    try {
      const tab = currentTab();

      if (!tab || tab.kind === "all" || tab.kind === "favoris") {
        const favoriParam = tab?.kind === "favoris" ? { favori: true } : {};
        const [liensResp, mediasResp] = await Promise.all([
          fetchLiens({ ...commonParams(), ...favoriParam, limit: PAGE_SIZE, offset: 0 }),
          fetchMedias({ ...commonParams(), ...favoriParam, limit: PAGE_SIZE, offset: 0 }),
        ]);
        items.value = mergeSortedByDate(liensResp.items.map(normalizeLien), mediasResp.items.map(normalizeMedia));
        liensOffset.value = liensResp.items.length;
        mediasOffset.value = mediasResp.items.length;
        liensTotal.value = liensResp.total;
        mediasTotal.value = mediasResp.total;
      } else if (tab.kind === "lien") {
        const resp = await fetchLiens({ ...commonParams(), categorie_id: tab.categorieId, limit: PAGE_SIZE, offset: 0 });
        items.value = resp.items.map(normalizeLien);
        liensOffset.value = resp.items.length;
        singleTotal.value = resp.total;
      } else if (tab.kind === "media") {
        const resp = await fetchMedias({ ...commonParams(), type: tab.mediaType, limit: PAGE_SIZE, offset: 0 });
        items.value = resp.items.map(normalizeMedia);
        mediasOffset.value = resp.items.length;
        singleTotal.value = resp.total;
      }
    } catch (e) {
      error.value = e.message || "Impossible de charger les éléments. Réessaie dans un instant.";
    } finally {
      loading.value = false;
    }
  }

  async function loadMore() {
    if (loadingMore.value || !hasMore.value) return;
    loadingMore.value = true;
    error.value = "";

    try {
      const tab = currentTab();

      if (!tab || tab.kind === "all" || tab.kind === "favoris") {
        const favoriParam = tab?.kind === "favoris" ? { favori: true } : {};
        const [liensResp, mediasResp] = await Promise.all([
          liensOffset.value < liensTotal.value
            ? fetchLiens({ ...commonParams(), ...favoriParam, limit: PAGE_SIZE, offset: liensOffset.value })
            : Promise.resolve({ items: [], total: liensTotal.value }),
          mediasOffset.value < mediasTotal.value
            ? fetchMedias({ ...commonParams(), ...favoriParam, limit: PAGE_SIZE, offset: mediasOffset.value })
            : Promise.resolve({ items: [], total: mediasTotal.value }),
        ]);
        const newItems = mergeSortedByDate(liensResp.items.map(normalizeLien), mediasResp.items.map(normalizeMedia));
        items.value = mergeSortedByDate(items.value, newItems);
        liensOffset.value += liensResp.items.length;
        mediasOffset.value += mediasResp.items.length;
      } else if (tab.kind === "lien") {
        const resp = await fetchLiens({ ...commonParams(), categorie_id: tab.categorieId, limit: PAGE_SIZE, offset: liensOffset.value });
        items.value = [...items.value, ...resp.items.map(normalizeLien)];
        liensOffset.value += resp.items.length;
      } else if (tab.kind === "media") {
        const resp = await fetchMedias({ ...commonParams(), type: tab.mediaType, limit: PAGE_SIZE, offset: mediasOffset.value });
        items.value = [...items.value, ...resp.items.map(normalizeMedia)];
        mediasOffset.value += resp.items.length;
      }
    } catch (e) {
      error.value = e.message || "Impossible de charger la suite. Réessaie dans un instant.";
    } finally {
      loadingMore.value = false;
    }
  }

  return {
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
  };
}
