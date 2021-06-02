# OONI data

This data comes from [OONI (Open Observatory of Network
Interference)](https://ooni.org/). This dataset, constantly updated by
volunteers around the world, has people testing specific URLs (inputs) and
recording the responses they get back. Through these responses, OONI detects
whether there was network interference along the path (most typically, website
blocking by nation-states).

We collect both "confirmed" blocking events and "anomalous" events. For each
event, we label where the observation was made, and where the website came from.

A quick philosophical note: we cannot expect the "inputs" in our dataset to map
to exactly one jurisdiction. A company with a workforce in San Francisco may be
legally registered in the Bermuda, delivering the results of a query to a
Russian US-domiciled reverse proxy with a physical server in Germany. Our goal
is to map *what we can observe* of the destination to which that query was
issued. In other words, we are trying to see who (which parties) were *trying*
to provide the result. We are trying to get as many clues as we can about who
was trying to provide the information - by proxy, *in which countries the global
delivery of that content was being condoned*.


With this data, we make directed pairs; for example, RU->US would capture that
Russia interfered with a US-based website. (One way to think about this
relationship: the government of X disapproves of behavior that's condoned in Y).
From those pairs, we can detect the direction and velocity of network
interference worldwide.

To demonstrate these relationships, see [a visualization of network interference
globally]( https://elsehow.github.io/taaraxtak/visualizations/globe/). Click on
a country to see whose websites it blocks (outgoing - red) and who blocks its
websites (incoming - blue).

## Data shape

For now, we collect data from OONI's [web
connectivity](https://ooni.org/nettest/web-connectivity/) tests. We may add
other kinds of tests in the future. We collect all data where `anomaly` is true,
meaning the observation is either anomalous or a confirmed blocking event. (All
confirmed blocking events also have `anomaly=true`).

### `OONIWebConnectivityTest` type

This type is represented by the table `ooni_web_connectivity_test` in the
Postgres database.

- `blocking_type`: Type of blocking event.
  - "blocking": "tcp_ip" | "dns" | "http-diff" | "http-failure" | false | None
      - See [OONI
        docs](https://github.com/ooni/spec/blob/master/nettests/ts-017-web-connectivity.md#semantics-1)
- `probe_alpha2`: The country in which the probe was located, identified by ISO
  3166 code.
- `input_url`: The URL the probe requested.
- `anomaly`: A possible network interference event. (From [OONI
  docs](https://api.ooni.io/apidocs/#/default/get_api_v1_measurements): `True`
  if the measurements "require[s] special attention (it's likely to be a case of
  blocking), however it has not necessarily been confirmed").
- `confirmed=` `True` for "confirmed network anomalies" (From [OONI
  docs](https://api.ooni.io/apidocs/#/default/get_api_v1_measurements): "(we
  found a blockpage, a middlebox was found, the IM app is blocked, etc.)."
- `report_id`: A unique ID for the report.
  - To get the raw measurement, use the [OONI raw_measurement
    API](https://api.ooni.io/apidocs/#/default/get_api_v1_raw_measurement).
    You'll need this `report-id` and `input_url`.
- `input_ip_alpha2`: The country where the input's IP address maps, identified
  by ISO 3166 code.
  - We take the hostname and use `socket.gethostbyname` to find the IP address
    that hostname maps to.
  - We then look up the country where that IP address is located using the
    latest [monthly IP to Country Lite database from
    DB-IP](https://db-ip.com/db/lite.php), a widely-used vendor.
      - TODO Subscribe to the Daily pro databases.
  - NOTE: We can't always find the hostnames. When that happens, we market this
    field as `NULL`. Often, we can't find the IP because the site is
    inaccessible; that inacessibility will sometimes show up as an `anomalous`
    blocking event. If you're concerned about false positives, I lightly
    recommend ignoring all anomalous readings whose `input_ip_alpha2` is NULL,
    as that may indicate the site is simply down.
      
      
- `tld_jurisdiction_alpha2`: The country in which the jurisdiction for the top
  level domain's registry lies, identified by ISO 3166 code.
  - A TLD registry has ultimate censorship control over a website as represented
    by a human-readable name, which is the case for our `input_url`s in general:
    registries can change the website's mapping in the DNS. This has happened
    both domestically (Operation In Our Sites) and abroad.
  - Data about these jurisdictions was collected from
    [icannwiki.org](http://icannwiki.org/). We noted the legal jurisdiction of
    the TLD registrar. That information is stored in the `providers_labeled.csv`
    in this repo.
- `measurement_start_time`: The time at which the probe's measurement was
  started. We use this for querying the data.

## Collection strategy
## Data limitations

### `input_ip_alpha2`

TLDs don't tell us everything about where a website is: a website like bit.ly
has a Libyan domain, but is hosted by a US company. To get additional
information about website locale, we map input URLs to IP addresses, then map
those IP addresses to countries where the IP is located.

There are a few limitations to this approach. First, there may be some
innacuracies in our IP to Country DB.
    - TODO put some boundaries on that accuracy with DB-IP's own data

Second, even when the IP to country mapping is accurate, we have no way to know
if this is the IP address that the query would have resolved to at the time,
from that probe. We can only look up what those IPs would have resolved to for
*us*, in the US. (Remember, it's epistemically impossible to know where the
query would have resolved to if it weren't blocked. If we knew that, the website
wouldn't be blocked!)

When this limitation might matter: our process could return a country where the
content is hosted for me, but not where the content would have been hosted for
the query's issuer. For example, Facebook has different servers in different
countries; in the US, i'd hit a US server, but in RU, i'd hit an Russian server.
Data localization laws sometimes require this, but so do do performance
considerations (e.g., optimizing for low latency) *Usually* the websites are the
same, but sometimes websites can be different in different server locations.
GDPR notice might only launch when a request is from EU. Other times, the
request dictates what TLD you go to. (Fortunately, we capture the *intended* TLD
here in `tld_juris_alpha2`, but that wouldn't account for redirects (e.g.,
amazon.com -> amazon.ca when the request comes from canada) ).

Note: We can see the queries the probe made using the `report_id` on OONI's API,
but we can't rely on those queries. Often, these queries are blocked at the
level of the state-owned autonomous system (AS). Other times, the returned IPs
could be fake, or blockpages.

Note: theoretically, we could get finer-grained to the point of at least cities
on these IPs, but it's unclear if we need to.

### Assigning blame
In general, we cannot assign blame to governments for all network interference.

For example, outbound stuff from the US is almost certainly not the result of US
government action. They are almost certainly corporate firewalls or ISPs. though
in cases like China, Russia, and Iran that is typically the case.
## Observational notes

- Chinese blocking tends to show up as "anomalous" rather than "confirmed."
