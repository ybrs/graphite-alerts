Graphite Pager
==============

Graphite Pager is a small application to send PagerDuty alerts based on
Graphite metrics. This makes it easy to be paged about what's happening in
your system.

You shouldn't uses this yet, I'm still playing with it.

It can be deployed to Heroku (make sure you use SSL!)


## Background

Graphite is a great tool for recording metrics but it isn't easy to get paged
when a metric passes a certain threshold.

Graphite-Pager is an easy to use alerting tool for Graphite that will send
Pager Duty alerts if a metric reaches a warning or critical level.


## Requirements

* PagerDury account
* Graphite

## Installation

At the moment the easiest way to install Graphite-Pager is with Heroku! See
the example at
https://github.com/philipcristiano/graphite-pager-heroku-example.

1. Install the package with Pip

`pip install -e git://github.com/philipcristiano/graphite-pager.git#egg=graphitepager`

2.  Set Environment variables
```
    GRAPHITE_USER=HTTP-basic username
    GRAPHITE_PASS=HTTP-basic password
    GRAPHITE_URL=HTTPS(hopefully) URL to your Graphite installation
    PAGERDUTY_KEY=Specific PagerDuty application key
```
3. Set up alerts in the `alerts.yml` file

4. Run `graphite-pager`

## TODO

* Create a package
* Customize time to query
* Alerts with URLs to a graph
* Add Hipchat support / make it easy to add new notifiers
