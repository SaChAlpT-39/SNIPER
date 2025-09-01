import logging, logging.config, yaml, os

with open('config/logging.yml', 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)
logging.config.dictConfig(cfg)

log = logging.getLogger('sniper')

log.info('boot test: logger configured')
log.warning('boot test: warning visible (sniper)')

print('> Vérifie le fichier logs/system.log et la console pour les messages.')
