# OONI globe visualization 


This visualization shows network interference globally from 26 May 2021 (16:33
UTC) to 1 June 2021 (21:48 UTC).

Click on a country to see whose websites it blocks (outgoing) and who blocks its
websites (incoming).

This data comes from OONI (Open Observatory of Network Interference). This
dataset, constantly updated by volunteers around the world, has people testing
specific URLs (inputs) and recording the responses they get back. Through these
responses, OONI detects whether there was network interference along the path
(most typically, website blocking by nation-states).

We collect both "confirmed" blocking events and "anomalous" events. For each
event, we label where the observation was made, and where the website came from.
(A single website can be based in multiple places; [see methodological
details](src/w3techs/README.md) coming). With this data, we make directed pairs;
for example, RU->US would capture that Russia interfered with a US-based
website. (One way to think about this relationship: the government of X
disapproves of behavior that's condoned in Y). From those pairs, we can detect
the direction and velocity of network interference worldwide.

## Notes
- Chinese blocking tends to show up as "anomalous" rather than "confirmed."
  Click on China then check "All (anomalies)."
- Outbound stuff from the US is almost certainly not the result of US government
  action. They are almost certainly corporate firewalls or ISPs. In general, we
  cannot assign blame to governments here, though in cases like China, Russia,
  and Iran that is typically the case. I think this visualization is a good
  thing to show funders - a reasonable proposal for funding would be to make
  this visualization update in real-time
- Code to produce this visualization's data is in `src/ooni/visualizations.ipynb`.

## Credits

This visualization is powered by [GioJS](https://github.com/syt123450/giojs).
