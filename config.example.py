import logging

config = {
    "postgres": {
        "user": "scraper",
        "password":  "my-secure-password",
        "host": "127.0.0.1",
        "port": "5432",
        "database": "my-database",
    },
    "tld_cache_dir": "/home/my-user/",
    "logging": {
        "level": logging.DEBUG,
        "handler": "terminal"
    }
}
