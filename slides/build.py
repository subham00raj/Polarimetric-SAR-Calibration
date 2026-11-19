"""Refresh the slide manifest after adding, removing, or renaming slide pages."""
from pathlib import Path
import json
import hashlib
import re

root = Path(__file__).resolve().parent
pages = sorted(root.glob('slide-[0-9][0-9].html'))
if not pages:
    raise SystemExit('No slide HTML files found')
sections = []
manifest = []
for page in pages:
    matches = re.findall(r'<section\b[^>]*class="slide\b.*?</section>', page.read_text(), re.S)
    if len(matches) != 1:
        raise SystemExit(f'{page.name}: expected exactly one slide section')
    section = matches[0]
    name = re.search(r'data-name="([^"]+)"', section)
    if not name:
        raise SystemExit(f'{page.name}: missing slide name')
    sections.append(section)
    manifest.append({'file': page.name, 'name': name.group(1)})
(root / 'assets/slide-manifest.js').write_text('window.THESIS_SLIDES = ' + json.dumps(manifest, indent=2) + ';\n')
# Refresh the manifest URL whenever slide order or names change, including index.html.
version = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()[:12]
for page in [root / 'index.html', *pages]:
    html = page.read_text()
    html = re.sub(r'src="assets/slide-manifest\.js(?:\?[^"]*)?"',
                  f'src="assets/slide-manifest.js?v={version}"', html)
    page.write_text(html)
print(f'Updated manifest for {len(sections)} slides (version {version}). index.html loads pages directly.')
