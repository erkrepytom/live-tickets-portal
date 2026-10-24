#!/usr/bin/env bash
# Instala o servidor MCP meta-ads no Claude Code (Linux, macOS, WSL).
#   bash instalar.sh
# Este script nunca digita nem imprime o seu token.
set -euo pipefail
aqui="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

py=""
for candidato in python3 python; do
  if command -v "$candidato" >/dev/null 2>&1; then py="$candidato"; break; fi
done
[ -n "$py" ] || { echo "Python nao encontrado no PATH."; exit 1; }
echo "Python: $($py --version) ($py)"

if [ ! -f "$aqui/.env" ]; then
  cp "$aqui/.env.exemplo" "$aqui/.env"
  chmod 600 "$aqui/.env"
  echo "Criei $aqui/.env a partir do exemplo."
fi

echo
echo "Preencha META_ACCESS_TOKEN e META_AD_ACCOUNT_ID em:"
echo "  $aqui/.env"
echo "Depois rode este script de novo, ou direto:  $py $aqui/servidor.py --checar"
echo

if grep -q '^META_ACCESS_TOKEN=.\+' "$aqui/.env"; then
  echo "Conferindo o acesso na Graph API..."
  "$py" "$aqui/servidor.py" --checar || echo "O diagnostico nao fechou — confira permissao, prefixo act_ e META_API_VERSAO."
  if command -v claude >/dev/null 2>&1; then
    claude mcp remove meta-ads --scope user >/dev/null 2>&1 || true
    claude mcp add meta-ads --scope user -- "$py" "$aqui/servidor.py"
    echo "Registrado. Rode /mcp no Claude Code para ver 'meta-ads'."
  else
    echo "Comando 'claude' fora do PATH; o .mcp.json da raiz do projeto ja declara o servidor."
  fi
fi

echo
echo "Escrita bloqueada ate META_PERMITIR_ESCRITA=1 no .env."
