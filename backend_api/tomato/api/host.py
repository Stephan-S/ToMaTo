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

#fixme: all.

from api_helpers import checkauth, getCurrentUserInfo
from ..lib.cache import cached, invalidates
from ..lib.service import get_backend_users_proxy
from ..lib.remote_info import get_host_info, get_site_info

@cached(timeout=6*3600, autoupdate=True)
def organization_list():
	"""
	undocumented
	"""
	api = get_backend_users_proxy()
	return api.organization_list()

@invalidates(organization_list)
def organization_create(name, label="", attrs={}):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_create_organizations()
	api = get_backend_users_proxy()
	return api.organization_create(name, label, attrs)

def organization_info(name):
	"""
	undocumented
	"""
	api = get_backend_users_proxy()
	return api.organization_info(name)

@invalidates(organization_list)
def organization_modify(name, attrs):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_modify_organization(name)
	api = get_backend_users_proxy()
	return api.organization_modify(name, attrs)

@invalidates(organization_list)
def organization_remove(name):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_delete_organization(name)
	api = get_backend_users_proxy()
	api.organization_remove(name)

@checkauth
def organization_usage(name): #@ReservedAssignment
	#fixme: broken
	orga = _getOrganization(name)
	return orga.totalUsage.info()	

@cached(timeout=6*3600, autoupdate=True)
def site_list(organization=None):
	"""
	undocumented
	"""
	if organization:
		sites = Site.objects(organization=organization)
	else:
		sites = Site.objects.all()
	return [s.info() for s in sites]

@invalidates(site_list)
def site_create(name, organization, label="", attrs={}):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_create_sites(organization)
	s = Site.create(name, organization, label, attrs)
	return s.info()

def site_info(name):
	"""
	undocumented
	"""
	site = _getSite(name)
	return site.info()

@invalidates(site_list)
def site_modify(name, attrs):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_modify_site(get_site_info(name))
	site = _getSite(name)
	site.modify(attrs)
	return site.info()

@invalidates(site_list)
def site_remove(name):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_delete_site(get_site_info(name))
	site = _getSite(name)
	site.remove()

@cached(timeout=300, maxSize=1000, autoupdate=True)
def host_list(site=None, organization=None):
	"""
	undocumented
	"""
	if site:
		site = Site.get(site)
		hosts = Host.objects(site=site)
	elif organization:
		sites = Site.objects(organization=organization)
		hosts = Host.objects(site__in=sites)
	else:
		hosts = Host.objects
	return [h.info() for h in hosts]

@invalidates(host_list)
def host_create(name, site, attrs=None):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_create_hosts(get_site_info(site))
	if not attrs: attrs = {}
	site = _getSite(site)
	h = Host.create(name, site, attrs)
	return h.info()

@checkauth
def host_info(name):
	"""
	undocumented
	"""
	h = _getHost(name)
	return h.info()

@invalidates(host_list)
def host_modify(name, attrs):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_modify_host(get_host_info(name))
	h = _getHost(name)
	h.modify(attrs)
	return h.info()

@invalidates(host_list)
def host_remove(name):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_delete_host(get_host_info(name))
	h = _getHost(name)
	h.remove()

@checkauth
def host_users(name):
	"""
	undocumented
	"""
	getCurrentUserInfo().check_may_delete_host(get_host_info(name))
	h = _getHost(name)
	return h.getUsers()

@checkauth
def host_usage(name): #@ReservedAssignment
	h = _getHost(name)
	return h.totalUsage.info()

