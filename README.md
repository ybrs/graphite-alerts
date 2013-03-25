Graphite Alerts
==============

Graphite Alerts is a small application to send PagerDuty alerts based on
Graphite metrics. This makes it easy to be paged about what's happening in
your system.

## Background

Graphite is a great tool for recording metrics but it isn't easy to get paged
when a metric passes a certain threshold.

Graphite-Alerts is an easy to use alerting tool for Graphite that will send
Pager Duty alerts if a metric reaches a warning or critical level.


## Requirements

* Graphite

## Notifiers

Notifiers are what communicate with your preferred alerting service. Currently
PagerDuty, HipChat, Email notifiers exists.

More notifiers are easy to write, file an issue if there is something you would like!

## Installation

At the moment the easiest way to install Graphite-Alerts from git repo directly

1. Install the package with Pip

`pip install -e git://github.com/ybrs/graphite-alerts.git#egg=graphitealerts`

2.  Copy config-sample.yml and change as you like
4. Run `graphite-alerts`

    graphite-alerts --config config.yml

Where the file `config.yml` is in the following format.

# Configuration of Alerts

Configuration of alerts is handled by a YAML file.

### Settings

Currently you at least need to set these, redisurl and graphite_url is mandatory, others are optional 

settings:
    hipchat_key: ''    
    pagerduty_key: ''
    graphite_url: 'http://localhost:8080'
    graphite_auth_user: foo
    graphite_auth_password: bar       
    redisurl: 'redis://localhost:6379'



## Alert Format

Alerts have a simple configuration, you give a target first (the source in graphite), and add some rules 

    Simple Example:
    
        alerts:
            - target: servers.worker-1.system.load.load
              name: system load
              rules:      
                - greater than 5:
                    warning
                - greater than 10:
                    critical 

The first rule that triggers an alert will exit, and won't check the other rules.

You can combine greater and less than in some situations, suppose you have a metric hourly page views 10000,
if it goes over 50k you want to be alerted, but if it is less than 1000 you want alerts too because probably you
might have a problem. 

    Simple Example:
    
        alerts:
            - target: servers.worker-1.system.load.load
              name: system load
              rules:      
                - greater than 5:
                    warning
                - greater than 10:
                    critical 
                - less than 0.1: # probably nothing is working on the server, heads up
                    warning

Optionally you can add a from field, and a method

```
      from: -10min
      check_method: average
```  

from - The Graphite `from` parameter for how long to query for ex. `-10min` default `-1min`
check_method: `latest` or `average` average is default, but sometimes you might want latest,
average will take the average of not None values.

### Alerts based on history

Sometimes you want alerts not hard coded but based on history, suppose you have some servers working on
high load - converting mp4s maybe - and some are just have really low loads - just a chef/salt/puppet master.

If you have a couple of servers, its easy to hard code limits based on servers, but if you have more than a few
it becomes a pain. So here comes the historical alerts.

```
alerts:
    - target: servers.*.system.load.load
      name: system load
      from: -10min           
      check_method: historical
      rules:            
        - greater than historical * 2:
            critical    
        - greater than historical * 1.2:
            warning        
```

This will fetch the historical data, find hourly average on the last 2 days, then will give a warning
if its over 1.2 of the usual load, and issue a critical alert if the load is 2 times then usual.

You can also combine this with hard coded alerts, here is an example:
 
```
alerts:
    - target: servers.*.put.io.system.load.load
      name: system load
      from: -10min           
      check_method: historical             
      rules:            
        - less than 0.01:
            warning        
        - less than 3:        
            nothing                   
        - greater than historical * 2:
            critical    
        - greater than historical * 1.1:
            warning        
```   
  
If the load goes down 0.01 probably you are doing nothing with that server - maybe some services crashed on it ? -

The server might be working under very low load - like the usual load is just 1.0 - so you dont really want to wake
up if it goes over 2.0 - two times the usual load but, its still normal - so you add ``` less than 3: nothing ```

You can modify how historical data is grabbed,

``` 
alerts:
    - target: servers.*.put.io.system.load.load
      name: system load
      from: -10min           
      check_method: historical       
      historical: summarize(target, "1hour", "avg") from -2days      
      rules:            
        - less than 0.1:
            warning        
        - less than 3:        
            nothing                   
        - greater than historical * 2:
            critical    
        - greater than historical * 1.1:
            warning        
```  

The default is taking the hourly average on the last 2 days but, sometimes you might want a longer or shorter period etc.
summarize(target, "1hour", "avg") and -2days are directly sent to graphite, so you can tweak it as much as you like.

In my opinion this adds an endless possibilities on dynamic metrics, like if you want to get alerts based on "daily signups",
you can easily add an alert based on history, so you'll get notified if you are on hacker news, and if it goes really low,
below the usual, you can get alerts and check whats going wrong - maybe there is a bug etc. -


Here is an example

``` 
alerts:      
    - target: summarize(stats_counts.signups, "1hour")    
      name: system load
      from: -1day           
      check_method: historical             
      historical: summarize(target, "1hour", "avg") from -7days      
      rules:            
        - less than 1:
            critical        
        - less than historical / 2:
            critical                               
        - greater than historical * 2:
            critical    
        - greater than historical * 1.5:
            warning        
```  
   
You'll get alerts if it goes lower than half the usual past week, and you'll get alerts if its double than usual,
if you have no signups today, you def. have a bug so you need alerts.

### Ordering of Alerts

Alerts with the same name and target will only be checked once! This is useful
if you want to have a subset of metrics with different check times and/or
values

    Example:

        - name: Load
          target: aliasByNode(servers.worker-*.loadavg01,1)
          rules:      
            - greater than .5:
                warning

        - name: Load
          target: aliasByNode(servers.*.loadavg01,1)
          rules:      
            - greater than 1:
                warning

    Any worker-* nodes will alert for anything 10 or higher but the catch all
    will allow for the remaining metrics to be checked without alerting for
    worker nodes above 5

### Credits

Originally I forked the project from https://github.com/philipcristiano/graphite-pager. 

Changed the rules, removed environment variables, added historical alerts etc. 

