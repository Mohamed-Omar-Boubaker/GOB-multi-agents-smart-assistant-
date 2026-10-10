import os, re

def fix_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content

    # Fix 1: logger.py line 45 pattern
    content = content.replace(
        "f\"AgentIntelligent_{log_file.replace('/', '_').replace('\\\\', '_')}\"",
        "\"AgentIntelligent_\" + log_file.replace('/', '_').replace('\\\\', '_')"
    )
    content = content.replace(
        "f\"AgentIntelligent_{log_file.replace('/', '_').replace('\\', '_')}\"",
        "\"AgentIntelligent_\" + log_file.replace('/', '_').replace('\\\\', '_')"
    )

    # Fix 2: agent_core.py line 1585 pattern
    content = content.replace(
        "f\"✅ Rappel '{payload.get('title', 'tâche')}' créé pour {payload.get('date', 'aujourd\\'hui')}\"",
        "\"✅ Rappel '\" + payload.get('title', 'tâche') + \"' créé pour \" + payload.get('date', \"aujourd'hui\")"
    )

    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ Fixed: {path}")
    
    return content != original

# Scan all .py files in backend/
fixed = 0
for root, dirs, files in os.walk('backend'):
    dirs[:] = [d for d in dirs if d != 'venv']
    for fname in files:
        if fname.endswith('.py'):
            if fix_file(os.path.join(root, fname)):
                fixed += 1

print(f"\nDone — {fixed} file(s) fixed.")