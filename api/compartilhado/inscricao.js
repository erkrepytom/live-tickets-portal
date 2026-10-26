// Regra única de roteamento, para ninguém ficar nas duas listas:
//  1. Português vai para a Brevo; inglês e espanhol vão para a MailerLite.
//  2. Antes de cadastrar, confere se o e-mail já está na OUTRA ferramenta. Se estiver,
//     atualiza o contato lá (time, cidade, jogo) e não cria um segundo.
//  3. Se só uma das ferramentas estiver configurada, tudo vai para ela.

const IDIOMAS = ["pt", "en", "es"];
const EMAIL = /^[^\s@]{1,64}@[^\s@]{1,190}\.[^\s@]{2,}$/;

function limpar(v, max = 60) {
  return typeof v === "string" ? v.replace(/[\u0000-\u001f<>]/g, "").trim().slice(0, max) : "";
}

// Devolve { contato } ou { erro } com o que veio do formulário.
function validar(corpo) {
  if (!corpo || typeof corpo !== "object") return { erro: "corpo inválido" };
  if (corpo.site) return { robo: true }; // campo escondido preenchido = robô
  const email = limpar(corpo.email, 254).toLowerCase();
  if (!EMAIL.test(email)) return { erro: "e-mail inválido" };
  if (corpo.consentimento !== true) return { erro: "sem consentimento" };
  const idioma = IDIOMAS.includes(corpo.idioma) ? corpo.idioma : "en";
  return {
    contato: {
      email, idioma,
      nome: limpar(corpo.nome), time: limpar(corpo.time), cidade: limpar(corpo.cidade),
      evento: limpar(corpo.evento, 120).replace(/[^a-z0-9-]/g, ""),
      pagina: limpar(corpo.pagina, 200),
      consentidoEm: new Date().toISOString(),
    },
  };
}

// provedores = { brevo, mailerlite }, cada um com nome, configurada, existe(), salvar().
async function inscrever(contato, provedores) {
  const { brevo, mailerlite } = provedores;
  let destino = contato.idioma === "pt" ? brevo : mailerlite;
  let outra = destino === brevo ? mailerlite : brevo;
  if (!destino.configurada) [destino, outra] = [outra, destino];
  if (!destino.configurada) return { semConfiguracao: true };
  let conferida = true;
  if (outra.configurada) {
    try {
      if (await outra.existe(contato.email)) destino = outra;
    } catch (e) {
      // Melhor guardar a inscrição com risco de duplicar do que perder a pessoa.
      conferida = false;
    }
  }
  await destino.salvar(contato);
  return { ferramenta: destino.nome, conferida };
}

module.exports = { validar, inscrever };
