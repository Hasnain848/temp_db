"""Bulk replace emojis with Lucide icons across all HTML templates."""
import os
import re

replacements = {
    '\U0001f4ca': '<i data-lucide="bar-chart-2" style="width:16px;height:16px;"></i>',
    '\U0001f4da': '<i data-lucide="book-open" style="width:16px;height:16px;"></i>',
    '\U0001f4cb': '<i data-lucide="clipboard" style="width:16px;height:16px;"></i>',
    '\U0001f4dd': '<i data-lucide="edit-3" style="width:16px;height:16px;"></i>',
    '\U0001f393': '<i data-lucide="graduation-cap" style="width:16px;height:16px;"></i>',
    '\U0001f464': '<i data-lucide="user" style="width:16px;height:16px;"></i>',
    '\U0001f465': '<i data-lucide="users" style="width:16px;height:16px;"></i>',
    '\u2705': '<i data-lucide="check-circle" style="width:16px;height:16px;"></i>',
    '\U0001f4c5': '<i data-lucide="calendar" style="width:16px;height:16px;"></i>',
    '\U0001f4c8': '<i data-lucide="trending-up" style="width:16px;height:16px;"></i>',
    '\U0001f468\u200d\U0001f3eb': '<i data-lucide="briefcase" style="width:16px;height:16px;"></i>',
    '\U0001f3af': '<i data-lucide="target" style="width:16px;height:16px;"></i>',
    '\u2795': '<i data-lucide="plus" style="width:14px;height:14px;"></i>',
    '\U0001f50d': '<i data-lucide="search" style="width:16px;height:16px;"></i>',
    '\u2b05': '<i data-lucide="log-out" style="width:14px;height:14px;"></i>',
    '\U0001f319': '<i data-lucide="moon" style="width:14px;height:14px;"></i>',
    '\u2600\ufe0f': '<i data-lucide="sun" style="width:14px;height:14px;"></i>',
    '\u26a0\ufe0f': '<i data-lucide="alert-triangle" style="width:16px;height:16px;"></i>',
    '\U0001f3c6': '<i data-lucide="award" style="width:16px;height:16px;"></i>',
    '\U0001f947': '1st',
    '\U0001f948': '2nd',
    '\U0001f949': '3rd',
    '\U0001f512': '<i data-lucide="lock" style="width:14px;height:14px;"></i>',
    '\U0001f511': '<i data-lucide="key" style="width:14px;height:14px;"></i>',
    '\U0001f3e2': '<i data-lucide="building" style="width:16px;height:16px;"></i>',
    '\U0001f4bc': '<i data-lucide="briefcase" style="width:16px;height:16px;"></i>',
    '\U0001f4de': '<i data-lucide="phone" style="width:16px;height:16px;"></i>',
    '\U0001f4e7': '<i data-lucide="mail" style="width:16px;height:16px;"></i>',
    '\U0001f389': '<i data-lucide="inbox" style="width:16px;height:16px;"></i>',
    '\U0001f4b0': '<i data-lucide="dollar-sign" style="width:16px;height:16px;"></i>',
    '\u26a1': '<i data-lucide="zap" style="width:16px;height:16px;"></i>',
    '\U0001f4a1': '<i data-lucide="lightbulb" style="width:16px;height:16px;"></i>',
    '\U0001f4cc': '<i data-lucide="map-pin" style="width:16px;height:16px;"></i>',
    '\U0001f6e1': '<i data-lucide="shield" style="width:16px;height:16px;"></i>',
}

templates_dir = r'd:\Smart_Campus_Hub-main\Smart_Campus_Hub-main\templates'
count = 0

for root, dirs, files in os.walk(templates_dir):
    for fname in files:
        if not fname.endswith('.html'):
            continue
        fpath = os.path.join(root, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        original = content
        for emoji, icon in replacements.items():
            content = content.replace(emoji, icon)
        
        # Fix empty-state-icon: icons inside should be 48px
        content = re.sub(
            r'(<div class="empty-state-icon">)<i data-lucide="([^"]+)" style="width:16px;height:16px;"></i>(</div>)',
            r'\1<i data-lucide="\2" style="width:48px;height:48px;"></i>\3',
            content
        )
        
        # Fix stat-card-icon: icons inside should be 22px
        content = re.sub(
            r'(<div class="stat-card-icon[^"]*">)<i data-lucide="([^"]+)" style="width:16px;height:16px;"></i>(</div>)',
            r'\1<i data-lucide="\2" style="width:22px;height:22px;"></i>\3',
            content
        )
        
        if content != original:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(content)
            count += 1
            print(f'Updated: {os.path.relpath(fpath, templates_dir)}')

print(f'\nTotal files updated: {count}')
