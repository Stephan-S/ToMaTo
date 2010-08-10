# -*- coding: utf-8 -*-

from util import XmlObject, curry
import api

class Connection(XmlObject):
	"""
	This class represents a connection 
	"""

	def __init__ ( self, connector, dom, load_ids ):
		"""
		Creates a connection object
		@param connector the parent connector object
		@param dom the xml dom object of the connection
		@param load_ids whether to load or ignore assigned ids
		"""
		self.connector = connector
		self.decode_xml ( dom, load_ids )
		if not self.device_id:
			raise api.Fault(api.Fault.MALFORMED_TOPOLOGY_DESCRIPTION, "Malformed topology description: connection must have a device attribute")
		try:
			self.device = connector.topology.devices[self.device_id]
		except KeyError:
			raise api.Fault(api.Fault.MALFORMED_TOPOLOGY_DESCRIPTION, "Malformed topology description: connection must reference an existing device: %s" % self.device_id)
		if not self.device_id:
			raise api.Fault(api.Fault.MALFORMED_TOPOLOGY_DESCRIPTION, "Malformed topology description: connection must have an interface attribute")
		try:
			self.interface = self.device.interfaces[self.interface_id]
		except KeyError:
			raise api.Fault(api.Fault.MALFORMED_TOPOLOGY_DESCRIPTION, "Malformed topology description: connection must reference an existing interface: %s.%s" % ( self.device_id, self.interface_id) )
		self.interface.connection = self

	def encode_xml (self, dom, doc, print_ids):
		"""
		Encode the object to an xml dom object
		@param dom the xml dom object to write the data to
		@param doc the xml document needed to create child elements
		@param print_ids whether to include or ignore assigned ids
		"""
		XmlObject.encode_xml(self, dom)
		if not print_ids:
			if dom.hasAttribute("bridge_id"):
				dom.removeAttribute("bridge_id")
				if dom.hasAttribute("bridge"):
					dom.removeAttribute("bridge")

	def decode_xml (self, dom, load_ids):
		"""
		Read the attributes from the xml dom object
		@param dom the xml dom object to read the data from
		@param load_ids whether to load or ignore assigned ids
		"""
		if not load_ids:
			if dom.hasAttribute("bridge_id"):
				dom.removeAttribute("bridge_id")
				if dom.hasAttribute("bridge"):
					dom.removeAttribute("bridge")
		XmlObject.decode_xml(self,dom)

	bridge_name=property(curry(XmlObject.get_attr, "bridge"), curry(XmlObject.set_attr, "bridge"))
	"""
	The name of the bridge device for this connection. If bridge_id is defined this is expected to be "gbr"+bridge_id
	"""
	
	bridge_id=property(curry(XmlObject.get_attr, "bridge_id"), curry(XmlObject.set_attr, "bridge_id"))
	"""
	The id of the bridge device for this connection. If bridge_id is defined bridge_name is expected to be "gbr"+bridge_id
	"""

	device_id=property(curry(XmlObject.get_attr, "device"), curry(XmlObject.set_attr, "device"))
	"""
	The id of the device that this connection goes to.
	"""

	interface_id=property(curry(XmlObject.get_attr, "interface"), curry(XmlObject.set_attr, "interface"))
	"""
	The id of the interface on the device that this connection goes to.
	"""
	
	delay=property(curry(XmlObject.get_attr, "delay"), curry(XmlObject.set_attr, "delay"))
	"""
	Propagation delay, measured in milliseconds.  The value is rounded to the next multiple of the clock tick (typically 10ms, but it is a good practice to run kernels with “options HZ=1000” to reduce the granularity to 1ms or less).  The default value is 0, meaning no delay. [ipfw.8]
	"""
	
	bandwidth=property(curry(XmlObject.get_attr, "bandwidth"), curry(XmlObject.set_attr, "bandwidth"))
	"""
	Bandwidth, measured in [K|M]{bit/s|Byte/s}.
	A value of 0 (default) means unlimited bandwidth. The unit must immediately follow the number. [ipfw.8]
	"""
	
	lossratio=property(curry(XmlObject.get_attr, "lossratio"), curry(XmlObject.set_attr, "lossratio"))
	"""
	Packet loss rate.  Argument packet-loss-rate is a floating-point number between 0 and 1, with 0 meaning no loss, 1 meaning 100% loss.  The loss rate is internally represented on 31 bits. [ipfw.8]
	"""
	
	def write_control_script(self, host, script, fd):
		"""
		Write the control scrips for this object and its child objects
		"""
		if script == "start":
			fd.write("brctl addbr %s\n" % self.bridge_name )
			fd.write("ip link set %s up\n" % self.bridge_name )
			if self.bridge_id:
				pipe_id = int(self.bridge_id) * 10
				pipe_config=""
				fd.write("modprobe ipfw_mod\n")
				fd.write("ipfw add %d pipe %d via %s out\n" % ( pipe_id+1, pipe_id, self.bridge_name ) )
				if self.delay:
					pipe_config = pipe_config + " " + "delay %s" % self.delay
				if self.bandwidth:
					pipe_config = pipe_config + " " + "bw %s" % self.bandwidth
				fd.write("ipfw pipe %d config %s\n" % ( pipe_id, pipe_config ) )
				if self.lossratio:
					fd.write("ipfw add %d prob %s drop via %s out\n" % ( pipe_id, self.lossratio, self.bridge_name ) )
		if script == "stop":
			fd.write("ip link set %s down\n" % self.bridge_name )
			fd.write("brctl delbr %s\n" % self.bridge_name )
			if self.bridge_id:
				pipe_id = int(self.bridge_id) * 10
				fd.write("ipfw delete %d\n" % pipe_id )
				fd.write("ipfw delete %d\n" % ( pipe_id + 1 ) )
		
	
	def retake_resources(self):
		"""
		Take all resources that this object and child objects once had. Fields containing the ids of assigned resources control which resources will be taken.
		"""
		if self.bridge_id:
			self.device.host.bridge_ids.take_specific(self.bridge_id)
			self.bridge_name = "gbr" + self.bridge_id

	def take_resources(self):
		"""
		Take free resources for all unassigned resource slots of those object and its child objects. The number of the resources will be stored in internal fields.
		"""
		if not self.bridge_id and not self.bridge_name:
			self.bridge_id = self.device.host.bridge_ids.take()
			self.bridge_name = "gbr" + self.bridge_id

	def free_resources(self):
		"""
		Free all resources for all resource slots of this object and its child objects.
		"""
		if self.bridge_id:
			self.device.host.bridge_ids.free(self.bridge_id)
			self.bridge_id = None
			self.bridge_name = None
			
	def __repr__(self):
		return self.connector.id + "<->" + repr(self.interface)
