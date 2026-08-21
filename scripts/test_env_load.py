import os

def load_env_file(path: str):
    if not os.path.exists(path):
        print('NO_FILE')
        return
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            key, val = line.split('=', 1)
            key = key.strip()
            val = val.strip()
            if key not in os.environ or not os.environ.get(key):
                os.environ[key] = val

p = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_env_file(p)
print('ENV_HAS_KEY', bool(os.environ.get('ARMORIQ_API_KEY')))
print('ENV_KEYS_SAMPLED', [k for k in ('ARMORIQ_API_KEY','GEMINI_API_KEY') if k in os.environ])
