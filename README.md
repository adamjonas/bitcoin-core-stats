# Bitcoin repo stats

Create stats on the Bitcoin github repo. Creates global and per-used stats,
based on flags based to `repo_stats.py`.

## Usage

- Clone the [bitcoin-gh-meta repository](https://github.com/zw/bitcoin-gh-meta) and set
  the `GH_META_DIR` parameter in `repo_stats.py`.
- Run `repo_stats.py -b` to generate the comma separated value files of repo
  stats.
- Run `repo_stats.py -g` for global stats and `repo_stats.py -c <contributor>`
  for contributor stats. Use the `-y <year>` flag to generate stats for a
  different year.

Run `repo_stats.py --help` to print help text.
