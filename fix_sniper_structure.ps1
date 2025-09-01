# 📌 Script de normalisation SniperV4 (V2 idempotent)
Write-Host "=== 🚀 Début du script de normalisation SniperV4 ==="

# -- 0) Normaliser le nom du dossier interface-app -> interface_app
if (Test-Path "interface-app") {
    Rename-Item "interface-app" "interface_app" -Force
    Write-Host "Renommé: interface-app → interface_app"
}

# -- 1) Dossiers à s'assurer d'exister
$mustHaveDirs = @(
    "sniper_engine",
    "orderflow",
    "trap_simulator",
    "vectorx",
    "sentiment_macro",
    "sniper_compta",
    "journal_ia",
    "interface_app",
    "alerting",
    "modules_utils",
    "tests",
    "tests/unit",
    "tests/integration",
    "logs",
    "data/archived_backtests",
    "data/models"
)

foreach ($d in $mustHaveDirs) {
    if (-Not (Test-Path $d)) {
        New-Item -ItemType Directory -Path $d | Out-Null
        Write-Host "Créé dossier: $d"
    }
}

# -- 2) Créer __init__.py là où il manque
$packages = @(
    "sniper_engine",
    "orderflow",
    "trap_simulator",
    "vectorx",
    "sentiment_macro",
    "sniper_compta",
    "journal_ia",
    "interface_app",
    "alerting",
    "modules_utils",
    "tests",
    "tests/unit",
    "tests/integration"
)

foreach ($p in $packages) {
    $init = Join-Path $p "__init__.py"
    if (-Not (Test-Path $init)) {
        New-Item -ItemType File -Path $init | Out-Null
        Write-Host "Ajouté: $init"
    }
}

# -- 3) Renommages critiques si les sources existent
$renames = @{
    "sniper_engine\rsik_manager.py" = "sniper_engine\risk_manager.py";
    "sentiment_macro\new_parser.py" = "sentiment_macro\news_parser.py";
    "test_suite_tunner.py"          = "test_suite_runner.py";
    "tests\test_suite_tunner.py"    = "tests\test_suite_runner.py"
}

foreach ($src in $renames.Keys) {
    $dst = $renames[$src]
    if (Test-Path $src) {
        Rename-Item -Path $src -NewName $dst -Force
        Write-Host "Renommé: $src → $dst"
    }
}

# -- 4) .gitignore : créer s'il n'existe pas, puis ajouter les règles si absentes
$gitignorePath = ".gitignore"
if (-Not (Test-Path $gitignorePath)) {
    New-Item -ItemType File -Path $gitignorePath | Out-Null
    Write-Host "Créé: .gitignore"
}

$rules = @"
# Logs & DB
logs/*
!logs/.gitkeep
*.log
*.sqlite

# Data artifacts
data/archived_backtests/**
data/models/**
"@

# Ajouter .gitkeep dans logs
$gitkeep = "logs\.gitkeep"
if (-Not (Test-Path $gitkeep)) {
    New-Item -ItemType File -Path $gitkeep | Out-Null
}

# Ajouter les règles si elles ne sont pas déjà là
$existing = Get-Content $gitignorePath -ErrorAction SilentlyContinue
if ($existing -notmatch "logs/\*" -or $existing -notmatch "\.sqlite") {
    Add-Content -Path $gitignorePath -Value $rules
    Write-Host ".gitignore mis à jour"
}

Write-Host "=== ✅ Normalisation terminée ==="
