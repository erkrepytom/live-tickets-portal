#!/usr/bin/env python3
"""Prepara a Brevo e a MailerLite para o formulário "Avise-me dos jogos". Roda uma vez só.

Cria (ou reaproveita, se já existirem):
  Brevo:      a lista "MyTickets - Avise-me (PT)" e os atributos IDIOMA, TIME, CIDADE, EVENTO, ORIGEM, CONSENTIMENTO
  MailerLite: o grupo "MyTickets - Notify me (EN/ES)" e os campos idioma, time, cidade, evento, origem, consentimento

No fim imprime BREVO_LIST_ID e MAILERLITE_GROUP_ID, que vão para as variáveis de ambiente
do Azure Static Web Apps junto com as duas chaves. Nunca imprime as chaves.

    BREVO_API_KEY=... MAILERLITE_API_KEY=... python scripts/email_configurar.py

Qualquer uma das chaves pode faltar: a ferramenta sem chave é pulada.
"""

import json
import os
import sys
import urllib.error
import urllib.request

LISTA_BREVO = "MyTickets - Avise-me (PT)"
GRUPO_MAILERLITE = "MyTickets - Notify me (EN/ES)"
CAMPOS = ["idioma", "time", "cidade", "evento", "origem", "consentimento"]


def pedir(metodo, url, cab, corpo=None):
    dados = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request(url, data=dados, method=metodo,
                                 headers={**cab, "accept": "application/json", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            texto = r.read().decode() or "{}"
            return r.status, json.loads(texto)
    except urllib.error.HTTPError as exc:
        texto = exc.read().decode(errors="replace")
        try:
            return exc.code, json.loads(texto or "{}")
        except ValueError:
            return exc.code, {"message": texto[:200]}


def brevo(chave):
    cab = {"api-key": chave}
    base = "https://api.brevo.com/v3"
    for nome in CAMPOS:
        st, r = pedir("POST", f"{base}/contacts/attributes/normal/{nome.upper()}", cab, {"type": "text"})
        print(f"  Brevo atributo {nome.upper()}: {'criado' if st in (200, 201, 204) else 'já existia' if st == 400 else f'erro {st} {r}'}")
    st, r = pedir("GET", f"{base}/contacts/lists?limit=50", cab)
    for lista in r.get("lists", []):
        if lista["name"] == LISTA_BREVO:
            return lista["id"]
    st, r = pedir("GET", f"{base}/contacts/folders?limit=10", cab)
    pastas = r.get("folders", [])
    if pastas:
        pasta = pastas[0]["id"]
    else:
        st, r = pedir("POST", f"{base}/contacts/folders", cab, {"name": "MyTickets"})
        pasta = r["id"]
    st, r = pedir("POST", f"{base}/contacts/lists", cab, {"name": LISTA_BREVO, "folderId": pasta})
    if st not in (200, 201):
        sys.exit(f"Brevo: não deu para criar a lista ({st} {r.get('message')})")
    return r["id"]


def mailerlite(chave):
    cab = {"authorization": f"Bearer {chave}"}
    base = "https://connect.mailerlite.com/api"
    st, r = pedir("GET", f"{base}/fields?limit=100", cab)
    existentes = {c["key"] for c in r.get("data", [])}
    for nome in CAMPOS:
        if nome in existentes:
            print(f"  MailerLite campo {nome}: já existia")
            continue
        st, r = pedir("POST", f"{base}/fields", cab, {"name": nome, "type": "text"})
        print(f"  MailerLite campo {nome}: {'criado' if st in (200, 201) else f'erro {st}'}")
    st, r = pedir("GET", f"{base}/groups?limit=100&filter[name]={urllib.request.quote(GRUPO_MAILERLITE)}", cab)
    for g in r.get("data", []):
        if g["name"] == GRUPO_MAILERLITE:
            return g["id"]
    st, r = pedir("POST", f"{base}/groups", cab, {"name": GRUPO_MAILERLITE})
    if st not in (200, 201):
        sys.exit(f"MailerLite: não deu para criar o grupo ({st} {r.get('message')})")
    return r["data"]["id"]


def main():
    kb, km = os.environ.get("BREVO_API_KEY"), os.environ.get("MAILERLITE_API_KEY")
    if not kb and not km:
        sys.exit("Defina BREVO_API_KEY e/ou MAILERLITE_API_KEY.")
    print("Variáveis para o Azure Static Web Apps (além das chaves):")
    if kb:
        print(f"BREVO_LIST_ID={brevo(kb)}")
    if km:
        print(f"MAILERLITE_GROUP_ID={mailerlite(km)}")


if __name__ == "__main__":
    main()
