# Koolnova Integration Release Process

## Versioning

Versions are managed in `manifest.json`.

### Version Scheme
- **MAJOR**: Incompatible API or feature changes
- **MINOR**: Backward-compatible new features
- **PATCH**: Bug fixes and minor improvements

## Git Tags

Create tags for each release following semantic versioning.

## HACS Compatibility

This integration is HACS (Home Assistant Community Store) compatible:

- **Type**: Integration
- **Installation method**: GitHub release (standard GitHub releases)
- **Repository URL**: https://github.com/thcuba/homeassistant-koolnova

### HACS Requirements
- `manifest.json` with correct metadata
- `hacs.json` with complete configuration
- Translation files in `translations/` (optional)
- Clear documentation

### Required HACS Configuration (`hacs.json`)

The `hacs.json` file should include the following fields:

```json
{
  "name": "Koolnova",
  "homeassistant": "2024.12.0",
  "country": ["IT"]
}
```

**Critical fields**:
- `"homeassistant"`: Minimum compatible version.
- `"country"`: List of countries where the integration is relevant.

## Changelog

### v1.2.5
- Maintenance release
- Metadata synchronization and documentation updates
- Internal consistency checks for HACS compliance

### v1.2.0
- 🚨 **CRITICAL FIX**: Resolved import conflict that caused 404 errors
- ✅ Removed conflicting PyPI package `koolnova-api`
- ✅ Renamed local module to `koolnova_api` (underscore)
- ✅ Implemented relative imports for stability
- ✅ Added `__init__.py` to module directory
- 📈 Performance optimized: local code only, no external dependencies

### v1.1.0
- Improved coordinator polling
- Global zone control support
- HVAC mapping optimizations
- Sensor update bug fixes

### v1.0.0
- Initial release
- Basic project and zone support
- Individual temperature and mode control

## Release Process

### ⚠️ CRITICAL: HACS-Compatible Structure

**HACS requires standard GitHub structure, NOT custom ZIPs**

### 📁 Required Directory Structure

```
REPOSITORY_ROOT/
├── custom_components/
│   └── koolnova/          ← Domain name
│       ├── __init__.py
│       ├── manifest.json  ← Version MUST match tag
│       ├── climate.py
│       └── ... (all integration files)
├── README.md              ← Root documentation
└── hacs.json              ← HACS config in root
```

### 🔧 Required HACS Configuration (`hacs.json`)

```json
{
  "name": "Koolnova",
  "homeassistant": "2024.12.0",
  "country": ["IT"]
}
```

**Note**: Do not include `domain`, `repository`, `categories`, or `zip_release` in `hacs.json` as they are either redundant or invalid for integrations and can cause CI failures.

### Steps for HACS-Compatible Release

1. **Development**: Implement changes in a feature branch
2. **Testing**: Verify functionality in Home Assistant
3. **Update JSON files**:
   - `manifest.json`: Set `"version"` to match upcoming tag (e.g., `v1.2.1` → `"version": "1.2.1"`)
   - `hacs.json`: Verify `"domain"` matches `manifest.json`
4. **Commit**: `git commit -m "Release vX.Y.Z"`
5. **Tag**: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
6. **Push**: `git push origin main --tags`
7. **Create GitHub Release**: Use GitHub UI (no custom workflows needed)
8. **HACS**: Users can now update via HACS

### 🎯 Key HACS Requirements

- **Structure**: Standard GitHub (`repository-version/custom_components/domain/...`)
- **Required files**:
  - `custom_components/koolnova/manifest.json` (correct version)
  - `hacs.json` (correct domain in root)
  - `README.md` (root documentation)
- **Versions**: Tag and `manifest.json` MUST be identical
- **Releases**: Standard GitHub releases (no custom assets)

### ❌ Common Error: Version Mismatch

**PROBLEM**: If `manifest.json` does not match the tag, HACS shows:
```
Downloading luisgsluis/homeassistant-koolnova with version vX.Y.Z failed with (No content to download)
```

**PROBLEM 2**: HACS keeps offering the same update. It reads `manifest.json` to decide whether an
update is available, so if the manifest is behind while the tags move on it installs the release,
still sees the old version declared, and proposes the update again - forever.

**SOLUTION**: Ensure that:
- Tag is `v1.2.1`
- `manifest.json` has `"version": "1.2.1"`
- They are exactly identical (no prefix/suffix)

**Enforced automatically**: `scripts/check_version.py`, run by the `Release version` workflow. A
pushed tag whose `manifest.json` disagrees fails the build, and a pull request whose manifest has
fallen behind the newest tag fails too - so the drift cannot go unnoticed again. Both checks run
locally as well:

```bash
python scripts/check_version.py --tag 2.0.9                        # a release about to be tagged
python scripts/check_version.py --not-older-than $(git tag --sort=-creatordate | head -1)
```

## Distribution

- **HACS**: Automatic updates
- **Manual**: Download from GitHub releases
- **Beta**: Use `dev` branch for testing

## Pre-Release Checklist

- [ ] All changes tested in Home Assistant
- [ ] `manifest.json` version matches upcoming tag (`python scripts/check_version.py --tag <tag>`)
- [ ] `hacs.json` configured correctly
- [ ] `custom_components/` directory present
- [ ] All imports use relative syntax (development rule check)
- [ ] No PyPI dependencies except HA core
- [ ] Documentation updated
- [ ] CHANGELOG entry added