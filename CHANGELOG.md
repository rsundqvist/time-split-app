# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.7.2] - 2025-07-17

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


[Unreleased]: https://github.com/rsundqvist/time-split-app/compare/v0.7.2...HEAD
[0.7.2]: https://github.com/rsundqvist/time-split-app/compare/v0.7.1...v0.7.2
[0.7.1]: https://github.com/rsundqvist/time-split-app/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/rsundqvist/time-split-app/compare/v0.6.2...v0.7.0
[0.6.2]: https://github.com/rsundqvist/time-split-app/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/rsundqvist/time-split-app/compare/v0.6.0...v0.6.1
[0.1.0]: https://github.com/rsundqvist/time-split-app/compare/v0.0.0...v0.6.0
