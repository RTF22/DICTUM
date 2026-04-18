# VOCIX Packaging

Manifests and drafts for distributing VOCIX via Windows package managers and community lists.

## winget (Microsoft)

Files: `winget/RTF22.VOCIX.*.yaml` (version, installer, locale).

Submission workflow (manual, ~30 min):

1. Fork [microsoft/winget-pkgs](https://github.com/microsoft/winget-pkgs).
2. Copy the three YAMLs to `manifests/r/RTF22/VOCIX/1.1.0/` in the fork.
3. Validate locally: `winget validate --manifest manifests/r/RTF22/VOCIX/1.1.0`.
4. Open a PR — title `New version: RTF22.VOCIX version 1.1.0`. CI runs `wingetcreate`/`Komac` validation + sandbox install. Review typically 1–3 days.
5. After merge: `winget install RTF22.VOCIX` works globally.

For future releases, easiest path: install [wingetcreate](https://github.com/microsoft/winget-create) and run
`wingetcreate update RTF22.VOCIX --version <new> --urls <zip-url> --submit`.

## Scoop

File: `scoop/vocix.json`.

Two options:

- **Own bucket** (recommended): create repo `RTF22/scoop-vocix`, drop `vocix.json` at the root. Users run `scoop bucket add vocix https://github.com/RTF22/scoop-vocix && scoop install vocix`.
- **scoop-extras PR**: open a PR against [ScoopInstaller/Extras](https://github.com/ScoopInstaller/Extras) with `bucket/vocix.json`. Review is slower but reach is wider.

`checkver: github` + `autoupdate` block means Scoop auto-picks up new GitHub releases.

## Awesome lists (Stage 5)

See `awesome-submissions.md` for drafted one-liners and target repos.
