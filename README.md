# virtualvault_backend
Backend for Virtual Vault, which serves assets and an Elasticsearch index over HTTP.

## Getting Started

If you have [git](https://git-scm.com/) and [Docker](https://www.docker.com/community-edition) installed, using this repository is as simple as:

```
git clone https://github.com/RockefellerArchiveCenter/virtualvault_backend.git
cd virtualvault_backend
docker compose build
docker compose up
```

## Usage

By default, this app runs an update job at midnight every day (this schedule can be changed by editing the `crontab` file) which indexes metadata that has been updated in ArchivesSpace for existing items and also indexes metadata for new items.


## Expected Asset Structure

This app expects an assets directory with a specific structure:

```
/assets/
    /audio/
        00455a772f0d2c3dde0bb2847243b2e2/
            00455a772f0d2c3dde0bb2847243b2e2.mp3
        ...
    /catalogued-reports/
        00455a772f0d2c3dde0bb2847243b2e3/
            00455a772f0d2c3dde0bb2847243b2e3.pdf
        ...
    /moving-image/
        00455a772f0d2c3dde0bb2847243b2e4/
            00455a772f0d2c3dde0bb2847243b2e4.mp4
        ...
```

## License

This code is released under the MIT License.

## Contributing

This is an open source project and we welcome contributions! If you want to fix a bug, or have an idea of how to enhance the application, the process looks like this:

1. File an issue in this repository. This will provide a location to discuss proposed implementations of fixes or enhancements, and can then be tied to a subsequent pull request.
2. If you have an idea of how to fix the bug (or make the improvements), fork the repository and work in your own branch. When you are done, push the branch back to this repository and set up a pull request. Automated unit tests are run on all pull requests. Any new code should have unit test coverage, documentation (if necessary), and should conform to the Python PEP8 style guidelines.
3. After some back and forth between you and core committers (or individuals who have privileges to commit to the base branch of this repository), your code will probably be merged, perhaps with some minor changes.

This repository contains a configuration file for git [pre-commit](https://pre-commit.com/) hooks which help ensure that code is linted before it is checked into version control. It is strongly recommended that you install these hooks locally by installing pre-commit and running `pre-commit install`.

## Tests

New code should have unit tests. Tests can be run using [tox](https://tox.readthedocs.io/).
