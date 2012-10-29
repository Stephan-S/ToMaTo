# -*- coding: utf-8 -*-
# ToMaTo (Topology management software) 
# Copyright (C) 2010 Dennis Schwerdel, University of Kaiserslautern
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from django.db import models
from . import config, currentUser
from accounting import UsageStatistics
from lib import attributes, db, rpc, util, logging #@UnresolvedImport
from auth import Flags
import xmlrpclib, time

class Site(attributes.Mixin, models.Model):
    name = models.CharField(max_length=10, unique=True)
    #hosts: [Host]
    attrs = db.JSONField()
    description = attributes.attribute("description", str, "")
    location = attributes.attribute("location", str, "")
    
    class Meta:
        pass

    def init(self, attrs):
        self.modify(attrs)

    def modify(self, attrs):
        fault.check(currentUser().hasFlag(Flags.HostsManager), "Not enough permissions")
        logging.logMessage("modify", category="site", name=self.name, attrs=attrs)
        for key, value in attrs.iteritems():
            if key == "description":
                self.description = value
            elif key == "location":
                self.location = value
            else:
                fault.raise_("Unknown site attribute: %s" % key, fault.USER_ERROR)
        self.save()

    def remove(self):
        fault.check(currentUser().hasFlag(Flags.HostsManager), "Not enough permissions")
        fault.check(not self.hosts.all(), "Site still has hosts")
        logging.logMessage("remove", category="site", name=self.name)
        self.delete()

    def info(self):
        return {
            "name": self.name,
            "description": self.description,
            "location": self.location
        }

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Site(%s)" % self.name


def getSite(name, **kwargs):
    try:
        return Site.objects.get(name=name, **kwargs)
    except Site.DoesNotExist:
        return None

def getAllSites(**kwargs):
    return list(Site.objects.filter(**kwargs))
    
def createSite(name, description=""):
    fault.check(currentUser().hasFlag(Flags.HostsManager), "Not enough permissions")
    logging.logMessage("create", category="site", name=name, description=description)        
    site = Site(name=name)
    site.save()
    site.init({"description": description})
    return site

def _connect(address, port):
    transport = rpc.SafeTransportWithCerts(config.CERTIFICATE, config.CERTIFICATE)
    return rpc.ServerProxy('https://%s:%d' % (address, port), allow_none=True, transport=transport)


class Host(attributes.Mixin, models.Model):
    address = models.CharField(max_length=255, unique=True)
    site = models.ForeignKey(Site, null=False, related_name="hosts")
    attrs = db.JSONField()
    port = attributes.attribute("port", int, 8000)
    elementTypes = attributes.attribute("element_types", dict, {})
    connectionTypes = attributes.attribute("connection_types", dict, {})
    hostInfo = attributes.attribute("info", dict, {})
    hostInfoTimestamp = attributes.attribute("info_timestamp", float, 0.0)
    accountingTimestamp = attributes.attribute("accounting_timestamp", float, 0.0)
    lastResourcesSync = attributes.attribute("last_resources_sync", float, 0.0)
    enabled = attributes.attribute("enabled", bool, True)
    componentErrors = attributes.attribute("componentErrors", int, 0)
    # connections: [HostConnection]
    # elements: [HostElement]
    
    class Meta:
        ordering = ['site', 'address']

    def init(self, attrs={}):
        self.attrs = {}
        self.modify(attrs)
        self.update()

    def _saveAttributes(self):
        pass #disable automatic attribute saving

    def getProxy(self):
        if not hasattr(self, "_proxy"):
            self._proxy = _connect(self.address, self.port)
        return self._proxy
        
    def incrementErrors(self):
        # count all component errors {element|connection}_{create|action|modify}
        # this value is reset on every sync
        self.componentErrors +=1
        self.save()
        
    def update(self):
        before = time.time()
        self.hostInfo = self._info()
        after = time.time()
        self.hostInfoTimestamp = (before+after)/2.0
        self.hostInfo["query_time"] = after - before
        self.hostInfo["time_diff"] = self.hostInfo["time"] - self.hostInfoTimestamp
        caps = self._capabilities()
        self.elementTypes = caps["elements"]
        self.connectionTypes = caps["connections"]
        self.componentErrors = 0
        self.save()
        logging.logMessage("info", category="host", address=self.address, info=self.hostInfo)        
        logging.logMessage("capabilities", category="host", address=self.address, capabilities=caps)        
        
    def _capabilities(self):
        return self.getProxy().host_capabilities()
        
    def _info(self):
        return self.getProxy().host_info()
        
    def getElementCapabilities(self, type_):
        return self.elementTypes.get(type_)
        
    def getConnectionCapabilities(self, type_):
        return self.connectionTypes.get(type_)

    def createElement(self, type_, parent=None, attrs={}, owner=None):
        assert not parent or parent.host == self
        try:
            el = self.getProxy().element_create(type_, parent.num if parent else None, attrs)
        except:
            self.incrementErrors()
            raise
        hel = HostElement(host=self, num=el["id"])
        hel.usageStatistics = UsageStatistics.objects.create()
        hel.attrs = el
        hel.save()
        logging.logMessage("element_create", category="host", host=self.address, element=el, owner=(owner.__class__.__name__.lower(), owner.id) if owner else None)        
        return hel

    def getElement(self, num):
        return self.elements.get(num=num)

    def createConnection(self, hel1, hel2, type_=None, attrs={}, owner=None):
        assert hel1.host == self
        assert hel2.host == self
        try:
            con = self.getProxy().connection_create(hel1.num, hel2.num, type_, attrs)
        except:
            self.incrementErrors()
            raise
        hcon = HostConnection(host=self, num=con["id"])
        hcon.usageStatistics = UsageStatistics.objects.create()
        hcon.attrs = con
        hcon.save()
        logging.logMessage("connection_create", category="host", host=self.address, element=con, owner=(owner.__class__.__name__.lower(), owner.id) if owner else None)        
        return hcon

    def getConnection(self, num):
        return self.connections.get(num=num)

    def grantUrl(self, grant, action):
        return "http://%s:%d/%s/%s" % (self.address, self.hostInfo["fileserver_port"], grant, action)
    
    def synchronizeResources(self):
        if time.time() - self.lastResourcesSync < config.RESOURCES_SYNC_INTERVAL:
            return
        logging.logMessage("resource_sync begin", category="host", address=self.address)        
        #TODO: implement for other resources
        from . import resources
        hostNets = {}
        for net in self.getProxy().resource_list("network"):
            hostNets[(net["attrs"]["kind"], net["attrs"]["bridge"])] = net
        for net in self.networks.all():
            key = (net.getKind(), net.bridge)
            attrs = net.attrs.copy()
            attrs["bridge"] = net.bridge
            attrs["kind"] = net.getKind()
            attrs["preference"] = net.network.preference
            if not key in hostNets:
                #create resource
                self.getProxy().resource_create("network", attrs)
                logging.logMessage("network create", category="host", address=self.address, network=attrs)        
            else:
                hNet = hostNets[key]
                if hNet["attrs"] != attrs:
                    #update resource
                    self.getProxy().resource_modify(hNet["id"], attrs)
                    logging.logMessage("network update", category="host", address=self.address, network=attrs)                
        hostTpls = {}
        for tpl in self.getProxy().resource_list("template"):
            hostTpls[(tpl["attrs"]["tech"], tpl["attrs"]["name"])] = tpl
        for tpl in resources.getAll(type="template"):
            key = (tpl.tech, tpl.name)
            attrs = tpl.attrs.copy()
            attrs["name"] = tpl.name
            attrs["tech"] = tpl.tech
            if not key in hostTpls:
                #create resource
                self.getProxy().resource_create("template", attrs)
                logging.logMessage("template create", category="host", address=self.address, template=attrs)        
            else:
                hTpl = hostTpls[key]
                if hTpl["attrs"] != tpl.info()["attrs"]:
                    #update resource
                    if hTpl["attrs"]["torrent_data_hash"] == tpl.info()["attrs"]["torrent_data_hash"]:
                        #only send torrent data when needed
                        del attrs["torrent_data"]
                    self.getProxy().resource_modify(hTpl["id"], attrs)
                    logging.logMessage("template update", category="host", address=self.address, template=attrs)        
        logging.logMessage("resource_sync end", category="host", address=self.address)        
        self.lastResourcesSync = time.time()
        self.save()

    def updateAccountingData(self, now):
        logging.logMessage("accounting_sync begin", category="host", address=self.address)        
        data = self.getProxy().accounting_statistics(type="5minutes", after=self.accountingTimestamp-900)
        for el in self.elements.all():
            if not el.usageStatistics:
                el.usageStatistics = UsageStatistics.objects.create()
                el.save()
            if not str(el.num) in data["elements"]:
                print "Missing accounting data for element #%d on host %s" % (el.num, self.address)
                el.checkMissing()
                continue
            logging.logMessage("host_records", category="accounting", host=self.address, records=data["elements"][str(el.num)], object=("element", el.id))        
            el.updateAccountingData(data["elements"][str(el.num)])
        for con in self.connections.all():
            if not con.usageStatistics:
                con.usageStatistics = UsageStatistics.objects.create()
                con.save()
            if not str(con.num) in data["connections"]:
                print "Missing accounting data for connection #%d on host %s" % (con.num, self.address)
                con.checkMissing()
                continue
            logging.logMessage("host_records", category="accounting", host=self.address, records=data["connections"][str(con.num)], object=("connection", con.id))        
            con.updateAccountingData(data["connections"][str(con.num)])
        self.accountingTimestamp=now
        self.save()
        logging.logMessage("accounting_sync end", category="host", address=self.address)        
    
    def getNetworkKinds(self):
        return [net.getKind() for net in self.networks.all()]
    
    def remove(self):
        fault.check(currentUser().hasFlag(Flags.HostsManager), "Not enough permissions")
        fault.check(not self.elements.all(), "Host still has active elements")
        fault.check(not self.connections.all(), "Host still has active connections")
        logging.logMessage("remove", category="host", name=self.address)
        self.delete()

    def modify(self, attrs):
        fault.check(currentUser().hasFlag(Flags.HostsManager), "Not enough permissions")
        logging.logMessage("modify", category="host", name=self.address, attrs=attrs)
        for key, value in attrs.iteritems():
            if key == "site":
                self.site = getSite(value)
            elif key == "enabled":
                self.enabled = value
            else:
                fault.raise_("Unknown host attribute: %s" % key, fault.USER_ERROR)
        self.save()

    def problems(self):
        problems = []
        if not self.enabled:
            problems.append("Manually disabled")
        hi = self.hostInfo
        if time.time() - self.hostInfoTimestamp > 3 * config.HOST_UPDATE_INTERVAL:
            problems.append("Old info age, host unreachable?")
        if not hi:
            problems.append("Node info is missing")
            return problems
        if hi["uptime"] < 10 * 60:
            problems.append("Node just booted")
        if hi["time_diff"] > 5 * 60:
            problems.append("Node clock is out of sync")             
        if hi["query_time"] > 0.5:
            problems.append("Last query took very long")             
        res = hi["resources"]
        cpus = res["cpus_present"]
        if not cpus["count"]:
            problems.append("No CPUS ?!?")
        if cpus["bogomips_avg"] < 1000:
            problems.append("Slow CPUs")
        if res["loadavg"][1] > cpus["count"]:
            problems.append("High load")
        disks = res["diskspace"]
        if int(disks["root"]["total"]) - int(disks["root"]["used"]) < 1e6:
            problems.append("Root disk full") 
        if int(disks["data"]["total"]) - int(disks["data"]["used"]) < 10e6:
            problems.append("Data disk full") 
        if int(res["memory"]["total"]) - int(res["memory"]["used"]) < 1e6:
            problems.append("Memory full") 
        if self.componentErrors > 2:
            problems.append("Multiple component errors")
        return problems
        
    def getLoad(self):
        """
        Returns the host load on a scale from 0 (no load) to 1.0 (fully loaded)
        """
        hi = self.hostInfo
        if not hi:
            return -1
        res = hi["resources"]; cpus = res["cpus_present"]; disks = res["diskspace"]
        load = []
        load.append(res["loadavg"][1] / cpus["count"])
        load.append(float(res["memory"]["used"]) / int(res["memory"]["total"]))
        load.append(float(disks["data"]["used"]) / int(disks["data"]["total"]))
        return min(max(load), 1.0)
        
    def info(self):
        return {
            "address": self.address,
            "site": self.site.name,
            "enabled": self.enabled,
            "problems": self.problems(),
            "load": self.getLoad(),
            "element_types": self.elementTypes.keys(),
            "connection_types": self.connectionTypes.keys(),
            "host_info": self.hostInfo.copy() if self.hostInfo else None,
            "host_info_timestamp": self.hostInfoTimestamp,
        }
        
    def __str__(self):
        return self.address

    def __repr__(self):
        return "Host(%s)" % self.address

class HostElement(attributes.Mixin, models.Model):
    host = models.ForeignKey(Host, null=False, related_name="elements")
    num = models.IntegerField(null=False) #not id, since this is reserved
    usageStatistics = models.OneToOneField(UsageStatistics, null=True, related_name='+')
    attrs = db.JSONField()
    connection = attributes.attribute("connection", int)
    state = attributes.attribute("state", str)
    type = attributes.attribute("type", str) #@ReservedAssignment
        
    class Meta:
        unique_together = (("host", "num"),)

    def createChild(self, type_, attrs={}, owner=None):
        return self.host.createElement(type_, self, attrs, owner=owner)

    def connectWith(self, hel, type_=None, attrs={}, owner=None):
        return self.host.createConnection(self, hel, type_, attrs, owner=owner)

    def modify(self, attrs):
        logging.logMessage("element_modify", category="host", host=self.host.address, id=self.num, attrs=attrs)
        try:        
            self.attrs = self.host.getProxy().element_modify(self.num, attrs)
        except:
            self.host.incrementErrors()
            raise
        logging.logMessage("element_info", category="host", host=self.host.address, id=self.num, info=self.attrs)        
        self.save()
            
    def action(self, action, params={}):
        logging.logMessage("element_action begin", category="host", host=self.host.address, id=self.num, action=action, params=params)        
        try:
            res = self.host.getProxy().element_action(self.num, action, params)
        except:
            self.host.incrementErrors()
            raise
        logging.logMessage("element_action end", category="host", host=self.host.address, id=self.num, action=action, params=params, result=res)        
        self.updateInfo()
        return res
            
    def remove(self):
        try:
            logging.logMessage("element_remove", category="host", host=self.host.address, id=self.num)        
            self.host.getProxy().element_remove(self.num)
        except xmlrpclib.Fault, f:
            if f.faultCode != fault.UNKNOWN_OBJECT:
                raise
        self.usageStatistics.delete()
        self.delete()

    def getConnection(self):
        return self.host.getConnection(self.connection) if self.connection else None

    def updateInfo(self):
        try:
            self.attrs = self.host.getProxy().element_info(self.num)
        except:
            self.host.incrementErrors()
            raise
        logging.logMessage("element_info", category="host", host=self.host.address, id=self.num, info=self.attrs)        
        self.save()
        
    def checkMissing(self):
        els = self.host.getProxy().element_list()
        for el in els:
            if el["id"] == self.num:
                return
        logging.logMessage("missing_element", category="host", host=self.host.address, id=self.num, info=self.attrs)
        self.delete() 

    def info(self):
        return self.attrs

    def getAttrs(self):
        return self.attrs["attrs"]

    def getAllowedActions(self):
        caps = self.host.getElementCapabilities(self.type)["actions"]
        res = []
        for key, states in caps.iteritems():
            if self.state in states:
                res.append(key)
        return res

    def getAllowedAttributes(self):
        caps = self.host.getElementCapabilities(self.type)["attrs"]
        ret = dict(filter(lambda attr: not "states" in attr[1] or self.state in attr[1]["states"], caps.iteritems()))
        return ret
    
    def updateAccountingData(self, data):
        self.usageStatistics.importRecords(data)
        self.usageStatistics.removeOld()
        
    def getOwner(self):
        from . import elements, connections
        for el in elements.getAll():
            if self in el.getHostElements():
                return ("element", el.id)
        for con in connections.getAll():
            if self in el.getHostElements():
                return ("connection", con.id)
        return (None, None)

        
class HostConnection(attributes.Mixin, models.Model):
    host = models.ForeignKey(Host, null=False, related_name="connections")
    num = models.IntegerField(null=False) #not id, since this is reserved
    usageStatistics = models.OneToOneField(UsageStatistics, null=True, related_name='+')
    attrs = db.JSONField()
    elements = attributes.attribute("elements", list)
    state = attributes.attribute("state", str)
    type = attributes.attribute("type", str) #@ReservedAssignment
    
    class Meta:
        unique_together = (("host", "num"),)

    def modify(self, attrs):
        logging.logMessage("connection_modify", category="host", host=self.host.address, id=self.num, attrs=attrs)
        try:        
            self.attrs = self.host.getProxy().connection_modify(self.num, attrs)
        except:
            self.host.incrementErrors()
            raise
        logging.logMessage("connection_info", category="host", host=self.host.address, id=self.num, info=self.attrs)        
        self.save()
            
    def action(self, action, params={}):
        logging.logMessage("connection_action begin", category="host", host=self.host.address, id=self.num, action=action, params=params)
        try:        
            res = self.host.getProxy().connection_action(self.num, action, params)
        except:
            self.host.incrementErrors()
            raise
        logging.logMessage("connection_action begin", category="host", host=self.host.address, id=self.num, action=action, params=params, result=res)        
        self.updateInfo()
        return res
            
    def remove(self):
        try:
            logging.logMessage("connection_remove", category="host", host=self.host.address, id=self.num)        
            self.host.getProxy().connection_remove(self.num)
        except xmlrpclib.Fault, f:
            if f.faultCode != fault.UNKNOWN_OBJECT:
                raise
        self.usageStatistics.delete()
        self.delete()
        
    def getElements(self):
        return [self.host.getElement(el) for el in self.elements]

    def updateInfo(self):
        try:
            self.attrs = self.host.getProxy().connection_info(self.num)
        except:
            self.host.incrementErrors()
            raise
        logging.logMessage("connection_info", category="host", host=self.host.address, id=self.num, info=self.attrs)        
        self.save()
        
    def checkMissing(self):
        cons = self.host.getProxy().connections_list()
        for con in cons:
            if con["id"] == self.num:
                return
        logging.logMessage("missing_connection", category="host", host=self.host.address, id=self.num, info=self.attrs)
        self.delete() 

    def info(self):
        return self.attrs
    
    def getAttrs(self):
        return self.attrs["attrs"]
  
    def getAllowedActions(self):
        caps = self.host.getConnectionCapabilities(self.type)["actions"]
        res = []
        for key, states in caps.iteritems():
            if self.state in states:
                res.append(key)
        return res

    def getAllowedAttributes(self):
        caps = self.host.getConnectionCapabilities(self.type)["attrs"]
        return dict(filter(lambda attr: not "states" in attr[1] or self.state in attr[1]["states"], caps.iteritems()))
  
    def updateAccountingData(self, data):
        self.usageStatistics.importRecords(data)
        self.usageStatistics.removeOld()

    def getOwner(self):
        from . import elements, connections
        for el in elements.getAll():
            if self in el.getHostConnections():
                return ("element", el.id)
        for con in connections.getAll():
            if self in el.getHostConnections():
                return ("connection", con.id)
        return (None, None)


def get(**kwargs):
    try:
        return Host.objects.get(**kwargs)
    except Host.DoesNotExist:
        return None

def getAll(**kwargs):
    return list(Host.objects.filter(**kwargs))
    
def create(address, site, attrs={}):
    fault.check(currentUser().hasFlag(Flags.HostsManager), "Not enough permissions")
    host = Host(address=address, site=site)
    host.init(attrs)
    host.save()
    logging.logMessage("create", category="host", info=host.info())        
    return host

def select(site=None, elementTypes=[], connectionTypes=[], networkKinds=[], hostPrefs={}, sitePrefs={}):
    #STEP 1: limit host choices to what is possible
    all_ = getAll(site=site) if site else getAll()
    hosts = []
    for host in all_:
        if host.problems():
            continue
        if set(elementTypes) - set(host.elementTypes.keys()):
            continue
        if set(connectionTypes) - set(host.connectionTypes.keys()):
            continue
        if set(networkKinds) - set(host.getNetworkKinds()):
            continue #FIXME: allow general networks
        hosts.append(host)
    # any host in hosts can handle the request
    prefs = dict([(h, 0.0) for h in hosts])
    #STEP 2: calculate preferences based on host load
    els = 0.0
    cons = 0.0
    for h in hosts:
        prefs[h] -= h.componentErrors * 25 #discourage hosts with previous errors
        prefs[h] -= h.getLoad() * 100 #up to -100 points for load
        els += h.elements.count()
        cons += h.connections.count()
    avgEls = els/len(hosts)
    avgCons = cons/len(hosts)
    for h in hosts:
        #between -30 and +30 points for element/connection over-/under-population
        prefs[h] -= max(-20.0, min(10.0*(h.elements.count() - avgEls)/avgEls, 20.0))
        prefs[h] -= max(-10.0, min(10.0*(h.connections.count() - avgCons)/avgCons, 10.0))
    #STEP 3: calculate preferences based on host location
    for h in hosts:
        if h in hostPrefs:
            prefs[h] += hostPrefs[h]
        if h.site in sitePrefs:
            prefs[h] += sitePrefs[h.site]
    #STEP 4: select the best host
    hosts.sort(key=lambda h: prefs[h], reverse=True)
    logging.logMessage("select", category="host", result=hosts[0].address, 
            prefs=dict([(k.address, v) for k, v in prefs.iteritems()]), 
            site=site, element_types=elementTypes, connection_types=connectionTypes, network_types=networkKinds,
            host_prefs=dict([(k.address, v) for k, v in hostPrefs.iteritems()]),
            site_prefs=dict([(k.name, v) for k, v in sitePrefs.iteritems()]))
    return hosts[0]

def getElementTypes():
    types = set()
    for h in getAll():
        types += set(h.elementTypes.keys())
    return types

def getElementCapabilities(type_):
    #FIXME: merge capabilities
    caps = {}
    for h in getAll():
        hcaps = h.getElementCapabilities(type_)
        if len(repr(hcaps)) > len(repr(caps)):
            caps = hcaps
    return caps
    
def getConnectionTypes():
    types = set()
    for h in getAll():
        types += set(h.connectionTypes.keys())
    return types

def getConnectionCapabilities(type_):
    #FIXME: merge capabilities
    caps = {}
    for h in getAll():
        hcaps = h.getConnectionCapabilities(type_)
        if len(repr(hcaps)) > len(repr(caps)):
            caps = hcaps
    return caps

@db.commit_after
def synchronize():
    #TODO: implement more than resource sync
    for host in getAll():
        try:
            host.update()
            host.synchronizeResources()
        except:
            logging.logException(host=host.address)
            print "Error updating information from %s" % host

task = util.RepeatedTimer(config.HOST_UPDATE_INTERVAL, synchronize) #every min

from . import fault