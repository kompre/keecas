# Changelog

## [1.3.0](https://github.com/kompre/keecas/compare/v1.2.1...v1.3.0) (2026-09-18)


### Features

* consolidate skill CLI into `keecas skill install`/`print` ([9154f8f](https://github.com/kompre/keecas/commit/9154f8f0b130e34590c65e8c85b8b7f3343ef2e1))
* consolidate skill CLI into keecas skill install/print ([1f30c0e](https://github.com/kompre/keecas/commit/1f30c0ef0ccc541a389bd187e1ced3b370bbff77))


### Bug Fixes

* **cli:** fix install-skill for installed (non-editable) packages ([98e8fd9](https://github.com/kompre/keecas/commit/98e8fd912bdc6d97b6ee670266e50ec70fca4333))
* install-skill fails on real (non-editable) keecas installs ([df0e60d](https://github.com/kompre/keecas/commit/df0e60d3b53d69a2ba2228b9a7a8eb9c778f767b))
* **skill:** correct stale comma-escaping examples, add description-safety guidance ([10b059c](https://github.com/kompre/keecas/commit/10b059c7287047e9a0bbdc8ea4b44f30ccc46e8a))


### Documentation

* drop mandatory dev hop from branch strategy ([9202012](https://github.com/kompre/keecas/commit/92020120937cc1cefadcc9c318e3050850113900))
* drop mandatory dev hop from branch strategy ([bcea9ea](https://github.com/kompre/keecas/commit/bcea9ea3156d795ada2a8897205b390adc949598))

## [1.2.1](https://github.com/kompre/keecas/compare/v1.2.0...v1.2.1) (2026-08-28)


### Bug Fixes

* **keecas-notebook:** run %run as the very first cell, not after init ([072df11](https://github.com/kompre/keecas/commit/072df110252751075331b893cfff86b4b0e8cd25))
* **keecas-notebook:** run %run as the very first cell, not after init ([0b5680e](https://github.com/kompre/keecas/commit/0b5680e3ad9c0dc6b999c03147341c39a8810fdb))


### Documentation

* fix stale docs.yml trigger description in CONTRIBUTING.md ([56c16ef](https://github.com/kompre/keecas/commit/56c16efc9e894dfb163b3d87d0193be3ce3c5d1d))
* rewrite CLAUDE.md to be lean and reference-driven ([973dbce](https://github.com/kompre/keecas/commit/973dbce3913f0c889ab28d502351a15b52351750))

## [1.2.0](https://github.com/kompre/keecas/compare/v1.1.4...v1.2.0) (2026-07-07)


### Features

* add keecas-notebook Claude Code skill and install-skill CLI ([ac663cc](https://github.com/kompre/keecas/commit/ac663ccff23ca0e9f66cff4c6314e35ddfb731b6))
* add keecas-notebook Claude Code skill and install-skill command ([0dd5638](https://github.com/kompre/keecas/commit/0dd5638dad8ef99aa6fe31761b27a26661250a68))
* auto-wrap string values in PDF mode using varwidth environment ([166c55d](https://github.com/kompre/keecas/commit/166c55da529708ae1322ba1b9624131b6fc29576))
* **display:** auto-wrap long strings in PDF mode using varwidth ([cdcda91](https://github.com/kompre/keecas/commit/cdcda91773f0a160d4d3698ca944f6e1d76acf81))
* **display:** auto-wrap long strings in PDF mode using varwidth ([22e5602](https://github.com/kompre/keecas/commit/22e5602c0b55f13c0e5360519c5eb8636b1b2b49))
* **display:** replace katex condition with pdf_mode flag, add text_wrap_width config ([f9f0437](https://github.com/kompre/keecas/commit/f9f0437e950b46ae332bbe6e6ebbe408859d7423))
* wrap symbols() to auto-escape commas inside curly braces ([8d188ee](https://github.com/kompre/keecas/commit/8d188ee50db4ee7a255c85ff0da50ee37c7c17e5))
* wrap symbols() to auto-escape commas inside curly braces ([d4044f9](https://github.com/kompre/keecas/commit/d4044f9320817d138b5212ab1cc76bbc246e3c54))


### Bug Fixes

* **formatters:** fix negative coefficient parenthesization in format_mul ([44a0c85](https://github.com/kompre/keecas/commit/44a0c859c719f4976a74c7fdb8c312d6d02d1fd0))
* **formatters:** fix negative coefficient parenthesization in format_mul ([78dedb0](https://github.com/kompre/keecas/commit/78dedb0ecea91a7aa9b228cf2d0ba4f2b76eb0ee))
* **formatters:** restore magnitude-outside-unit display for compound fraction units ([8c11213](https://github.com/kompre/keecas/commit/8c11213a169c9f57dd3487915feda80bb8e26ef6))
* **formatters:** restore magnitude-outside-unit display for compound fraction units ([1b8cfbe](https://github.com/kompre/keecas/commit/1b8cfbe6325a69b56f65d7f944b4790b4c73adc1))
* **install-skill:** fall back to copytree on Windows when symlink is unavailable ([353be61](https://github.com/kompre/keecas/commit/353be61a43ff2285d8de38009996f9a85e46d5ea))


### Documentation

* **examples:** add text_wrap example to quarto_example notebook ([c7a415a](https://github.com/kompre/keecas/commit/c7a415aa945fd852db092a35cd56a28a3ccfe028))
