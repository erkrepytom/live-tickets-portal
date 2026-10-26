// POST /api/inscrever — formulário "Avise-me dos jogos" (assets/avise.js).
// A resposta é a mesma exista ou não o e-mail, para a página não revelar quem já é inscrito.
const { brevo, mailerlite } = require("../compartilhado/provedores");
const { validar, inscrever } = require("../compartilhado/inscricao");

const ORIGENS = /^https:\/\/(www\.)?mytickets\.tours$|^http:\/\/localhost(:\d+)?$/;

function responder(context, status, corpo) {
  context.res = { status, headers: { "content-type": "application/json", "cache-control": "no-store" }, body: corpo };
}

module.exports = async function (context, req) {
  const origem = req.headers && req.headers.origin;
  if (origem && !ORIGENS.test(origem)) return responder(context, 403, { ok: false });

  const v = validar(req.body);
  if (v.robo) return responder(context, 200, { ok: true });
  if (v.erro) return responder(context, 400, { ok: false, erro: v.erro });

  try {
    const r = await inscrever(v.contato, { brevo: brevo(process.env), mailerlite: mailerlite(process.env) });
    if (r.semConfiguracao) return responder(context, 503, { ok: false, erro: "cadastro ainda não configurado" });
    context.log(`inscrição salva na ${r.ferramenta} (${v.contato.idioma})${r.conferida ? "" : ", sem conferir a outra ferramenta"}`);
    return responder(context, 200, { ok: true });
  } catch (e) {
    context.log.error(`falha na inscrição: ${e.message}`);
    return responder(context, 502, { ok: false });
  }
};
