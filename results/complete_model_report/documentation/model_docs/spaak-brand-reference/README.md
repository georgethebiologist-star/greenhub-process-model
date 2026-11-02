# Spaak Brand Reference Bundle

This folder preserves downloaded Spaak Circular Solutions website assets for future GreenHub dashboard design work.

## Saved Location

Use this folder in prompts:

`C:\my\Spaak\Greenhub\Model\docs\spaak-brand-reference\assets`

## Strong Design References

- `main.css` - primary Spaak website stylesheet. Contains the most useful brand tokens, layout conventions, typography rules, button styling, section rhythm, and colors.
- `Circulaire economie, duurzaam denken en doen - Spaak CS.html` - saved rendered page HTML with local asset references.
- `view-source_https___spaakcs.nl.html` - saved website source HTML with canonical remote URLs.
- `logo-text.svg` - dark Spaak wordmark.
- `spaak-footer.svg` - large light Spaak footer lockup including icon and wordmark.
- `Spaak logo icoon (1).png` - standalone dark circular Spaak icon.
- `circle-green.svg` and `circle-blue.svg` - simple circular brand motifs.
- `themas.svg`, `thema-blauw.svg`, `thema-geel.svg`, `thema-groen.svg`, `thema-roze.svg` - brand illustration/theme assets.
- `icon.json` - Lottie animation data for the header Spaak icon.

## Fonts Available

- `SuisseIntl-Regular-WebS.woff2` - body copy font.
- `SuisseIntl-SemiBold-WebS.woff2` - emphasized body/UI copy.
- `MarrSans-Semibold-Web.woff2` - semibold display/support font.
- `MarrSansCondensed-Semibold-Web.woff2` - condensed display heading font.

Missing from this bundle: `MarrSans-Regular-Web.woff2` and `.woff` fallback files referenced by `main.css`. The dashboard can still use Suisse for body text and Marr Sans Condensed/Semibold for headings.

## Brand Cues Found

- Main text/dark teal: `#0C3338`
- Background cream: `#EFEBE6`
- Green accent: `#408F4D`
- Blue accent: `#729AD2`
- Yellow accent: `#E4B839`
- Pink accent: `#D277A3` / `#D775A4`
- Website uses large condensed headings, rounded image/card treatments around 20px, clean cream backgrounds, and simple colored circular motifs.

## Lower-Priority / Runtime Files

These were saved for completeness but are less useful for dashboard design:

- `picturefill.min.js`
- `main.min.js`
- `main.js`
- `libs.min.js`
- `swiper-bundle.min.js`
- `lottie.min.js`
- `lottie-player.js`
- `lazysizes.min.js`
- `jquery.min.js`
- `jquery-3.6.0.min.js`
- `gsap.min.js`
- `frontend.min.js`
- `float.js`
- `api.js`
- `js`
- `webworker.js`
- `wp-emoji-release.min.js`
- `wp-emoji-loader.min.js`
- `swiper-bundle.min.css`
- `contentScript.css`
- `sciteFont.css`
- `styles__ltr.css`

`contentScript.css`, `sciteFont.css`, and `styles__ltr.css` appear to come from browser extensions or third-party tooling rather than Spaak's core website design.

`main.min.js` is the useful Spaak-specific website behavior file. It includes header/menu behavior, scroll reveal, carousel setup, quote hover animation, and logo Lottie animation loading from `templateUrl + /js/animations/icon.json` and `icon-white.json`.

`main.js` appears to be Kaspersky/browser-injected code, not Spaak website source. Do not use it as a design or implementation reference.

`js` is Google Tag Manager/analytics code. `api.js`, `webworker.js`, `frontend.min.js`, `float.js`, and the `wp-emoji-*` files are third-party/plugin runtime files. They are preserved only so the downloaded website snapshot remains understandable.

Potentially still missing if exact animation parity is desired:

- `icon-white.json`

`icon.json` is present, so the normal dark header icon animation can be reproduced. `icon-white.json` is only needed if a light/white animated footer or dark-background logo variant must match the website exactly.

## Suggested Prompt Reference

Ask future agents to inspect `main.css`, `logo-text.svg`, `spaak-footer.svg`, the theme SVGs, and the saved HTML before redesigning GreenHub. They should adapt the brand into a product dashboard, not copy the marketing site wholesale.
