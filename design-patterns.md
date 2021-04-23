# Design patterns

## All validation happens in types

This project relies heavily on scraping the web. Sometimes we scrape
undocumented APIs, sometimes we scrape HTML pages. Needless to say, anything can
happen. As a result, we have to be specific and consistent with where and how we
provide validation.

In this project, we validate all data through types - custom Python classes.
Each data source has a `types.py` file that define (and validate!) the type. If something passes this type validator, we assume it's trusted.

Make [an API key](https://grafana.com/docs/grafana/latest/http_api/auth/)
