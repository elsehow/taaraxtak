# W3Techs data

We collect data from [W3Techs](https://w3techs.com/) to understand the
centralization of core Internet services among particular providers and
jurisdictions. Our primary tool is the Gini coefficient. 

[See this blogpost for
context](https://nickmerrill.substack.com/p/measuring-internet-decentralization)
on our motivation and the Gini coefficient.

# Scraping W3Techs data

`collect.py` scrapes published data on technology usage from `w3techs.com`.
These data are typically updated daily. We label the jurisdiction for each
service provider using `analysis/providers_labeled.csv`. `types.py` defines the
Postgres tables for these data.

# Computing gini coefficients

## Included markets

The markets we include in our Gini metric are (listed here by their W3Techs names): 

```
'data-centers', 
'web-hosting', 
'dns-server', 
'proxy', 
'ssl-certificate',
'server-location', 
'top-level-domain',
```

Explanations of each, and rationale for including them, are as follows:

### 1. Data centers
 Data center providers supply hardware and software infrastructure to serve
 websites on the internet.

 If data centers were overly centralized, providers could effectively take down
 content. If data centers were overly centralized in particular jurisdictions,
 jurisdictions could take down that content by legal decree.

### 2. Web hosts
A web hosting service provides hardware and software infrastructure to enable
webmasters to make their website accessible via the internet. Web hosts are
distinct from data centers: for example, for WordPress sites, WP Engine is a
hosting provider, because customers buy hosting services from them. However, WP
Engine uses Google to run its physical servers. Therefore Google, is the data
center provider and WP Engine is the web host.

If web hosting were overly centralized, providers or jurisdictions could make
content inaccessible.

### 3. DNS servers
DNS (domain name system) servers manage internet domain names and their
associated records such as IP addresses.

If DNS servers were overly centralized, providers or jurisdictions could make
content inaccessible by severing users' path to that content.

### 4. Reverse proxies
A reverse proxy service is an intermediary for a website which handles requests
from web clients on behalf of the website's server. Common uses for reverse
proxies are content delivery networks (CDNs, typically located in different
geographical regions) and DDoS (distributed denial of service) protection
services.

If reverse proxies were overly centralized, providers could make content
inaccessible by refusing to serve key content.

### 5. Certificate authorities
SSL certificate authorities are institutions that issue SSL certificates.

If certificate authorities were overly centralized, they could make content more
difficult to access by revoking or denying TLS certificates.

### 5. Server locations

Servers must be positioned in the world. We assume countries have jurisdiction
over the servers located in their countries (meaning those countires can
"legitimately" (by Weber's definition) seize those servers or cut Internet
access to them).

If server locations were overly centralized, particular jurisdictions could make content impossible to access by seizing or blocking access to servers in their jurisdiction.

### 5. Top-level domain

The Domain Name System supports top-level domains (e.g., .com, .net, .ar). Those top-level domains are amdinistered by registrars with clear national jurisdiction.

If top-level domains were overly centralized, particular jurisdictions could
block access to content by compelling certificate authorities to drop or reroute
DNS requests.

## Collecting data for Gini

A Gini is computed for each market. When computing a Gini coefficient, we pass
in the current time `date`, and get everything between timestamp '{date}' -
interval '12 hour' AND '{date}'.

## Weighting Gini

Finally, we weight each country's marketshare by its proportion of global
Internet users (`marketshare / proportion of Internet users`). In other words,
if everyone's proportion of core Internet services were equal to their
proportion of the global population of Internet users, the Gini coefficient
would be 1. 


An example of where this matters: Indonesia and Russia have a comprable share of
the world's Internet users: 3.2% vs 3.1% (as of April 21, 2021). But Indonesia
has jurisdiction over only 0.1% of the world's core Internet services, whereas
Russia has 0.5%. So Indonesia's weighted value ends up being 0.030380 vs
Russia's 1.643119, reflecting the population-weighted disparity in service
provision.

We generate data on the proportion of world's Internet users using WorldBank
data. See `analysis/generate_proportion_net_users.py`. The generated file we use
for weighting is `analysis/prop_net_users.csv`.

# Backfilling historical data

W3Techs provides monthly data paying subscribers. Relative to the data we scrape
from the webpage, that data lists slightly more providers, but does not change
at the day-to-day level (it only shows data for the first of each month). And,
relative to the monthly data, the data we scrape does not describe specific
marketshare numbers for providers with less than 0.1% of the marketshare, where
monthly data does include those providers.

In our production database, we separately add those monthly values in. 
The effect is that certain providers with less than 0.1% marketshare are encoded
more sparsely in the data.

The code for adding in monthly data is in `historical-data.ipynb`. We may
backfill monthly data in the future as it becomes available.

*NOTE* - when backfilling data, beware of existing datapoints that have exactly
the same time. It *could* be prudent not to write the tiemstamp as midnight
exactly---or, to drop those data (carefully!) if overwriting them.
