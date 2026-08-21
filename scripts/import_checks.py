import importlib, sys
mods = [
    'app.armoriq.client',
    'app.armoriq.test_shim',
    'app.tools.scholarship_tools',
    'app.agent.orchestrator',
]
for m in mods:
    try:
        importlib.import_module(m)
        print('OK:', m)
    except Exception as e:
        print('ERROR importing', m, e)
        sys.exit(1)
print('IMPORT CHECKS PASSED')
