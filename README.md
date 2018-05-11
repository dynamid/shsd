# SHSD - Self-Hosting Security Dashboard

This tool aims to provide a simple overview of the health of local networked devices. It is tailored to users who can deploy self-hosting solutions such as Yunohost or Sandstorm without requiring expert security knowledge.

In a near future, it will present very simple indicators on local devices which should be useful to detect security breaches.

Some examples of what we aim to detect :

* A device infected with MIRAI
* An account compromised through the compromission of a low-security device such as a smartphone

Some examples of what we explicitely **do not** aim to detect :

* APTs :-)

SHSD typically targets SOHO networks with less than 10 devices and less than 10 accounts.

# Why ?

_Because self-hosting security matters._

Self-hosting is necessary to provide alternatives to GAFAMs. Security of self-hosting is a necessity for self-hosting to compete with GAFAMs. Security of self-hosting cannot be achieved the same way as the security of GAFAMs but, on the other hand, self-hosters may have a better insight on what _should_ happen on their server.

Notably, exists :

* SIEM tools (prelude, ELK, etc.) exhibit security alerts but need dedicated human resources to provide any value ;
* Monitoring tools (Nagios, Grafana, etc.) show functional metrics (free memory, CPU usage) but security is mostly about non-functional activities (for which graphs are close to useless or need huge interpretation).

SHSD must provide value to self-hosters who are not security experts. To achieve this, SHSD leverages specific knowledge and insights a self-hoster may have about his own devices or the few hosted guest accounts.

SHSD does not feature any AI nor precog features.
