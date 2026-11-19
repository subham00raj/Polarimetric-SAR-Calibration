# Thesis slides

Open `index.html` to present the deck. It loads `slide-01.html` through `slide-26.html` directly, so edits to a slide appear when you refresh the browser. There is no rebuild step for content, style, or animation changes. This also works when opening files directly without a web server.

- Individual `slide-NN.html` files contain each slide's markup and can also open independently.
- `assets/deck.css` contains shared styling.
- `assets/deck.js` contains charts, reveals, keyboard navigation, and the slide menu.
- `assets/fundamentals.js` contains the SAR animations.
- `assets/index.js` connects the individual pages into the presentation.
- `assets/slide-manifest.js` lists slide order and menu names.

Arrow keys reveal the next build, then advance between slides. Ordinary page clicks do not change slides; outline links, menu items, and animation controls remain clickable. `M` opens the menu, `F` toggles fullscreen, and `Home` / `End` jump to the beginning / end. A link such as `index.html#6` opens slide 6. Add `?static` for all slides in print mode.

Only run `python3 slides/build.py` if you add, remove, or rename slide pages, or change their menu names. It updates the manifest and does not overwrite `index.html`.

Keep the HTML files together with `assets/` so images, fonts, styles, and scripts resolve.
