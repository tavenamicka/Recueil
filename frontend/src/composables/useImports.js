import { reactive } from "vue";
import { createLien, fetchImportStatus, importMedia, importTxt } from "../api/client";

export function useImports(onSettled) {
  const tasks = reactive([]);

  function addFiles(files) {
    for (const file of files) {
      const isTxt = file.name.toLowerCase().endsWith(".txt");
      const task = reactive({
        id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
        filename: file.name,
        status: "uploading",
        current: 0,
        total: 0,
        message: "",
      });
      tasks.push(task);
      if (isTxt) runTxtImport(file, task);
      else runMediaImport(file, task);
    }
  }

  async function runTxtImport(file, task) {
    try {
      const { job_id: jobId } = await importTxt(file);
      task.status = "processing";
      await pollJob(jobId, task);
    } catch (e) {
      task.status = "error";
      task.message = e.message || "Échec de l'import.";
    } finally {
      onSettled?.();
    }
  }

  function pollJob(jobId, task) {
    return new Promise((resolve) => {
      const interval = setInterval(async () => {
        try {
          const status = await fetchImportStatus(jobId);
          task.current = status.current;
          task.total = status.total;
          if (status.status === "done" || status.status === "error") {
            clearInterval(interval);
            task.status = status.status;
            task.message = status.message || "Échec de l'import.";
            resolve();
          }
        } catch {
          clearInterval(interval);
          task.status = "error";
          task.message = "Impossible de suivre la progression de cet import.";
          resolve();
        }
      }, 700);
    });
  }

  async function runMediaImport(file, task) {
    try {
      const media = await importMedia(file);
      task.status = "done";
      const labels = { image: "image", video: "vidéo", audio: "audio" };
      task.message = `${media.filename} ajouté (${labels[media.type] || media.type}).`;
    } catch (e) {
      task.status = "error";
      task.message = e.message || "Échec de l'import.";
    } finally {
      onSettled?.();
    }
  }

  async function addLink(url) {
    const task = reactive({
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      filename: url,
      status: "uploading",
      current: 0,
      total: 0,
      message: "",
    });
    tasks.push(task);
    try {
      const lien = await createLien(url);
      task.status = "done";
      task.message = `Lien ajouté : ${lien.titre_page || lien.domaine || lien.url}`;
    } catch (e) {
      task.status = "error";
      task.message = e.message || "Échec de l'ajout du lien.";
    } finally {
      onSettled?.();
    }
  }

  function dismiss(taskId) {
    const idx = tasks.findIndex((t) => t.id === taskId);
    if (idx !== -1) tasks.splice(idx, 1);
  }

  return { tasks, addFiles, addLink, dismiss };
}
