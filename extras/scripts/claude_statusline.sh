#!/usr/bin/env bash
# Claude Code statusline that also saves the rate-limit readings for project-continuity.
# Claude Code pipes JSON (incl. rate_limits.five_hour / seven_day with used_percentage and
# resets_at) to a statusLine command (needs a Pro/Max login; data appears after the first reply).
# Requires: jq.
#
# Install (one time, user level): copy this file to ~/.claude/statusline.sh, chmod +x, and in
# ~/.claude/settings.json set:
#   { "statusLine": { "type": "command", "command": "~/.claude/statusline.sh" } }
# If you already have a statusline script, paste the "save snapshot" block into it.
#
# Writes <project>/.continuity/quota/claude-code.json when the project has a .continuity/ folder.
# Add `.continuity/quota/` to .gitignore (it is local machine state).

in=$(cat)
dir=$(jq -r '.workspace.current_dir // .cwd // empty' <<<"$in")
fh=$(jq -r '.rate_limits.five_hour.used_percentage // empty' <<<"$in")
sd=$(jq -r '.rate_limits.seven_day.used_percentage // empty' <<<"$in")

# --- save snapshot -------------------------------------------------------------------------
if [ -n "$dir" ] && [ -n "$fh$sd" ]; then
  d="$dir"
  while [ "$d" != "/" ] && [ ! -d "$d/.continuity" ]; do d=$(dirname "$d"); done
  if [ -d "$d/.continuity" ]; then
    mkdir -p "$d/.continuity/quota"
    jq -n --argjson now "$(date +%s)" \
      --argjson f "${fh:-null}" --argjson s "${sd:-null}" \
      --argjson fr "$(jq '.rate_limits.five_hour.resets_at // null' <<<"$in")" \
      --argjson sr "$(jq '.rate_limits.seven_day.resets_at // null' <<<"$in")" '
      def w(u; r; now): if u == null then null
        else {observed_at: now, source: "claude-code statusline", used_percent: u, remaining_percent: (100 - u), resets_at: r} end;
      {observed_at: $now, source: "claude-code statusline",
       windows: ({five_hour: w($f; $fr; $now), seven_day: w($s; $sr; $now)} | with_entries(select(.value != null)))}' \
      > "$d/.continuity/quota/claude-code.json.tmp" 2>/dev/null \
      && mv "$d/.continuity/quota/claude-code.json.tmp" "$d/.continuity/quota/claude-code.json"
  fi
fi

# --- display -------------------------------------------------------------------------------
[ -z "$fh" ] && exit 0
printf '5h %s%% left' "$(awk -v u="$fh" 'BEGIN{printf "%d", 100-u}')"
[ -n "$sd" ] && printf ' · 7d %s%% left' "$(awk -v u="$sd" 'BEGIN{printf "%d", 100-u}')"
