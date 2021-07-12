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
        "handler": "terminal",
        "format": "%(asctime)s [%(process)d:%(thread)d] %(levelname)-8s %(name)-30.30s %(message)s",
        "file": "/path/to/log/file"
    }
}
