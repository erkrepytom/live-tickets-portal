// Brevo e MailerLite, cada uma com as mesmas duas operações: existe(email) e salvar(contato).
// As chaves vêm das variáveis de ambiente do Azure Static Web Apps (Configuração → Variáveis
// de ambiente). Nunca coloque chave neste repositório: ele é público.
//
//   BREVO_API_KEY         chave da Brevo (SMTP & API → API Keys)
//   BREVO_LIST_ID         número da lista "Avise-me" na Brevo
//   MAILERLITE_API_KEY    token da MailerLite (Integrations → API)
//   MAILERLITE_GROUP_ID   id do grupo "Notify me" na MailerLite
//
// Os atributos (Brevo) e campos (MailerLite) usados aqui são criados por scripts/email_configurar.py.

const TEMPO_LIMITE = 8000;

async function chamar(fetchFn, url, opcoes) {
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), TEMPO_LIMITE);
  try {
    return await fetchFn(url, { ...opcoes, signal: ctl.signal });
  } finally {
    clearTimeout(timer);
  }
}

async function falha(nome, r) {
  let corpo = "";
  try { corpo = (await r.text()).slice(0, 300); } catch (e) { /* sem corpo */ }
  return new Error(`${nome} respondeu ${r.status}: ${corpo}`);
}

function brevo(env, fetchFn = fetch) {
  const chave = env.BREVO_API_KEY, lista = Number(env.BREVO_LIST_ID);
  const cab = { "api-key": chave, "accept": "application/json", "content-type": "application/json" };
  return {
    nome: "brevo",
    configurada: Boolean(chave && lista),
    async existe(email) {
      const r = await chamar(fetchFn, `https://api.brevo.com/v3/contacts/${encodeURIComponent(email)}`, { headers: cab });
      if (r.status === 404) return false;
      if (r.ok) return true;
      throw await falha("Brevo", r);
    },
    async salvar(c) {
      // updateEnabled: se o e-mail já existe, atualiza em vez de dar erro.
      const r = await chamar(fetchFn, "https://api.brevo.com/v3/contacts", {
        method: "POST", headers: cab,
        body: JSON.stringify({
          email: c.email, updateEnabled: true, listIds: [lista],
          attributes: {
            FIRSTNAME: c.nome || undefined, IDIOMA: c.idioma, TIME: c.time || undefined, CIDADE: c.cidade || undefined,
            EVENTO: c.evento || undefined, ORIGEM: c.pagina || undefined, CONSENTIMENTO: c.consentidoEm,
          },
        }),
      });
      if (!r.ok) throw await falha("Brevo", r);
    },
  };
}

function mailerlite(env, fetchFn = fetch) {
  const chave = env.MAILERLITE_API_KEY, grupo = env.MAILERLITE_GROUP_ID;
  const cab = { "authorization": `Bearer ${chave}`, "accept": "application/json", "content-type": "application/json" };
  return {
    nome: "mailerlite",
    configurada: Boolean(chave && grupo),
    async existe(email) {
      const r = await chamar(fetchFn, `https://connect.mailerlite.com/api/subscribers/${encodeURIComponent(email)}`, { headers: cab });
      if (r.status === 404) return false;
      if (r.ok) return true;
      throw await falha("MailerLite", r);
    },
    async salvar(c) {
      // POST /subscribers é upsert: cria ou atualiza, e só acrescenta grupos (não tira de nenhum).
      const campos = { name: c.nome, idioma: c.idioma, time: c.time, cidade: c.cidade, evento: c.evento, origem: c.pagina, consentimento: c.consentidoEm };
      for (const k of Object.keys(campos)) if (!campos[k]) delete campos[k];
      const r = await chamar(fetchFn, "https://connect.mailerlite.com/api/subscribers", {
        method: "POST", headers: cab,
        body: JSON.stringify({ email: c.email, fields: campos, groups: [String(grupo)] }),
      });
      if (!r.ok) throw await falha("MailerLite", r);
    },
  };
}

module.exports = { brevo, mailerlite };
