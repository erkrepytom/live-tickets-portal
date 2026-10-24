# Instala o servidor MCP meta-ads no Claude Code (Windows).
# Rode no PowerShell, de dentro desta pasta:   .\instalar.ps1
# Este script nunca digita nem imprime o seu token. Quem preenche e voce.

$ErrorActionPreference = "Stop"
$aqui = Split-Path -Parent $MyInvocation.MyCommand.Path

function Achar-Python {
    foreach ($candidato in @("python", "python3", "py")) {
        try {
            $versao = & $candidato --version 2>&1
            if ($LASTEXITCODE -eq 0) { return @{ cmd = $candidato; versao = "$versao" } }
        } catch { }
    }
    return $null
}

$py = Achar-Python
if ($null -eq $py) {
    Write-Host "Python nao encontrado no PATH. Instale pela Microsoft Store ou python.org e rode de novo." -ForegroundColor Red
    exit 1
}
Write-Host "Python: $($py.versao) (comando: $($py.cmd))" -ForegroundColor Green

$env_arquivo = Join-Path $aqui ".env"
if (-not (Test-Path $env_arquivo)) {
    Copy-Item (Join-Path $aqui ".env.exemplo") $env_arquivo
    Write-Host "Criei $env_arquivo a partir do exemplo." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Vou abrir o .env no Bloco de Notas. Preencha META_ACCESS_TOKEN e META_AD_ACCOUNT_ID," -ForegroundColor Cyan
Write-Host "salve e feche o Bloco de Notas. Nada do que voce digitar ali sai desta maquina." -ForegroundColor Cyan
Write-Host ""
Start-Process notepad.exe $env_arquivo -Wait

Write-Host "Conferindo o acesso na Graph API..." -ForegroundColor Cyan
& $py.cmd (Join-Path $aqui "servidor.py") --checar
$ok = ($LASTEXITCODE -eq 0)
if (-not $ok) {
    Write-Host ""
    Write-Host "O diagnostico acima nao fechou. Causas comuns:" -ForegroundColor Yellow
    Write-Host "  - token sem a permissao ads_read" -ForegroundColor Yellow
    Write-Host "  - id da conta sem o prefixo act_" -ForegroundColor Yellow
    Write-Host "  - versao da Graph API descontinuada (ajuste META_API_VERSAO no .env)" -ForegroundColor Yellow
    Write-Host "  - o System User nao tem acesso a essa conta de anuncios no Business Manager" -ForegroundColor Yellow
    Write-Host ""
}

$temClaude = $null -ne (Get-Command claude -ErrorAction SilentlyContinue)
if ($temClaude) {
    Write-Host "Registrando o servidor no Claude Code (escopo do usuario)..." -ForegroundColor Cyan
    $servidor = Join-Path $aqui "servidor.py"
    & claude mcp remove meta-ads --scope user 2>$null | Out-Null
    & claude mcp add meta-ads --scope user -- $py.cmd $servidor
    Write-Host "Pronto. Abra o Claude Code e rode /mcp para ver 'meta-ads' conectado." -ForegroundColor Green
} else {
    Write-Host "O comando 'claude' nao esta no PATH, entao nao registrei automaticamente." -ForegroundColor Yellow
    Write-Host "Abra o projeto no Claude Code: o .mcp.json da raiz ja declara o servidor," -ForegroundColor Yellow
    Write-Host "e o Claude Code vai pedir sua aprovacao na primeira vez." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Escrita (pausar campanha, mexer em orcamento) esta BLOQUEADA ate voce por" -ForegroundColor Magenta
Write-Host "META_PERMITIR_ESCRITA=1 no .env. Enquanto isso, so leitura." -ForegroundColor Magenta
