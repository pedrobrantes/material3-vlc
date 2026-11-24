## Summary

What changed and why.

## Type

- [ ] Color preset
- [ ] Layout / UI change
- [ ] Bug fix
- [ ] Docs / CI

## Previews (if visual)

Attach PNGs rendered via `uv run m3vlc build --preset m3-brown-dark --preview`.

## Checklist

- [ ] `uv run ruff check src tests`
- [ ] `uv run mypy src`
- [ ] `uv run pytest -v`
- [ ] `uv run m3vlc validate <file.vlt>`
- [ ] No hardcoded hex colors outside presets
