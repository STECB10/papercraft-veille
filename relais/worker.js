// Relais Papercraft : remplace le planificateur de GitHub Actions, trop irrégulier (retards de plusieurs heures,
// tâches sautées). Lancé chaque minute par Cloudflare :
//   - à 6 h 15 (heure de Paris), lance « Vidéo du jour » ; à 7 h 30, la relance une fois si la vidéo n'existe toujours pas ;
//   - dès qu'un clic Publier / Rejeter attend sur Telegram, lance « Écoute Telegram », qui le traite.
// Le relais ne consomme pas les clics (getUpdates sans offset) : publication.py reste seul à les lire et les acquitter.
// Secrets : GH_TOKEN (jeton GitHub limité au dépôt, Actions en écriture), TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.

const VIDEO = "video-du-jour.yml";
const ECOUTE = "ecoute-telegram.yml";
const HORAIRES_VIDEO = ["06:15", "07:30"];

function paris() {
  const p = Object.fromEntries(
    new Intl.DateTimeFormat("fr-FR", { timeZone: "Europe/Paris", year: "numeric", month: "2-digit", day: "2-digit",
      hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date()).map((x) => [x.type, x.value]));
  return { date: `${p.year}-${p.month}-${p.day}`, heure: `${p.hour}:${p.minute}` };
}

async function github(env, chemin, options = {}) {
  return fetch(`https://api.github.com/repos/${env.REPO}${chemin}`, {
    ...options,
    headers: { Authorization: `Bearer ${env.GH_TOKEN}`, Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "papercraft-relais" },
  });
}

async function enCours(env, workflow) {
  for (const statut of ["queued", "in_progress"]) {
    const r = await github(env, `/actions/workflows/${workflow}/runs?status=${statut}&per_page=1`);
    if (r.ok && (await r.json()).total_count > 0) return true;
  }
  return false;
}

async function lancer(env, workflow) {
  if (await enCours(env, workflow)) return `${workflow} déjà en cours`;
  const r = await github(env, `/actions/workflows/${workflow}/dispatches`, { method: "POST", body: JSON.stringify({ ref: "main" }) });
  if (!r.ok) throw new Error(`lancement de ${workflow} refusé : ${r.status} ${await r.text()}`);
  return `${workflow} lancé`;
}

async function video(env, { date, heure }) {
  if (!HORAIRES_VIDEO.includes(heure)) return null;
  const r = await github(env, `/releases/tags/jour-${date}`);
  if (r.ok) return `vidéo du ${date} déjà faite`;
  return lancer(env, VIDEO);
}

async function clics(env) {
  const r = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/getUpdates`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ timeout: 0, allowed_updates: ["callback_query"] }),
  });
  if (!r.ok) throw new Error(`Telegram getUpdates : ${r.status}`);
  const attente = ((await r.json()).result || []).filter((u) => String(u.callback_query?.from?.id) === String(env.TELEGRAM_CHAT_ID));
  if (!attente.length) return null;
  return lancer(env, ECOUTE);
}

export default {
  async scheduled(_evenement, env, ctx) {
    const maintenant = paris();
    const resultats = await Promise.allSettled([video(env, maintenant), clics(env)]);
    for (const r of resultats) {
      if (r.status === "rejected") console.error(r.reason?.message || r.reason);
      else if (r.value) console.log(`${maintenant.date} ${maintenant.heure} : ${r.value}`);
    }
  },
};
