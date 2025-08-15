# WordSeek

An offline dictionary for StarDict format, a hobby project in progress. If you need a feature-rich app, there is GoldenDict. This is an experiment to have alternative UIs, GNOME native and CLI

## Dev Notes
* Interestingly it's possible to marry Glib UI event loop, asyncio event loop and reactivex
* For Pyright we stick with the default stubs' folder name `typings`.
  See [Type Stub Files](https://microsoft.github.io/pyright/#/type-stubs)
* For Mypy there is a configuration in `[mypy]` section for this in `pyproject.toml`