/* ---------- "Avise-me dos jogos" → /api/inscrever (Brevo ou MailerLite, decidido no servidor) ---------- */
(() => {
  const form = document.getElementById("avise-form");
  if (!form) return;
  const $ = id => document.getElementById(id);
  const track = o => { try { (window.dataLayer = window.dataLayer || []).push(o); } catch (e) {} };
  form.addEventListener("submit", ev => {
    ev.preventDefault();
    const m = $("avise-msg"), email = $("v-email").value.trim(), ok = $("v-consent").checked;
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || !ok){ m.className = "form-msg err"; m.textContent = form.dataset.err; return; }
    const url = form.dataset.endpoint;
    if (!url){ m.className = "form-msg"; m.textContent = form.dataset.soon; return; }
    if ($("v-honey").value) return;
    const sel = $("v-evento"), btn = form.querySelector("button[type=submit]");
    const dados = { email, nome: $("v-nome").value.trim(), time: $("v-time").value.trim(), cidade: $("v-cidade").value.trim(),
                    evento: sel.value, idioma: form.dataset.lang, consentimento: true, pagina: location.pathname, site: $("v-honey").value };
    btn.disabled = true; m.className = "form-msg"; m.textContent = form.dataset.sending;
    fetch(url, { method: "POST", headers: { "Content-Type": "application/json", "Accept": "application/json" }, body: JSON.stringify(dados) })
      .then(r => r.json().catch(() => ({})).then(j => ({ r, j })))
      .then(({ r, j }) => {
        if (r.ok && j.ok){
          m.className = "form-msg ok"; m.textContent = form.dataset.done;
          track({ event: "generate_lead", lead_type: "game_alert", event_slug: sel.value, alert_language: form.dataset.lang, favorite_team: dados.time });
          form.reset();
        } else if (r.status === 503){ m.className = "form-msg"; m.textContent = form.dataset.soon; }
        else if (r.status === 400){ m.className = "form-msg err"; m.textContent = form.dataset.err; }
        else return Promise.reject();
      })
      .catch(() => { m.className = "form-msg err"; m.textContent = form.dataset.fail; })
      .finally(() => { btn.disabled = false; });
  });
})();
