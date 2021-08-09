# taaraxtak

![python-workflow](https://github.com/elsehow/taaraxtak/actions/workflows/python-workflow.yml/badge.svg)


taaraxtak is a platform for collecting, storing, and visualizing data about
political dimensions of the Internet. See [some context on its
motivation](https://nickmerrill.substack.com/p/the-story-so-far).

See a live version at XXX


# Install

See [INSTALL.md](INSTALL.md)

# Run

For local development, start the collection server with

```
python3 collect.py
```

Then check out your Grafana instance (by default, https://localhost:3000).

To deploy a production environment, see [DEPLOY.md](DEPLOY.md)

# Testing

Tests will require `pytest`:

```
pip install pytest
```

Run tests with 

```
pytest test/*
```

Optionally, you can run tests with code coverage:

```
pip install pytest
pip install pytest-cov
pytest test/* --cov=src

```

# Contributing

See [CONTRIBUTING.MD](CONTRIBUTING.md).

# About the name

taaraxtak (IPA: taːɾaxtak) means "the sky" in the [Chochenyo
Ohlone](https://sogoreate-landtrust.org/lisjan-history-and-territory/) language.

Looking up at the sky, I can only see what's above me. Similarly, the Internet
is something I can only know partially. The name is meant to remind us to look
at what we *can* see, knowing it's only part of the whole.
(When we measure the Internet we are, in more
senses than one, looking at the shape of clouds). Remember, everything we
learned about the atmosphere started by looking up at the sky. All we ever
need is a partial perspective and an open system of thought.

# License

BSD 2-Clause
