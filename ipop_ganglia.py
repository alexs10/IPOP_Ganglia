#this is how to install ganglia
#http://sourceforge.net/apps/trac/ganglia/wiki/ganglia_quick_start

#this is how I figured out how to get python modules working (you may not need this depending on linux version
#http://sachinsharm.wordpress.com/2013/08/19/setup-and-configure-ganglia-python-modules-on-centosrhel-6-3/

#here are some examples of pythone moduels
#https://github.com/ganglia/gmond_python_modules

import re
import time
import sys
import os
import copy
import json

PARAMS = {}

METRICS = {}

LAST_METRICS = copy.deepcopy(METRICS)
METRICS_CACHE_MAX = 5

descriptors = []

# Where to get the stats from
net_stats_file = "/home/h2/ipop-14.01.1-x86_ubuntu12/state.json"

def create_desc(skel, prop):
    d = skel.copy()
    for k,v in prop.iteritems():
        d[k] = v
    return d

def metric_init(params):
    global descriptors

#    print INTERFACES
    time_max = 60

    Desc_Skel = {
        'name'        : 'XXX',
        'call_back'   : get_xmpp_time,
        'time_max'    : 60,
        'value_type'  : 'float',
        'format'      : '%.0f',
        'units'       : '/s',
        'slope'       : 'both', # zero|positive|negative|both
        'description' : 'XXX',
        'groups'      : 'IPOP',
        }

    data = []
    with open(net_stats_file, 'r') as inf:
	for line in inf:
	    data = json.loads(line)

    for item in data:
	test = str(data[item]["ip4"])


	#this chunk is needed to find all of the delta values
	METRICS["peer_bytes_recv_"+test] = 0  
	METRICS["peer_bytes_recv_"+test+"_time"] = time.time()
	METRICS["peer_bytes_recv_"+test+"_delta"] = 0
	METRICS["peer_bytes_sent_"+test] = 0
	METRICS["peer_bytes_sent_"+test+"_time"] = time.time()
	METRICS["peer_bytes_sent_"+test+"_delta"] = 0
	for j in data[item]["stats"]:
	    METRICS["peer_bytes_recv_"+test] += j["recv_total_bytes"]
	    METRICS["peer_bytes_sent_"+test] += j["sent_total_bytes"]

	#this is how you add metrics
	descriptors.append(create_desc(Desc_Skel, {
		    "name"        : "peer_bytes_recv_" + test,
		    "units"       : "bytes/sec",
		    "call_back"   : get_recv_total_bytes,
		    "description" : "Total bytes recieved",
		    }))
	descriptors.append(create_desc(Desc_Skel, {
		    "name"        : "peer_bytes_sent_"+ test,
		    "units"       : "bytes/sec",
		    "call_back"   : get_sent_total_bytes,
		    "description" : "Total bytes sent",
		    }))
	descriptors.append(create_desc(Desc_Skel, {
		    "name"        : "peer_rtt_"+ test,
		    "units"       : "jumps",
		    "call_back"   : get_rtt,
		    "description" : "Routing transit time",
		    }))
	descriptors.append(create_desc(Desc_Skel, {
		    "name"        : "peer_xmpp_time_"+ test,
		    "units"       : "seconds",
		    "call_back"   : get_xmpp_time,
		    "description" : "XMPP time",
		    }))
	descriptors.append(create_desc(Desc_Skel, {
		    "name"        : "peer_status_"+ test,
		    "units"       : "On/Off",
		    "call_back"   : get_status,
		    "description" : "On or Off",
		    }))
    
    return descriptors

def metric_cleanup():
    '''Clean up the metric module.'''
    pass
    
def get_xmpp_time(name):

    data = []
    with open(net_stats_file, 'r') as inf:
	for line in inf:
	    data = json.loads(line)

    for item in data:
	if ("peer_xmpp_time_"+ data[item]["ip4"]) == name:
	    return data[item]["xmpp_time"]
    return 0

def get_recv_total_bytes(name):
    global METRICS
    if (time.time() - METRICS[name+"_time"]) > METRICS_CACHE_MAX:

	output = 0
	data = []
	with open(net_stats_file, 'r') as inf:
	    for line in inf:
	        data = json.loads(line)

	for item in data:
	    if ("peer_bytes_recv_"+ data[item]["ip4"]) == name:
	        for j in data[item]["stats"]:
	    	    output = output + j["recv_total_bytes"]

	METRICS[name+"_delta"] = (output - METRICS[name])/(time.time() - METRICS[name+"_time"])
	METRICS[name] = output
	METRICS[name+"_time"] = time.time()
    return METRICS[name+"_delta"]
    
	

def get_sent_total_bytes(name):
    global METRICS
    if (time.time() - METRICS[name+"_time"]) > METRICS_CACHE_MAX:
	output = 0
	data = []
	with open(net_stats_file, 'r') as inf:
	    for line in inf:
	        data = json.loads(line)

	for item in data:
	    if ("peer_bytes_sent_"+ data[item]["ip4"]) == name:
	        for j in data[item]["stats"]:
	    	    output = output + j["sent_total_bytes"]

	METRICS[name+"_delta"] = (output - METRICS[name])/(time.time() - METRICS[name+"_time"])
	METRICS[name] = output
	METRICS[name+"_time"] = time.time()
    return METRICS[name+"_delta"]

def get_rtt(name):
    data = []
    with open(net_stats_file, 'r') as inf:
	for line in inf:
	    data = json.loads(line)

    for item in data:
	if ("peer_rtt_" + data[item]["ip4"]) == name:
            for j in data[item]["stats"]:
	        if j["best_conn"]:
		    return j["rtt"]
    return 0

def get_status(name):

    data = []
    with open(net_stats_file, 'r') as inf:
	for line in inf:
	    data = json.loads(line)

    for item in data:
	if ("peer_status_"+data[item]["ip4"]) == name:
	    if data[item]["status"] == "online":
	    	return 1
    return 0



#for testing only
if __name__ == '__main__':
    
    params = {}
    metric_init(params)
    while True:
	for d in descriptors:
	    v = d['call_back'](d['name'])
	    print ('value for %s is ' + d['format']) % (d['name'], v)
	time.sleep(5)



