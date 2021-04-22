# taaraxtak

taaraxtak is a platform for collecting, storing, and visualizing data about
political dimensions of the Internet. See [some context on its
motivation](https://nickmerrill.substack.com/p/the-story-so-far).

See a live version at XXX

# Install

### Pre-requisites

- Python 3.6 or higher
- Postgres 10 or higher

### First-time setup

1. Install pre-requisites with `pip3 install -r requirements.txt`. 
2. Make sure Postgres is running. Make a database and a user with write access.
3. Copy `config.example.py` to `config.py` and enter your credentials. 
4. Set up the database with `python3 create-tables.py`. 

# Run

Start the collection server with

```
python3 collect.py
```

# Contributing

See [CONTRIBUTING.MD](CONTRIBUTING.md).

# About the name

taaraxtak (IPA: taːɾaxtak) means "the sky" in the [Chochenyo
Ohlone](https://sogoreate-landtrust.org/lisjan-history-and-territory/) language.

Looking up at the sky, I can only see what's above me. Similarly, the Internet
is something I can only know partially; when we measure the Internet we are, in
more senses than one, looking at the shape of clouds. This name is meant to
remind us to look at what we *can* see, acknowledging its partiality, and being
thankful for whatever we can take from it. Remember, everything we learned about
the atmosphere started by looking up at the sky. All we've ever needed is a
partial perspective and an open system of thought.

# License

BSD 2-Clause
