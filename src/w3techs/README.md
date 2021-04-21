# W3Techs data

We collect data from [W3Techs](https://w3techs.com/) to understand the
centralization of core Internet services among particular providers and
jurisdictions. Our primary tool is the Gini coefficient. 

[See this blogpost for
context](https://nickmerrill.substack.com/p/measuring-internet-decentralization),
though mind the particulars may have changed.


## Method

`collect.py` scrapes data on technology usage from `w3techs.com`. We combine
these with some data with some external data sources (like the population of
countries and the jurisdiction of providers), maintained more manually and kept
in `analysis`.

`types.py` defines the Postgres tables for these data.


## Caveats

W3Techs provides monthly data paying subscribers. Relative to the data we scrape
from the webpage, that data lists slightly more providers, but does not change
at the day-to-day level (it only shows data for the first of each month).

Regarding inclusivity of providers, the data we scrape does not describe
specific marketshare numbers for providers with less than 0.1% of the
marketshare, where monthly data does include those providers.

In our production database, we separately add those monthly values in. The
effect is that certain providers with less than 0.1% marketshare are encoded
more sparsely in the data.
