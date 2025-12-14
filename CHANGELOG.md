# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.3.2] - 2025-12-14

### Fixed
* Fix single-period period spans in the query (e.g. `before='1 day'`).

## [2.3.1] - 2025-12-11

### Fixed
* Fix early exit after the first `DATASET_LOADER` entry.
* Fix logging repeated warnings when reading `DATASETS_CONFIG_PATH` raises `FileNotFoundError`.

## [2.3.0] - 2025-12-10

### Added
* Added several new log messages related to datasets.
* Added `PERFORMANCE_LOG_LEVEL` to control log level of most performance messages.

### Changed
* Improvements to the `QueryParameters` class:
  - Added `.get_splitter_kwargs() -> DatetimeIndexSplitterKwargs` method.
  - Added `.filter` parameter (requires user extensions).
  - Attempt to show correct widget type based (e.g. timedelta when `schedule='9 days'`).
* All performance messages are now logged by the `time_split_app.performance` logger.

### Fixed
* The `DurationWidget` now properly converts between units (e.g. hours and minutes).
* Fixed several issues where query parameters would overwrite user inputs on reload.
* Fixed a number of documentation and other minor issues.

## [2.2.1] - 2025-12-06

### Added
- Sanity check `DataLoaderWidget.get_prefix()` on startup.
- Log and display warnings when params do not contain expected prefixes.
- Discard params to do not contain the expected prefix for the chosen loader.

## [2.2.0] - 2025-12-06

### Added
- Support params for multiple custom loaders.
- Method `DataLoaderWidget.get_prefix()` (default returns `None` = automatic prefix).
- Add `"🔍 Show raw data"` gradient highlighting, formatting, and data summary widgets.

### Changed
- Render `📈 Aggregations per fold` figures in tabs.

## [2.1.2] - 2025-12-06

### Fixed
- Fix loading of local `datasets.toml`-files without `fsspec`.

## [2.1.1] - 2025-11-17

### Fixed
* Fix range when using dummy data query (e.g. `?data=1760745600-1763337600`).

## [2.1.0] - 2025-11-16

### Changed
* Reload bundled datasets on any config file change (instead of just processed content).

## [2.0.0] - 2025-11-16

### Added
* Python `3.14` is now fully tested and supported in CI/CD.
* Add `--port=8501` option to CLI.
* Add color and formatting options for `📈 Aggregations per fold` table.
* Add table display option the `📊 Folds` view.

### Changed
* Require `streamlit >= 1.49.1` and fix warnings.
* Update column style of `📈 Aggregations per fold` table.
* The `📊 Folds / Code snippets` section now uses `🐼 Pandas types` by default.
* The `📊 Folds / Code snippets` section now shows splits as a list as well.

### Fixed
* Updated a few broken links.
* Fix row and hour count in the `📈 Aggregations per fold` view.

## [1.1.0] - 2025-08-22

### Added
* Support multiple custom loaders. Params supported only for the primary loader.

## [1.0.3] - 2025-08-21
* Fix PyPI trusted publishing.

## [1.0.0] - 2025-08-21

### Added
* Options `config.CONFIGURE_PLOTTING` and `CONFIGURE_LOGGING` (default=`true` for both).
* Option `config.DATE_ONLY` (default=`true`).
* Option `config.DATA_GENERATOR_INITIAL_RANGE_FN` (default = last 30 days.)
* CLI commands `new` and `print-config`.

### Changed
* Bump PyPI `Development Status` classifier.
* Datetime and Duration widgets now use horizontal layouts by default.
* The `config.DATASETS_CONFIG_PATH` option now supports remote paths.

### Fixed
* Option `config.PERFORMANCE_LOG_LEVEL` is now mapped to the correct env var.

## [0.7.2] - 2025-07-17

### Fixed
* Various documentation issues.

## [0.7.1] - 2025-07-17

### Added
- New command `python -m time_split app new` - creates template project.

### Fixed
- Fixed `time-split` dependency version.

## [0.7.0] - 2025-07-16

### Added
* Support several now user customizations
  - Data loaders (env: `DATASET_LOADER`)
  - Split params selection function (env: `SPLIT_SELECT_FN`)
  - Plotting function (env: `PLOT_FN`)
  - Link function (env: `LINK_FN`)
* Make installable as an extra; `time-split[app]`
* New CLI, e.g. `python -m time_split app start`.

## [0.6.2] - 2025-03-28

### Changed
* Use more prominent error when no dataset is selected.

## [0.6.1] - 2025-01-25

### Changed
* Use `streamlit==1.41.1`.
* The Docker image is now multi-platform (`linux/amd64` + `linux/arm64`).
* Dataset cache timeout (`DATASET_CACHE_TTL`) increased from 1 hour to 12 hours.

### Fixed
* All datasets are now properly reloaded when the configuration file changes (`DATASET_CONFIG_CACHE_TTL=30`)

## [0.6.0] - 2024-08-31

### Changed
* Move out of `time_split` namespace.
* Use `time-split==0.6.0` and `streamlit==1.38.0`.

### Fixed
* Fixed a few documentation and examples issues.

* Branch from [time_split@v0.5.0](https://github.com/rsundqvist/time-split/blob/v0.5.0/CHANGELOG.md).


[Unreleased]: https://github.com/rsundqvist/time-split-app/compare/v2.3.2...HEAD
[2.3.2]: https://github.com/rsundqvist/time-split-app/compare/v2.3.1...v2.3.2
[2.3.1]: https://github.com/rsundqvist/time-split-app/compare/v2.3.0...v2.3.1
[2.3.0]: https://github.com/rsundqvist/time-split-app/compare/v2.2.1...v2.3.0
[2.2.1]: https://github.com/rsundqvist/time-split-app/compare/v2.2.0...v2.2.1
[2.2.0]: https://github.com/rsundqvist/time-split-app/compare/v2.1.2...v2.2.0
[2.1.2]: https://github.com/rsundqvist/time-split-app/compare/v2.1.1...v2.1.2
[2.1.1]: https://github.com/rsundqvist/time-split-app/compare/v2.1.0...v2.1.1
[2.1.0]: https://github.com/rsundqvist/time-split-app/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/rsundqvist/time-split-app/compare/v1.1.0...v2.0.0
[1.1.0]: https://github.com/rsundqvist/time-split-app/compare/v1.0.3...v1.1.0
[1.0.3]: https://github.com/rsundqvist/time-split-app/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/rsundqvist/time-split-app/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/rsundqvist/time-split-app/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/rsundqvist/time-split-app/compare/v0.7.2...v1.0.0
[0.7.2]: https://github.com/rsundqvist/time-split-app/compare/v0.7.1...v0.7.2
[0.7.1]: https://github.com/rsundqvist/time-split-app/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/rsundqvist/time-split-app/compare/v0.6.2...v0.7.0
[0.6.2]: https://github.com/rsundqvist/time-split-app/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/rsundqvist/time-split-app/compare/v0.6.0...v0.6.1
[0.1.0]: https://github.com/rsundqvist/time-split-app/compare/v0.0.0...v0.6.0
