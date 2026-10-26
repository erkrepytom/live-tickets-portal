// node --test (dentro de api/): confere o roteamento e a checagem de duplicados sem chamar a rede.
const test = require("node:test");
const assert = require("node:assert");
const { validar, inscrever } = require("./compartilhado/inscricao");
const { brevo, mailerlite } = require("./compartilhado/provedores");

function falsa(nome, { configurada = true, tem = [], quebra = false } = {}) {
  const salvos = [];
  return { nome, configurada, salvos,
    async existe(email) { if (quebra) throw new Error("fora do ar"); return tem.includes(email); },
    async salvar(c) { salvos.push(c.email); } };
}
const contato = idioma => validar({ email: "Ana@Email.com", consentimento: true, idioma, time: "Flamengo" }).contato;

test("português vai para a Brevo, inglês e espanhol para a MailerLite", async () => {
  for (const [idioma, esperado] of [["pt", "brevo"], ["en", "mailerlite"], ["es", "mailerlite"]]) {
    const r = await inscrever(contato(idioma), { brevo: falsa("brevo"), mailerlite: falsa("mailerlite") });
    assert.strictEqual(r.ferramenta, esperado);
  }
});

test("e-mail que já está na outra ferramenta é atualizado lá, não duplicado", async () => {
  const b = falsa("brevo", { tem: ["ana@email.com"] }), m = falsa("mailerlite");
  const r = await inscrever(contato("en"), { brevo: b, mailerlite: m });
  assert.strictEqual(r.ferramenta, "brevo");
  assert.deepStrictEqual(b.salvos, ["ana@email.com"]);
  assert.deepStrictEqual(m.salvos, []);
});

test("só uma ferramenta configurada recebe tudo; nenhuma = sem configuração", async () => {
  const r = await inscrever(contato("pt"), { brevo: falsa("brevo", { configurada: false }), mailerlite: falsa("mailerlite") });
  assert.strictEqual(r.ferramenta, "mailerlite");
  const n = await inscrever(contato("pt"), { brevo: falsa("brevo", { configurada: false }), mailerlite: falsa("mailerlite", { configurada: false }) });
  assert.ok(n.semConfiguracao);
});

test("se a outra ferramenta estiver fora do ar, a inscrição não se perde", async () => {
  const b = falsa("brevo"), m = falsa("mailerlite", { quebra: true });
  const r = await inscrever(contato("pt"), { brevo: b, mailerlite: m });
  assert.strictEqual(r.ferramenta, "brevo");
  assert.strictEqual(r.conferida, false);
});

test("validação: e-mail, consentimento e robô", () => {
  assert.ok(validar({ email: "x", consentimento: true }).erro);
  assert.ok(validar({ email: "a@b.com", consentimento: false }).erro);
  assert.ok(validar({ email: "a@b.com", consentimento: true, site: "spam" }).robo);
  assert.strictEqual(validar({ email: "a@b.com", consentimento: true, idioma: "fr" }).contato.idioma, "en");
});

test("chamadas HTTP das duas ferramentas", async () => {
  const pedidos = [];
  const fetchFn = async (url, op = {}) => { pedidos.push({ url, op }); return { ok: !url.includes("/subscribers/") && !url.includes("/contacts/"), status: url.match(/\/(subscribers|contacts)\//) ? 404 : 201, text: async () => "" }; };
  const b = brevo({ BREVO_API_KEY: "k", BREVO_LIST_ID: "7" }, fetchFn);
  const m = mailerlite({ MAILERLITE_API_KEY: "t", MAILERLITE_GROUP_ID: "99" }, fetchFn);
  assert.strictEqual(await b.existe("a+b@c.com"), false);
  assert.strictEqual(await m.existe("a@c.com"), false);
  await b.salvar(contato("pt"));
  await m.salvar(contato("en"));
  const corpoB = JSON.parse(pedidos[2].op.body), corpoM = JSON.parse(pedidos[3].op.body);
  assert.ok(pedidos[0].url.endsWith("a%2Bb%40c.com"));
  assert.deepStrictEqual(corpoB.listIds, [7]);
  assert.strictEqual(corpoB.updateEnabled, true);
  assert.strictEqual(corpoB.attributes.TIME, "Flamengo");
  assert.deepStrictEqual(corpoM.groups, ["99"]);
  assert.strictEqual(corpoM.fields.time, "Flamengo");
  assert.strictEqual(pedidos[3].op.headers.authorization, "Bearer t");
});
