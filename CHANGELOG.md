# Changelog

## 1.2.33

- Map the DSH 44.7 tool names (`pwsh`, `working_directory`, `read_image`,
  `terminal_*`, goal/schedule/session/cordis) so tool rows keep their pixel
  item instead of falling back to the native glyph.
- Fall back to a chest for unknown tool names and to the host's variant family
  for renamed tools, so later host upgrades stay themed.

## 1.2.32

- Replace the like/dislike splash potions with upright, centred-cork potions.

## 1.2.31

- Add compatibility mappings for the tested Linux Web build of DSH 0.2.2-rc.1
  while retaining the existing desktop selectors.
- Keep the theme stylesheet after dynamically loaded host styles and clean up
  observers on disposal, including when two instances overlap during reload.
- Package the standalone theme with its embedded artwork and fonts.
