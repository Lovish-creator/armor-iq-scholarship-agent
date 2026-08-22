import os
import uvicorn


def load_env_file(path: str):
    """Manually load simple KEY=VALUE pairs from a .env file into os.environ.

    This avoids relying on external dotenv behavior in different shells.
    """
    if not os.path.exists(path):
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
            # Strip surrounding quotes if present
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            # Set value if not present or present but empty
            if key not in os.environ or not os.environ.get(key):
                os.environ[key] = val


def ensure_env_defaults():
    """Ensure minimal environment defaults so the agent can start locally.

    Sets `ARMORIQ_BASE_URL` to the official default if not present, and a
    sensible `PORTAL_BASE_URL` for the mock portal.
    """
    if not os.environ.get('ARMORIQ_BASE_URL'):
        # SDK default backend endpoint
        os.environ['ARMORIQ_BASE_URL'] = 'https://api.armoriq.ai'

    if not os.environ.get('PORTAL_BASE_URL'):
        os.environ['PORTAL_BASE_URL'] = 'http://127.0.0.1:8001'


if __name__ == '__main__':
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_env_file(env_path)
    # Debug: report whether key is loaded (do not print value)
    present = bool(os.environ.get('ARMORIQ_API_KEY'))
    # Also report whether the .env file contains a non-empty ARMORIQ_API_KEY line
    dotenv_has = False
    dotenv_nonempty = False
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip().startswith('ARMORIQ_API_KEY'):
                    dotenv_has = True
                    parts = line.split('=', 1)
                    if len(parts) > 1 and parts[1].strip():
                        dotenv_nonempty = True
                    break

    print('ARMORIQ_KEY_PRESENT' if present else 'ARMORIQ_KEY_MISSING', 'DOTENV_HAS_KEY' if dotenv_has else 'DOTENV_NO_KEY', 'DOTENV_NONEMPTY' if dotenv_nonempty else 'DOTENV_EMPTY')
    # Start Uvicorn; app.main will read os.environ at import time
    uvicorn.run('app.main:app', host='127.0.0.1', port=8000)
