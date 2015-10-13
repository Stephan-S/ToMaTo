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

from django import VERSION as DJANGO_VERSION
if DJANGO_VERSION < (1,6):
    from django.conf.urls.defaults import *
else:
    from django.conf.urls import patterns, url, include

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
	(r'^$', 'tomato.main.index'),
	(r'^fonts/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'tomato/fonts'}),
	(r'^img/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'tomato/img'}),
	(r'^js/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'tomato/js'}),
	(r'^style/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'tomato/style'}),
	(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'tomato/static'}),
	(r'^help$', 'tomato.help.help'),
	(r'^help/contact$', 'tomato.help.contact_form'),
	(r'^help/(?P<page>.*)$', 'tomato.help.help'),
	url(r'^login$', 'tomato.main.login'),
	(r'^logout$', 'tomato.main.logout'),
	(r'^account/register$', 'tomato.account.register'),
    (r'^img_ls$', 'tomato.dynimg.ls_img'),
    (r'^key.pem$', 'tomato.main.backend_key'),
	url(r'^account/list$', 'tomato.account.list', {"organization": True}, name="account_list"),
	url(r'^account/list/all$', 'tomato.account.list', {"organization": False}, name="account_list_all"),
	url(r'^account/registrations$', 'tomato.account.list', {"organization": True, "with_flag": "new_account"}, name="account_list_registrations"),
	url(r'^account/registrations/all$', 'tomato.account.list', {"organization": False, "with_flag": "new_account"}, name="account_list_registrations_all"),
	url(r'^organization/(?P<organization>\w+)/accounts$', 'tomato.account.list', name="organization_accounts"),
	(r'^account$', 'tomato.account.info'),
	(r'^account/(?P<id>[^/]+)$', 'tomato.account.info'),
	(r'^account/(?P<id>[^/]+)/accept$', 'tomato.account.accept'),
	(r'^account/(?P<id>[^/]+)/edit$', 'tomato.account.edit'),
	(r'^account/(?P<id>[^/]+)/remove$', 'tomato.account.remove'),
	(r'^account/(?P<id>[^/]+)/reset_password$', 'tomato.account.reset_password'),
	(r'^account/(?P<id>[^/]+)/usage$', 'tomato.usage.account'),
	url(r'^topology$', 'tomato.topology.list', {"show_all": False}, name="topology_list"),
	url(r'^topology/all$', 'tomato.topology.list', {"show_all": True}, name="topology_list_all"),
	url(r'^organization/(?P<organization>\w+)/topologies$', 'tomato.topology.list', {"show_all": True}, name="organization_topologies"),
	(r'^topology/(?P<id>\w{24})$', 'tomato.topology.info'),
	(r'^topology/(?P<id>\w{24})/export$', 'tomato.topology.export'),
	(r'^topology/(?P<id>\w{24})/usage$', 'tomato.usage.topology'),
	(r'^topology/create$', 'tomato.topology.create'),
	(r'^topology/import$', 'tomato.topology.import_'),
	(r'^tutorial$', 'tomato.tutorial.list'),
	(r'^tutorial/start$', 'tomato.tutorial.start'),
	(r'^connection/(?P<id>\w{24})/usage$', 'tomato.usage.connection'),
	(r'^element/(?P<id>\w{24})/usage$', 'tomato.usage.element'),
	(r'^element/(?P<id>\w{24})/rextfv_status$', 'tomato.element.rextfv_status'),
	(r'^element/(?P<id>\w{24})/console$', 'tomato.element.console'),
	(r'^element/(?P<id>\w{24})/console_novnc$', 'tomato.element.console_novnc'),
	(r'^statistics$', 'tomato.main.statistics'),
	(r'^map/$', 'tomato.site_map.map'),
	(r'^map.kml$', 'tomato.site_map.map_kml'),
	(r'^link_stats/(?P<site>\w+)$', 'tomato.site_map.details_site'),
	(r'^link_stats/(?P<src>\w+)/(?P<dst>\w+)$', 'tomato.site_map.details_link'),
	url(r'^host/$', 'tomato.admin.host.list', {"organization": None, "site": None}, name="host_list"),
	url(r'^organization/(?P<organization>\w+)/hosts$', 'tomato.admin.host.list', name="organization_hosts"),
	url(r'^site/(?P<site>\w+)/hosts$', 'tomato.admin.host.list', name="site_hosts"),
	(r'^host/add$', 'tomato.admin.host.add'),
	(r'^host/add/(?P<site>\w+)$', 'tomato.admin.host.add'),
	(r'^host/(?P<name>[^/]+)$', 'tomato.admin.host.info'),
	(r'^host/(?P<name>[^/]+)/edit$', 'tomato.admin.host.edit'),
	(r'^host/(?P<name>[^/]+)/remove$', 'tomato.admin.host.remove'),
	(r'^host/(?P<name>[^/]+)/usage$', 'tomato.usage.host'),
	(r'^organization/$', 'tomato.admin.organization.list'),
	(r'^organization/add$', 'tomato.admin.organization.add'),
	(r'^organization/(?P<name>\w+)$', 'tomato.admin.organization.info'),
	(r'^organization/(?P<name>\w+)/edit$', 'tomato.admin.organization.edit'),
	(r'^organization/(?P<name>\w+)/remove$', 'tomato.admin.organization.remove'),
	(r'^organization/(?P<name>\w+)/usage$', 'tomato.usage.organization'),
	(r'^organization/(?P<organization>\w+)/add_site$', 'tomato.admin.site.add'),
    (r'^site/$', 'tomato.admin.site.list'),
    (r'^site/add$', 'tomato.admin.site.add'),
    (r'^site/(?P<name>\w+)/edit$', 'tomato.admin.site.edit'),
    (r'^site/(?P<name>\w+)/info$', 'tomato.admin.site.info'),
	(r'^site/(?P<name>\w+)/remove$', 'tomato.admin.site.remove'),
	url(r'^template/$', 'tomato.template.list', {"tech": None}, name="template_list"),
	url(r'^template/bytech/(?P<tech>\w+)$', 'tomato.template.list', name="template_list_bytech"),
	(r'^template/add$', 'tomato.template.add'),
	(r'^template/add/(?P<tech>\w+)$', 'tomato.template.add'),
    (r'^template/(?P<res_id>\w{24})$', 'tomato.template.info'),
    (r'^template/(?P<res_id>\w{24})/torrent$', 'tomato.template.download_torrent'),
	(r'^template/(?P<res_id>\w{24})/edit$', 'tomato.template.edit'),
	(r'^template/(?P<res_id>\w{24})/edit/torrent$', 'tomato.template.edit_torrent'),
	(r'^template/(?P<res_id>\w{24})/remove$', 'tomato.template.remove'),
	url(r'^profile/$', 'tomato.profile.list', {"tech": None}, name="profile_list"),
	url(r'^profile/bytech/(?P<tech>\w+)$', 'tomato.profile.list', name="profile_list_bytech"),
	(r'^profile/add/$', 'tomato.profile.add'),
	(r'^profile/add/(?P<tech>\w+)$', 'tomato.profile.add'),
	(r'^profile/(?P<res_id>\w{24})$', 'tomato.profile.info'),
	(r'^profile/(?P<res_id>\w{24})/edit$', 'tomato.profile.edit'),
	(r'^profile/(?P<res_id>\w{24})/remove$', 'tomato.profile.remove'),
	(r'^external_network/$', 'tomato.external_network.list'),
	(r'^external_network/add/$', 'tomato.external_network.add'),
	(r'^external_network/(?P<res_id>\w{24})/edit$', 'tomato.external_network.edit'),
	(r'^external_network/(?P<res_id>\w{24})/remove$', 'tomato.external_network.remove'),
	url(r'^external_network/(?P<network>\w{24})/instances$', 'tomato.external_network_instance.list', name="external_network_instances"),
	url(r'^external_network_instance$', 'tomato.external_network_instance.list', name="external_network_instances_all"),
	(r'^external_network_instance/add$', 'tomato.external_network_instance.add'),
	(r'^external_network_instance/add/(?P<network>\w{24})$', 'tomato.external_network_instance.add'),
	(r'^external_network_instance/add/all/(?P<host>[^/]+)$', 'tomato.external_network_instance.add'),
	(r'^external_network_instance/add/(?P<network>\w{24})/(?P<host>[^/]+)$', 'tomato.external_network_instance.add'),
	(r'^external_network_instance/(?P<res_id>\w{24})/edit$', 'tomato.external_network_instance.edit'),
	(r'^external_network_instance/(?P<res_id>\w{24})/remove$', 'tomato.external_network_instance.remove'),
	url(r'^host/(?P<host>[^/]+)/external_networks$', 'tomato.external_network_instance.list', name="host_external_networks"),
	url(r'^host/(?P<host>[^/]+)/external_network/(?P<network>\w{24})$', 'tomato.external_network_instance.list', name="host_external_network"),
	url(r'^site/(?P<site>[^/]+)/external_networks$', 'tomato.external_network_instance.list', name="site_external_networks"),
	url(r'^site/(?P<site>[^/]+)/external_network/(?P<network>\w{24})$', 'tomato.external_network_instance.list', name="site_external_network"),
	url(r'^organization/(?P<organization>[^/]+)/external_networks$', 'tomato.external_network_instance.list', name="organization_external_networks"),
	url(r'^organization/(?P<organization>[^/]+)/external_network/(?P<network>\w{24})$', 'tomato.external_network_instance.list', name="organization_external_network"),
	(r'^ajax/topology/(?P<id>\w{24})/info$', 'tomato.ajax.topology_info'),
	(r'^ajax/topology/(?P<id>\w{24})/action$', 'tomato.ajax.topology_action'),
	(r'^ajax/topology/(?P<id>\w{24})/modify$', 'tomato.ajax.topology_modify'),
	(r'^ajax/topology/(?P<id>\w{24})/permission$', 'tomato.ajax.topology_permission'),
	(r'^ajax/topology/(?P<id>\w{24})/remove$', 'tomato.ajax.topology_remove'),
	(r'^ajax/element/(?P<id>\w{24})/info$', 'tomato.ajax.element_info'),
	(r'^ajax/topology/(?P<topid>\w{24})/create_element$', 'tomato.ajax.element_create'),
	(r'^ajax/element/(?P<id>\w{24})/action$', 'tomato.ajax.element_action'),
	(r'^ajax/element/(?P<id>\w{24})/modify$', 'tomato.ajax.element_modify'),
	(r'^ajax/element/(?P<id>\w{24})/remove$', 'tomato.ajax.element_remove'),
	(r'^ajax/connection/(?P<id>\w{24})/info$', 'tomato.ajax.connection_info'),
	(r'^ajax/connection/create$', 'tomato.ajax.connection_create'),
	(r'^ajax/connection/(?P<id>\w{24})/action$', 'tomato.ajax.connection_action'),
	(r'^ajax/connection/(?P<id>\w{24})/modify$', 'tomato.ajax.connection_modify'),
	(r'^ajax/connection/(?P<id>\w{24})/remove$', 'tomato.ajax.connection_remove'),
	(r'^ajax/account/(?P<name>.*)/info', 'tomato.ajax.account_info'),
	(r'^debug/host_users/(?P<name>[^/]+)$', 'tomato.debug.host_users'),
	(r'^debug/topology/(?P<id>\w{24})$', 'tomato.debug.topology'),
	(r'^debug/element/(?P<id>\w{24})$', 'tomato.debug.element'),
	(r'^debug/connection/(?P<id>\w{24})$', 'tomato.debug.connection'),
	(r'^debug/stats$', 'tomato.debug.stats'),
    url(r'^dumpmanager/$',  'tomato.dumpmanager.group_list',name='errorgroup_list'),
    (r'^dumpmanager/refresh$', 'tomato.dumpmanager.refresh'),
    (r'^dumpmanager/group/(?P<group_id>\w+)$', 'tomato.dumpmanager.group_info'),
    (r'^dumpmanager/group/(?P<group_id>\w+)/edit$', 'tomato.dumpmanager.group_edit'),
    (r'^dumpmanager/group/(?P<group_id>\w+)/hide$', 'tomato.dumpmanager.group_hide'),
    (r'^dumpmanager/group/(?P<group_id>\w+)/remove$', 'tomato.dumpmanager.group_remove'),
    (r'^dumpmanager/group/(?P<group_id>\w+)/add_to_favorites', 'tomato.dumpmanager.errorgroup_favorite'),
    (r'^dumpmanager/group/(?P<group_id>\w+)/remove_from_favorites', 'tomato.dumpmanager.errorgroup_unfavorite'),
		(r'^dumpmanager/group/(?P<group_id>\w+)/github', 'tomato.dumpmanager.errorgroup_github'),
    (r'^dumpmanager/group/(?P<group_id>\w+)/source/(?P<source>[^/]+)/dump/(?P<dump_id>[\d_.]+)/export$', 'tomato.dumpmanager.dump_export'),
    (r'^dumpmanager/group/(?P<group_id>\w+)/source/(?P<source>[^/]+)/dump/(?P<dump_id>[\d_.]+)/export_data$', 'tomato.dumpmanager.dump_export_with_data')
)
