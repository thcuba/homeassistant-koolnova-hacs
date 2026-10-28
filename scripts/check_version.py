#!/usr/bin/env python3
"""Check that the integration version agrees with the release tag.

``docs/RELEASE.md`` states the rule plainly: *"Tag and ``manifest.json`` MUST be identical"*. It
matters beyond tidiness - HACS reads ``manifest.json`` to decide whether an update is available, so a
manifest left behind while tags move on makes HACS offer the same update forever: it installs the
release, sees the old version still declared, and asks again.

That is exactly what happened here: the manifest sat at 2.0.4 while releases went to 2.0.9, because
nothing checked the two against each other.

Two checks, both usable from CI and by hand:

    # a tag is being pushed: the manifest must say exactly this
    python scripts/check_version.py --tag 2.0.9

    # any other moment: the manifest must not be older than the newest tag
    python scripts/check_version.py --not-older-than 2.0.9

Exit status is 0 when the check passes and 1 when it fails, with the reason on stderr.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "custom_components" / "koolnova" / "manifest.json"


def read_manifest_version(manifest_path: Path = MANIFEST_PATH) -> str:
    """The ``version`` field of the manifest."""
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    version = data.get("version")
    if not isinstance(version, str) or not version.strip():
        msg = f"{manifest_path} non dichiara una 'version' valida: {version!r}"
        raise ValueError(msg)
    return version.strip()


def normalise(tag: str) -> str:
    """Tags appear both bare and ``v``-prefixed (``2.0.9`` / ``v2.0.9``)."""
    stripped = tag.strip()
    return stripped[1:] if stripped[:1] in {"v", "V"} else stripped


def release_parts(version: str) -> tuple[int, ...]:
    """Numeric components of a release version, so 2.0.9 sorts after 2.0.4.

    Only the release part is compared: a suffix such as ``-beta`` is ignored rather than guessed at.
    """
    core = normalise(version).split("-", 1)[0].split("+", 1)[0]
    components = core.split(".")
    if not components or not all(component.isdigit() for component in components):
        msg = f"versione non riconosciuta: {version!r}"
        raise ValueError(msg)
    return tuple(int(component) for component in components)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--tag", help="tag della release: il manifest deve dichiarare esattamente questa versione")
    group.add_argument(
        "--not-older-than",
        dest="floor",
        help="versione piu' recente nota: il manifest non puo' essere piu' vecchio",
    )
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH, help="percorso del manifest.json")
    args = parser.parse_args(argv)

    try:
        version = read_manifest_version(args.manifest)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        return 1

    if args.tag is not None:
        expected = normalise(args.tag)
        if normalise(version) != expected:
            print(
                f"ERRORE: il tag '{args.tag}' e il manifest dichiarano versioni diverse "
                f"(manifest: '{version}').\n"
                f"        Allinea 'version' in custom_components/koolnova/manifest.json a "
                f"'{expected}' prima di pubblicare la release.",
                file=sys.stderr,
            )
            return 1
        print(f"OK: tag '{args.tag}' e manifest '{version}' coincidono.")
        return 0

    try:
        floor = normalise(args.floor)
        if release_parts(version) < release_parts(floor):
            print(
                f"ERRORE: il manifest dichiara '{version}', ma la release piu' recente e' '{args.floor}'.\n"
                f"        HACS confronta questa versione con l'ultima release: se resta indietro "
                f"propone lo stesso aggiornamento all'infinito.\n"
                f"        Porta 'version' almeno a '{floor}'.",
                file=sys.stderr,
            )
            return 1
    except ValueError as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        return 1
    print(f"OK: manifest '{version}' non e' piu' vecchio della release '{args.floor}'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
