/********************************************************************************
 * Browser quirks:
 * - IE8 does not like a comma after the last function in a class
 * - IE8 does not like colors defined as words, so only traditional #RRGGBB colors
 * - IE8 does not like texts with specified fonts, etc.
 * - Firefox opens new tabs/windows when icons are clicked with shift or ctrl key
 *   hold, so all icons are overlayed with a transparent rectangular
 * - Opera zooms in when ctrl is hold while pressing the left mouse button and
 *   reacts sometines strangely when alt key is hold.
 ********************************************************************************/ 

var NetElement = Class.extend({
	init: function(editor){
		this.editor = editor;
		this.selected = false;
		this.editor.addElement(this);
		this.attributes = {};
	},
	remove: function(){
		this.editor.removeElement(this);
		if (this.selectionFrame) this.selectionFrame.remove();
		this.editor.ajaxModify([this.modification("delete", {})], function(res) {});
	},
	paint: function(){
	},
	paintUpdate: function(){
		if (this.selected) {
			var rect = this.getRect();
			rect = {x: rect.x-5, y: rect.y-5, width: rect.width+10, height: rect.height+10};
			if (!this.selectionFrame) this.selectionFrame = this.editor.g.rect(rect.x, rect.y, rect.width, rect.height).attr({stroke:this.editor.glabColor, "stroke-width": 2});
			this.selectionFrame.attr(rect);
		} else {
			if (this.selectionFrame) this.selectionFrame.remove();
			this.selectionFrame = false;
		}
	},
	getX: function() {
		return this.getPos().x;
	},
	getY: function() {
		return this.getPos().y;
	},
	getWidth: function() {
		return this.getSize().x;
	},
	getHeight: function() {
		return this.getSize().y;
	},
	getRect: function() {
		return {x: this.getX()-this.getWidth()/2, y: this.getY()-this.getHeight()/2, width: this.getWidth(), height: this.getHeight()};
	},
	setSelected: function(isSelected) {
		this.selected = isSelected;
		this.paintUpdate();
	},
	isSelected: function() {
		return this.selected;
	},
	onClick: function(event) {
		if (!this.editor.editable) {
			this.form.toggle();
			return;
		}
		if (event.shiftKey) this.setSelected(!this.isSelected());
		else {
			var oldSelected = this.isSelected();
			var sel = this.editor.selectedElements();
			for (var i in sel) sel[i].setSelected(false);
			this.setSelected(!oldSelected | sel.length>1);
		}
	},
	modification: function(type, attr) {
		return {"type": this.getElementType() + "-" + type, "element": this.getElementName(), "subelement": this.getSubElementName(), "properties": attr};
	},
	setAttribute: function(name, value) {
		this.attributes[name]=value;
		var attr = {};
		attr[name]=value;
		this.editor.ajaxModify([this.modification("configure", attr)]);
	},
	getAttribute: function(name) {
		return this.attributes[name];
	},
	setAttributes: function(attrs) {
		for (var key in attrs) this.setAttribute(key, attrs[key]);
	},
	getElementType: function() {
		return "";
	},
	getElementName: function() {
		return "";
	},
	getSubElementName: function() {
		return "";
	}
});

var IconElement = NetElement.extend({
	init: function(editor, name, iconsrc, iconsize, pos) {
		this.name = name;
		this._super(editor);
		this.iconsrc = iconsrc;
		this.iconsize = iconsize;
		this.pos = pos;
		this.paletteItem = false;
	},
	_dragMove: function (dx, dy) {
		var p = this.parent;
		if (! p.editor.editable) return false;
		if (p.paletteItem) p.shadow.attr({x: p.opos.x + dx-p.iconsize.x/2, y: p.opos.y + dy-p.iconsize.y/2});
		else p.move({x: p.opos.x + dx, y: p.opos.y + dy});
	}, 
	_dragStart: function () {
		var p = this.parent;
		if (! p.editor.editable) return false;
		p.opos = p.pos;
		if (p.paletteItem) p.shadow = p.icon.clone().attr({opacity:0.5});
	},
	_dragStop: function () {
		var p = this.parent;
		if (! p.editor.editable) return false;
		if (p.paletteItem) {
			var pos = {x: p.shadow.attr("x")+p.iconsize.x/2, y: p.shadow.attr("y")+p.iconsize.y/2};
			if (pos.x != p.opos.x || pos.y != p.opos.y) {
				var element = p.createAnother(pos);
				element.move(element.correctPos(pos));
			}
			p.shadow.remove();
		}
		if (p.pos != p.opos) {
			p.move(p.correctPos(p.pos));
			p.lastMoved = new Date();
			p.setAttribute("pos", (p.pos.x-p.editor.paletteWidth)+","+p.pos.y);
		}
	},
	_click: function(event){
		var p = this.parent;
		if (p.lastMoved && p.lastMoved.getTime() + 1 > new Date().getTime()) return;
		p.onClick(event);
	},
	_dblclick: function(event){
		var p = this.parent;
		p.form.toggle();
	},
	paint: function(){
		this._super();
		if (this.text) this.text.remove();
		this.text = this.editor.g.text(this.pos.x, this.pos.y+this.iconsize.y/2+7, this.name);
		if (! isIE) this.text.attr(this.editor.defaultFont);
		this.text.parent = this;
		if (this.icon) this.icon.remove();
		this.icon = this.editor.g.image(basepath+this.iconsrc, this.pos.x-this.iconsize.x/2, this.pos.y-this.iconsize.y/2, this.iconsize.x, this.iconsize.y);
		this.icon.parent = this;
		this.stateIcon = this.editor.g.image(basepath+"images/started.png", this.pos.x+5, this.pos.y+5, 16, 16);
		this.stateIcon.attr({opacity: 0.0});
		var r = this.getRect();
		if (this.rect) this.rect.remove();
		this.rect = this.editor.g.rect(r.x, r.y, r.width, r.height).attr({opacity:0, fill:"#FFFFFF"});
		this.rect.parent = this;
		this.rect.drag(this._dragMove, this._dragStart, this._dragStop);
		this.rect.click(this._click);    
		this.rect.dblclick(this._dblclick);
	},
	paintUpdate: function() {
		this.icon.attr({x: this.pos.x-this.iconsize.x/2, y: this.pos.y-this.iconsize.y/2, src: basepath+this.iconsrc});
		this.stateIcon.attr({x: this.pos.x+5, y: this.pos.y+5});
		this.text.attr({x: this.pos.x, y: this.pos.y+this.iconsize.y/2+7, text: this.name});
		this.rect.attr(this.getRect());
		this._super(); //must be at end, so rect has already been updated
	},
	setAttribute: function(name, value) {
		this._super(name, value);
		if (name == "name") {
			arrayRemove(this.editor.elementNames, this.name);
			this.editor.ajaxModify([this.modification("rename", {name: value})], function(res) {});
			this.name = value;
			this.paintUpdate();
			this.editor.elementNames.push(value);
		} else if (name == "state") {
			switch (value) {
				case "started":
				case "prepared":
					this.stateIcon.attr({src: basepath+"images/"+value+".png"});
					this.stateIcon.attr({opacity: 1.0});
					break;
				default:
					this.stateIcon.attr({opacity: 0.0});
			}
		}
	},
	remove: function(){
		this._super();
		if (this.icon) this.icon.remove();
		if (this.text) this.text.remove();
		if (this.rect) this.rect.remove();
		if (this.stateIcon) this.stateIcon.remove();
	},
	correctPos: function(pos) {
		if (pos.x + this.iconsize.x/2 > this.editor.g.width) pos.x = this.editor.g.width - this.iconsize.x/2;
		if (pos.y + this.iconsize.y/2 + 11 > this.editor.g.height) pos.y = this.editor.g.height - this.iconsize.y/2 - 11;
		if (pos.x - this.iconsize.x/2 < this.editor.paletteWidth) pos.x = this.editor.paletteWidth + this.iconsize.x/2;
		if (pos.y - this.iconsize.y/2 < 0) pos.y = this.iconsize.y/2;
		return pos;
	},
	move: function(pos) {
		pos.x = pos.x || 0;
		pos.y = pos.y || 0;
		this.pos = pos;
		this.paintUpdate();
	},
	getPos: function() {
		return this.pos;
	},
	getSize: function() {
		return {x: Math.max(this.text.getBBox().width,this.iconsize.x), y: this.iconsize.y + this.text.getBBox().height};
	},
	getRect: function() {
		return compoundBBox([this.text, this.icon]);
	},
	createAnother: function(pos) {
	},
	setSelected: function(isSelected) {
		this._super(isSelected & !this.paletteItem);
	},
	getElementName: function() {
		return this.name;
	}
});
	
var Topology = IconElement.extend({
	init: function(editor, name, pos) {
		this._super(editor, name, "images/topology.png", {x: 32, y: 32}, pos);
		this.paletteItem = true;
		this.paint();
		this.form = new TopologyForm(this);
	},
	setAttribute: function(name, value) {
		//ignore name changes
		this.attributes[name]=value;
		if (name == "name") this.editor.ajaxModify([this.modification("rename", {name: value})], function(res) {});
	},
	_dragStart: function () {
	},
	_dragMove: function (dx, dy) {
	},
	_dragStop: function () {
	},
	getElementType: function () {
		return "topology";
	}
});

var Connection = NetElement.extend({
	init: function(editor, con, dev) {
		this._super(editor);
		this.con = con;
		this.dev = dev;
		this.paint();
		this.isConnection = true ;
		this.iface = false;
		this.name = "connection";
		this.form = new ConnectionForm(this);		
	},
	connect: function(iface) {
		this.iface = iface;
		this.editor.ajaxModify([this.modification("create", {"interface": this.getSubElementName()})], function(res) {});
	},
	getElementType: function () {
		return "connection";
	},
	getElementName: function () {
		if (this.con) return this.con.name;
		else return "";
	},
	getSubElementName : function() {
		if (this.dev && this.iface) return this.dev.name + "." + this.iface.name;
		else return "";
	},
	getIPHint: function() {
		return "dhcp";
	},	
	getPos: function(){
		return {x: (this.con.getX()+this.dev.getX())/2, y: (this.con.getY()+this.dev.getY())/2};
	},
	getSize: function() {
		return {x: 16, y: 16};
	},
	getPath: function(){
		return "M"+this.con.getX()+" "+this.con.getY()+"L"+this.dev.getX()+" "+this.dev.getY();
	},
	paintUpdate: function(){
		this._super();
		this.path.attr({path: this.getPath()});
		this.handle.attr({x: this.getX()-8, y: this.getY()-8});
	},
	paint: function(){
		this._super();
		if (this.path) this.path.remove();
		this.path = this.editor.g.path(this.getPath());
		this.path.toBack();
		if (this.handle) this.handle.remove();
		this.handle = this.editor.g.rect(this.getX()-8, this.getY()-8, 16, 16).attr({fill: "#A0A0A0"});
		this.handle.parent = this;
		this.handle.drag(this._dragMove, this._dragStart, this._dragStop);
		this.handle.click(this._click);
		this.handle.dblclick(this._dblclick);
	},
	remove: function(){
		this._super();
		if (this.path) this.path.remove();
		if (this.handle) this.handle.remove();
		if (this.con) this.con.removeConnection(this);
		if (this.iface) {
			var tmp = this.iface;
			delete this.iface;
			tmp.remove();
		}
		delete this.con;
		delete this.dev;
	},
	_click: function(event){
		var p = this.parent;
		p.onClick(event);
	},
	_dblclick: function(event){
		var p = this.parent;
		p.form.toggle();
	}
});

var EmulatedConnection = Connection.extend({
	init: function(editor, dev, con){
		this._super(editor, dev, con);
		this.handle.attr({fill: this.editor.glabColor});
		this.form = new EmulatedConnectionForm(this);
		this.IPHintNumber = this.con.nextIPHintNumber++;
	},
	getIPHint: function() {
		return "10."+this.con.IPHintNumber+".0."+this.IPHintNumber+"/24";
	}	
});

var EmulatedRouterConnection = EmulatedConnection.extend({
	init: function(editor, dev, con){
		this._super(editor, dev, con);
		this.form = new EmulatedRouterConnectionForm(this);
		this.setAttribute("gateway", "10."+this.con.IPHintNumber+"."+this.IPHintNumber+".254/24");
	},
	getIPHint: function() {
		return "10."+this.con.IPHintNumber+"."+this.IPHintNumber+".1/24";
	}	
});

var Interface = NetElement.extend({
	init: function(editor, dev, con){
		this._super(editor);
		this.dev = dev;
		this.con = con;
		this.paint();
		this.isInterface = true;
		this.name = "eth" + dev.interfaces.length;
		this.form = new InterfaceForm(this);
		this.editor.ajaxModify([this.modification("create", {name: this.name})], function(res) {});
	},
	getElementType: function () {
		return "interface";
	},
	getElementName: function () {
		return this.dev.name;
	},
	getSubElementName : function() {
		return this.name;
	},
	getPos: function() {
		var xd = this.con.getX() - this.dev.getX();
		var yd = this.con.getY() - this.dev.getY();
		var magSquared = (xd * xd + yd * yd);
		var mag = 14.0 / Math.sqrt(magSquared);
		return {x: this.dev.getX() + (xd * mag), y: this.dev.getY() + (yd * mag)};
	},
	getSize: function() {
		return {x: 16, y: 16};
	},
	paint: function(){
		if (this.circle) this.circle.remove();
		this.circle = this.editor.g.circle(this.getX(), this.getY(), 8).attr({fill: "#CDCDB3"});
		this.circle.parent = this;
		this.circle.click(this._click);
		this.circle.dblclick(this._dblclick);
	},
	paintUpdate: function(){
		this._super();
		this.circle.attr({cx: this.getX(), cy: this.getY()});
	},
	remove: function(){
		this._super();
		if (this.circle) this.circle.remove();
		if (this.dev) this.dev.removeInterface(this);
		delete this.con;
		delete this.dev;
	},
	_click: function(event) {
		var p = this.parent;
		p.onClick(event);
	},
	_dblclick: function(event){
		var p = this.parent;
		p.form.toggle();
	}
});

var ConfiguredInterface = Interface.extend({
	init: function(editor, dev, con){
		this._super(editor, dev, con);
		this.form = new ConfiguredInterfaceForm(this);
		var ipHint = con.getIPHint();
		this.setAttribute("use_dhcp", ipHint == "dhcp");
		if (ipHint != "dhcp" ) this.setAttribute("ip4address", ipHint);
	}
});

var Connector = IconElement.extend({
	init: function(editor, name, iconsrc, iconsize, pos) {
		this._super(editor, name, iconsrc, iconsize, pos);
		this.connections = [];
		this.paint();
		this.isConnector = true;
		this.IPHintNumber = this.editor.nextIPHintNumber++;
		this.nextIPHintNumber = 1;
		this.editor.ajaxModify([this.modification("create", {type: this.baseName(), pos:(pos.x-editor.paletteWidth)+","+pos.y, name: name})], function(res) {});
	},
	getElementType: function () {
		return "connector";
	},
	getElementName: function () {
		return this.name;
	},
	nextName: function() {
		return this.editor.getNameHint(this.baseName());
	},
	remove: function(){
		var cons = this.connections.slice(0);
		for (var i in cons) cons[i].remove();
		this._super();
	},
	move: function(pos) {
		this._super(pos);
		for (var i in this.connections) {
			this.connections[i].paintUpdate();
			this.connections[i].dev.paintUpdateInterfaces();
		}    
	},
	onClick: function(event) {
		if (event.ctrlKey || event.altKey) {
			var selectedElements = this.editor.selectedElements();
			for (var i in selectedElements) {
				var el = selectedElements[i];
				if (el.isDevice && !this.isConnectedWith(el)) this.editor.connect(this, el);
			}
		} else this._super(event);
	},
	isConnectedWith: function(dev) {
		for (var i in this.connections) if (this.connections[i].dev == dev) return true;
		return false;
	},
	createConnection: function(dev) {
		var con = new Connection(this.editor, this, dev);
		this.connections.push(con);
		return con;
	},
	removeConnection: function(con) {
		arrayRemove(this.connections,con);
	}
});

var SpecialConnector = Connector.extend({
	init: function(editor, name, pos) {
		this._super(editor, name, "images/special.png", {x: 32, y: 32}, pos);
		this.form = new SpecialConnectorForm(this);
	},
	nextIPHint: function() {
		return "dhcp";
	},
	setAttribute: function(name, value) {
		this._super(name, value);
		if (name == "feature_type") {
			if (value=="openflow" || value=="internet") this.iconsrc="images/"+value+".png";
			else this.iconsrc="images/special.png";
			this.paintUpdate();
		}
	},
	baseName: function() {
		return "special";
	},
	createAnother: function(pos) {
		return new SpecialConnector(this.editor, this.nextName(), pos);
	}
});

var HubConnector = Connector.extend({
	init: function(editor, name, pos) {
		this._super(editor, name, "images/hub.png", {x: 32, y: 16}, pos);
		this.form = new HubConnectorForm(this);
	},
	baseName: function() {
		return "hub";
	},
	createAnother: function(pos) {
		return new HubConnector(this.editor, this.nextName(), pos);
	},
	createConnection: function(dev) {
		var con = new EmulatedConnection(this.editor, this, dev);
		this.connections.push(con);
		return con;
	}
});

var SwitchConnector = Connector.extend({
	init: function(editor, name, pos) {
		if (!pos) { //called with 2 parameters
			pos = name;
			name = this.nextName();
		}
		this._super(editor, name, "images/switch.png", {x: 32, y: 16}, pos);
		this.form = new SwitchConnectorForm(this);
	},
	baseName: function() {
		return "switch";
	},
	createAnother: function(pos) {
		return new SwitchConnector(this.editor, this.nextName(), pos);
	},
	createConnection: function(dev) {
		var con = new EmulatedConnection(this.editor, this, dev);
		this.connections.push(con);
		return con;
	}
});

var RouterConnector = Connector.extend({
	init: function(editor, name, pos) {
		this._super(editor, name, "images/router.png", {x: 32, y: 16}, pos);
		this.form = new RouterConnectorForm(this);
	},
	nextIPHint: function() {
		return "10."+this.IPHintNumber+"."+(this.nextIPHintNumber++)+".1/24";
	},
	baseName: function() {
		return "router";
	},
	createAnother: function(pos) {
		return new RouterConnector(this.editor, this.nextName(), pos);
	},
	createConnection: function(dev) {
		var con = new EmulatedRouterConnection(this.editor, this, dev);
		this.connections.push(con);
		return con;
	}
});

var Device = IconElement.extend({
	init: function(editor, name, iconsrc, iconsize, pos) {
		this._super(editor, name, iconsrc, iconsize, pos);
		this.interfaces = [];
		this.paint();
		this.isDevice = true;
		this.editor.ajaxModify([this.modification("create", {type: this.baseName(), pos:(pos.x-editor.paletteWidth)+","+pos.y, name: name})], function(res) {});
	},
	getElementType: function () {
		return "device";
	},
	getElementName: function () {
		return this.name;
	},
	nextName: function() {
		return this.editor.getNameHint(this.baseName());
	},
	remove: function(){
		var ifs = this.interfaces.slice(0);
		for (var i in ifs) {
			if(ifs[i].con) ifs[i].con.remove();
			else ifs[i].remove();
		}
		this._super();
	},
	move: function(pos) {
		this._super(pos);
		for (var i in this.interfaces) this.interfaces[i].con.paintUpdate();
		this.paintUpdateInterfaces();   
	},
	paint: function() {
		this._super();
		for (var i in this.interfaces) this.interfaces[i].paint();    
	},
	paintUpdateInterfaces: function() {
		for (var i in this.interfaces) this.interfaces[i].paintUpdate();
	},
	onClick: function(event) {
		if (event.ctrlKey || event.altKey) {
			var selectedElements = this.editor.selectedElements();
			for (var i in selectedElements) {
				var el = selectedElements[i];
				if (el.isConnector && !this.isConnectedWith(el)) this.editor.connect(el, this);
				if (el.isDevice && el != this) {
					var middle = {x: (this.getPos().x + el.getPos().x) / 2, y: (this.getPos().y + el.getPos().y) / 2}; 
					var con = new SwitchConnector(this.editor, this.editor.getNameHint("switch"), middle);
					this.editor.connect(con, el);
					this.editor.connect(con, this);
				}
			}
		} else this._super(event);
	},
	isConnectedWith: function(con) {
		for (var i in this.interfaces) if (this.interfaces[i].con.con == con) return true;
		return false;
	},
	createInterface: function(con) {
		var iface = new Interface(this.editor, this, con);
		this.interfaces.push(iface);
		return iface;
	},
	removeInterface: function(iface) {
		arrayRemove(this.interfaces,iface);
	}
});

var OpenVZDevice = Device.extend({
	init: function(editor, name, pos) {
		this._super(editor, name, "images/computer.png", {x: 32, y: 32}, pos);
		this.form = new OpenVZDeviceForm(this);
	},
	baseName: function() {
		return "openvz";
	},
	createAnother: function(pos) {
		return new OpenVZDevice(this.editor, this.nextName(), pos);
	},
	createInterface: function(con) {
		var iface = new ConfiguredInterface(this.editor, this, con);
		this.interfaces.push(iface);
		return iface;
	}
});

var KVMDevice = Device.extend({
	init: function(editor, name, pos) {
		this._super(editor, name, "images/pc_green.png", {x: 32, y: 32}, pos);
		this.form = new KVMDeviceForm(this);
	},
	baseName: function() {
		return "kvm";
	},
	createAnother: function(pos) {
		return new KVMDevice(this.editor, this.nextName(), pos);
	}
});

var Editor = Class.extend({
	init: function(size, editable) {
		this.g = Raphael("editor", size.x, size.y);
		this.editable = editable;
		this.size = size;
		this.paletteWidth = editable ? 60 : 0;
		this.glabColor = "#911A20";
		this.defaultFont = {"font-size":12, "font": "Verdana"};
		this.elements = [];
		this.elementNames = [];
		this.elementNums = {};
		this.hostGroups = [];
		this.templatesOpenVZ = [];
		this.templatesKVM = [];
		this.specialFeatures = {};
		this.nextIPHintNumber = 0;
		this.isLoading = false;
		if (editable) this.paintPalette();
		this.topology = new Topology(this, "Topology", {x: 30+this.paletteWidth, y: 20});
		this.paintBackground();
	},
	infoMessage: function(title, message) {
		var div = $('<div/>').dialog({autoOpen: true, draggable: false, modal: true,
			resizable: false, height:"auto", width:"auto", title: title, dialogClass: "ui-state-highlight"});
		div.append(""+message);
		return div; 
	},
	errorMessage: function(title, message) {
		var div = $('<div/>').dialog({autoOpen: false, draggable: false, modal: true,
			resizable: false, height:"auto", width:"auto", title: title, dialogClass: "ui-state-error"});
		div.append(""+message);
		div.dialog("open");
		return div; 
	},
	ajaxModify: function(mods, func) {
		if (this.isLoading) return;
		console.log("AJAX MOD:");
		for (var i in mods) console.log(mods[i]);
		var data = {"mods": JSON.stringify(mods)};
		var editor = this;
		return $.ajax({type: "POST", url:ajaxpath+"top/"+topid+"/modify", async: true, data: data, complete: function(res){
			if (res.status == 200) {
				var msg = JSON.parse(res.responseText);
				if (! msg.success) editor.errorMessage("Request failed", "<p><b>Error message:</b> " + msg.output + "</p><p>This page will be reloaded to refresh the editor.</p>").bind("dialogclose", function(){
					window.location.reload();						
				});
				if (func) func(msg);
			} else editor.errorMessage("AJAX request failed", res.statusText);
		}});
	},
	setHostGroups: function(groups) {
		this.hostGroups = groups;
	},
	setTemplatesOpenVZ: function(tpls) {
		this.templatesOpenVZ = tpls;
	},
	setTemplatesKVM: function(tpls) {
		this.templatesKVM = tpls;
	},
	setSpecialFeatures: function(sfmap) {
		this.specialFeatures = sfmap;
	},
	loadTopologyURL: function(url) {
		var req = $.ajax({type: "GET", url: url, dataType: "xml"});
		var editor = this;
		req.success(function(xml) {
			editor.loadTopologyDOM(xml);
		});
	},
	loadTopologyDOM: function(xml) {
		this.isLoading = true;
		var editor = this;
		var dangling_interfaces_mods = [];
		$(xml).find("topology").each(function(){
			var attrs = getAttributesDOM(this);
			editor.topology.setAttributes(attrs);
			var devices = {};
			var connectors = {};
			var connections = {};
			var f = function(){
				var attrs = getAttributesDOM(this);
				var name = attrs["name"];
				var pos = attrs["pos"].split(",");
				var pos = {x: parseInt(pos[0])+editor.paletteWidth, y: parseInt(pos[1])};
				var type = attrs["type"];
				var el;
				switch (type) {
					case "openvz":
						el = new OpenVZDevice(editor, name, pos);
						devices[name] = el;
						break;
					case "kvm": 
						el = new KVMDevice(editor, name, pos);
						devices[name] = el;
						break;
					case "hub": 
						el = new HubConnector(editor, name, pos);
						connectors[name] = el;
						break;
					case "switch": 
						el = new SwitchConnector(editor, name, pos);
						connectors[name] = el;
						break;
					case "router": 
						el = new RouterConnector(editor, name, pos);
						connectors[name] = el;
						break;
					case "special": 
						el = new SpecialConnector(editor, name, pos);
						connectors[name] = el;
						break;
				}
				el.setAttributes(attrs);
			};
			$(this).find('device').each(f);
			$(this).find('connector').each(f);
			$(this).find('connection').each(function(){
				var attrs = getAttributesDOM(this);
				var con = connectors[$(this).parent().attr("name")];
				var ifname = attrs["interface"];
				var device = devices[ifname.split(".")[0]];
				var c = con.createConnection(device);
				c.setAttributes(attrs);
				connections[ifname] = c;
			});
			$(this).find('interface').each(function(){
				var attrs = getAttributesDOM(this);
				var device = devices[$(this).parent().attr("name")];
				var name = attrs["name"];
				var con = connections[device.name+"."+name];
				if (con) {
					var iface = device.createInterface(con);
					con.connect(iface);
					iface.setAttributes(attrs);
				} else {
					console.log(con);
					dangling_interfaces_mods.push({type: "interface-delete", element: device.name, subelement: name, properties: {}});
				}
			});
		});
		this.isLoading = false;
		if (dangling_interfaces_mods.length > 0) this.ajaxModify(dangling_interfaces_mods, new function(res){});
	},
	getPosition: function () { 
		var pos = $("#editor").position();
		return {x: pos.left, y: pos.top};
	}, 
	paintPalette: function() {
		this.isLoading = true;
		var y = 25;
		this.g.path("M"+this.paletteWidth+" 0L"+this.paletteWidth+" "+this.g.height).attr({"stroke-width": 2, stroke: this.glabColor});
		this.icon = this.g.image(basepath+"images/glablogo.jpg", 1, 5, this.paletteWidth-6, 79/153*(this.paletteWidth-6));
		this.openVZPrototype = new OpenVZDevice(this, "OpenVZ", {x: this.paletteWidth/2, y: y+=50});
		this.openVZPrototype.paletteItem = true;
		this.kvmPrototype = new KVMDevice(this, "KVM", {x: this.paletteWidth/2, y: y+=50});
		this.kvmPrototype.paletteItem = true;
		y+=30;
		this.specialPrototype = new SpecialConnector(this, "Special", {x: this.paletteWidth/2, y: y+=50});
		this.specialPrototype.paletteItem = true;
		this.hubPrototype = new HubConnector(this, "Hub", {x: this.paletteWidth/2, y: y+=45});
		this.hubPrototype.paletteItem = true;
		this.switchPrototype = new SwitchConnector(this, "Switch", {x: this.paletteWidth/2, y: y+=40});
		this.switchPrototype.paletteItem = true;
		this.routerPrototype = new RouterConnector(this, "Router", {x: this.paletteWidth/2, y: y+=40});
		this.routerPrototype.paletteItem = true;
		this.trash = this.g.image(basepath+"images/trash.png", this.paletteWidth/2 -16, this.size.y-50, 32, 32);
		this.trashText = this.g.text(this.paletteWidth/2, this.size.y-13, "Trash").attr(this.defaultFont);
		this.trashRect = this.g.rect(this.paletteWidth/2 -16, this.size.y-50, 32, 42).attr({fill:"#FFFFFF", opacity:0});
		this.trashRect.parent = this;
		this.trashRect.click(this._trashClick);
		this.nextIPHintNumber = 0; //reset to 0
		this.isLoading = false;
	},
	paintBackground: function() {
		this.background = this.g.rect(this.paletteWidth, 0, this.size.x-this.paletteWidth, this.size.y);
		this.background.attr({fill: "#FFFFFF", opacity: 0});
		this.background.toBack();
		this.background.parent = this;
		if (this.editable) this.background.drag(this._dragMove, this._dragStart, this._dragStop);
		this.background.click(this._click);
		this.background.dblclick(this._dblclick);
	},
	_dragMove: function (dx, dy) {
		var p = this.parent;
		p.selectionFrame.attr({x: Math.min(p.opos.x, p.opos.x+dx), y: Math.min(p.opos.y, p.opos.y+dy), width: Math.abs(dx), height: Math.abs(dy)});
	}, 
	_dragStart: function (x, y) {
		var p = this.parent;
		var startPos = p.getPosition();
		p.opos = {x: x - startPos.x, y: y - startPos.y};
		if (p.selectionFrame) p.selectionFrame.remove();
		p.selectionFrame = p.g.rect(p.opos.x, p.opos.y, 0, 0);
		p.selectionFrame.attr({stroke:"#000000", "stroke-dasharray": "- ", "stroke-width": 2});
	},
	_dragStop: function () {
		var p = this.parent;
		var f = p.selectionFrame;
		p.selectAllInArea({x: f.attr("x"), y: f.attr("y"), width: f.attr("width"), height: f.attr("height")});
		p.selectionFrame.remove();
		if (p.pos != p.opos) p.lastMoved = new Date();
	},
	_click: function(event){
		var p = this.parent;
		if (p.lastMoved && p.lastMoved.getTime() + 1 > new Date().getTime()) return;
		p.unselectAll();
	},
	_dblclick: function(event){
		var p = this.parent;
		p.topology.form.toggle();
	},
	_trashClick: function(event){
		var p = this.parent;
		p.removeSelectedElements();
	},
	connect: function(connector, device) {
		var con = connector.createConnection(device);
		var iface = device.createInterface(con);
		con.connect(iface);
	},
	disable: function() {
		this.disableRect = this.g.rect(0, 0, this.size.x,this.size.y).attr({fill:"#FFFFFF", opacity:.8});
	},
	enable: function() {
		if (this.disableRect) this.disableRect.remove();
	},
	selectedElements: function() {
		var sel = [];
		for (var i in this.elements) if (this.elements[i].isSelected()) sel.push(this.elements[i]);
		return sel;
	},
	unselectAll: function() {
		for (var i in this.elements) this.elements[i].setSelected(false);
	},
	selectAllInArea: function(area) {
		for (var i in this.elements) {
			var el = this.elements[i];
			var rect = el.getRect();
			var mid = {x: rect.x+rect.width/2, y: rect.y+rect.height/2};
			var isin = mid.x <= area.x + area.width && mid.x >= area.x && mid.y <= area.y + area.height && mid.y >= area.y;
			el.setSelected(isin);
		}
	},
	getNameHint: function(type) {
		var num = this.elementNums[type];
		if (!num) num = 1;
		while($.inArray(type+num, this.elementNames) >= 0) num++;
		this.elementNums[type]=num;
		return type+num;
	},
	addElement: function(el) {
		this.elements.push(el);
		if (el.name) this.elementNames.push(el.name);
	},
	removeElement: function(el) {
		arrayRemove(this.elements, el);
		if (el.name) arrayRemove(this.elementNames, el.name);
	},
	removeSelectedElements: function() {
		var sel = this.selectedElements();
		for (var i in sel) {
			var el = sel[i];
			if (el.isInterface) continue;
			el.remove();
		}
	}
});

var EditElement = Class.extend({
	init: function(name) {
		this.name = name;
	},
	onChanged: function(value) {
		this.form.obj.setAttribute(this.name, value);
	},
	setValue: function(value) {
	},
	getValue: function() {
	},
	setEditable: function(editable) {
	},
	setForm: function(form) {
		this.form = form;
	},
	getInputElement: function() {
		return null;
	}
});

var TextField = EditElement.extend({
	init: function(name, dflt) {
		this._super(name);
		this.dflt = dflt;
		this.input = $('<input type="text" name="'+name+'" value="'+dflt+'" size=10/>');
		this.input[0].fld = this;
		this.input.change(function (){
			this.fld.onChanged(this.value);
		});
	},
	setEditable: function(editable) {
		this.input.attr({disabled: !editable});
	},
	setValue: function(value) {
		this.input[0].value = value;
	},
	getValue: function() {
		return this.input[0].value;
	},
	getInputElement: function() {
		return this.input;
	}
});

var NameField = TextField.extend({
	init: function(obj) {
		this._super("name", obj.name);
	},
	onChanged: function(value) {
		this._super(value);
		this.form.div.dialog("option", "title", "Attributes of " + value);
	}
});

var MagicTextField = TextField.extend({
	init: function(name, pattern, dflt) {
		this._super(name, dflt);
		this.pattern = pattern;
	},
	onChanged: function(value) {
		this._super(value);
		if (this.pattern.test(this.getValue())) this.input[0].style.color="";
		else this.input[0].style.color="red";
	}
});

var PasswordField = TextField.extend({
	init: function(name, dflt) {
		this._super(name, dflt);
		this.input[0].type = "password";
	}
});

var SelectField = EditElement.extend({
	init: function(name, options, dflt) {
		this._super(name);
		this.options = options;
		this.dflt = dflt;
		this.input = $('<select name="'+name+'"/>');
		if (!(dflt in options)) this.input.append($('<option value="'+dflt+'">'+dflt+'</option>'));
		for (var i in options) {
			var option = $('<option value="'+options[i]+'">'+options[i]+'</option>');
			if (options[i] == dflt) option.attr({selected: true});
			this.input.append(option);
		}
		this.input[0].fld = this;
		this.input.change(function (){
			this.fld.onChanged(this.value);
		});
	},
	setEditable: function(editable) {
		this.input.attr({disabled: !editable});
	},
	setValue: function(value) {
		var found = false;
		this.input.find("option").each(function(){
			$(this).attr({selected: $(this).attr("value") == value});
			found |= $(this).attr("value") == value; 		
		});
		if (!found) this.input.append($('<option value="'+value+'" selected>'+value+'</option>'));
	},
	getValue: function() {
		return this.input[0].value;
	},
	getInputElement: function() {
		return this.input;
	}
});

var CheckField = EditElement.extend({
	init: function(name, dflt) {
		this._super(name);
		this.dflt = dflt;
		this.input = $('<input type="checkbox" name="'+name+'"/>');
		if (dflt) this.input.attr({checked: true});
		this.input[0].fld = this;
		this.input.change(function (){
			this.fld.onChanged(this.checked);
		});
	},
	setEditable: function(editable) {
		this.input.attr({disabled: !editable});
	},
	setValue: function(value) {
		this.input[0].checked = Boolean(value);
	},
	getValue: function() {
		return this.input[0].checked;
	},
	getInputElement: function() {
		return this.input;
	}
});

var Button = EditElement.extend({
	init: function(text, func) {
		this._super("button-"+text);
		this.func = func;
		this.input = $('<input type="button" value="'+text+'"/>');
		this.input[0].fld = this;
		this.input.click(function (){
			this.fld.func(this.fld);
		});
	},
	setEditable: function(editable) {
		this.input.attr({disabled: !editable});
	},
	setValue: function(value) {
	},
	getValue: function() {
		return "";
	},
	getInputElement: function() {
		return this.input;
	}
});

var IconButton = Button.extend({
	init: function(name, src, func) {
		this._super(name, src, func);
		this.input = $('<input type="image" src="'+src+'"/>');
		this.input[0].fld = this;
		this.input.click(function (){
			this.fld.func(this.fld);
		});
	}
});

var AttributeForm = Class.extend({
	init: function(obj) {
		this.obj = obj;
		this.editor = obj.editor;
		this.div = $('<div/>').dialog({autoOpen: false, draggable: false,
			resizable: false, height:"auto", width:"auto", title: "Attributes of "+obj.name,
			show: "slide", hide: "slide"});
		this.table = $('<table/>');
		this.div.append(this.table);
		this.fields = {};
	},
	show: function() {
		var rect = this.obj.getRect();
		var ed = this.editor.getPosition();
		this.div.dialog({position: [ed.x+rect.x+rect.width+8, ed.y+rect.y]});
		for (var name in this.fields) {
			var val = this.obj.attributes[name];
			if (val) this.fields[name].setValue(val);
			this.fields[name].setEditable(this.editor.editable);
		}
		this.div.dialog("open");
	},
	hide: function() {
		this.div.dialog("close");
	},
	toggle: function() {
		if (this.div.dialog("isOpen")) this.hide();
		else this.show();
	},
	addField: function(field, desc) {
		field.setForm(this);
		var tr = $('<tr/>');
		tr.append($('<td>'+desc+'</td>'));
		tr.append($('<td/>').append(field.getInputElement()));
		this.table.append(tr);
		this.fields[field.name]=field;
	},
	addMultipleFields: function(fields) {
		var tr = $('<tr/>');
		var td = $('<td/>');
		td.attr({colspan: "2", align: "center"});
		for (var i in fields) {
			var field = fields[i];
			field.setForm(this);
			this.fields[field.name]=field;
			td.append(field.getInputElement());
		}
		tr.append(td);
		this.table.append(tr);
	}
});

var TopologyForm = AttributeForm.extend({
	init: function(obj) {
		this._super(obj);
		this.addField(new TextField("name", "Topology"), "name");
	}
});

var DeviceForm = AttributeForm.extend({
	init: function(obj) {
		this._super(obj);
		this.addField(new NameField(obj), "name");
		this.addField(new SelectField("hostgroup", this.editor.hostGroups, "auto"), "hostgroup");
	}
});

var OpenVZDeviceForm = DeviceForm.extend({
	init: function(obj) {
		this._super(obj);
		this.addField(new SelectField("template", this.editor.templatesOpenVZ, "auto"), "template");
		this.addField(new TextField("root_password", "glabroot"), "root&nbsp;password");
		this.addField(new MagicTextField("gateway", /^\d+\.\d+\.\d+\.\d+$/, ""), "gateway");
	}
});

var KVMDeviceForm = DeviceForm.extend({
	init: function(obj) {
		this._super(obj);
		this.addField(new SelectField("template", this.editor.templatesKVM, "auto"), "template");
	}	
});

var ConnectorForm = AttributeForm.extend({
	init: function(obj) {
		this._super(obj);
		this.addField(new NameField(obj), "name");
	}
});

var SpecialConnectorForm = ConnectorForm.extend({
	init: function(obj) {
		this._super(obj);
		this.addField(new SelectField("feature_type", getKeys(this.editor.specialFeatures), "auto"), "type");
		this.addField(new SelectField("hostgroup", this.editor.hostGroups, "auto"), "hostgroup");
	}
});

var HubConnectorForm = ConnectorForm.extend({});

var SwitchConnectorForm = ConnectorForm.extend({});

var RouterConnectorForm = ConnectorForm.extend({});

var InterfaceForm = AttributeForm.extend({
	init: function(obj) {
		this._super(obj);
		this.addField(new NameField(obj), "name");
	}
});

var ConfiguredInterfaceForm = InterfaceForm.extend({
	init: function(obj) {
		this._super(obj);
		this.addField(new CheckField("use_dhcp", false), "use&nbsp;dhcp");
		this.addField(new MagicTextField("ip4address", /^\d+\.\d+\.\d+\.\d+\/\d+$/, ""), "ip/prefix");		
	}
});

var ConnectionForm = AttributeForm.extend({});

var EmulatedConnectionForm = ConnectionForm.extend({
	init: function(obj) {
		this._super(obj);
		this.addField(new MagicTextField("bandwidth", /^\d+$/, "10000"), "bandwidth&nbsp;(in&nbsp;kb/s)");
		this.addField(new MagicTextField("latency", /^\d+$/, "0"), "latency&nbsp;(in&nbsp;ms)");
		this.addField(new MagicTextField("loss", /^\d+\.\d+$/, "0.0"), "packet&nbsp;loss");
		this.addField(new CheckField("capture", false), "capture&nbsp;packets");
	}
});

var EmulatedRouterConnectionForm = EmulatedConnectionForm.extend({
	init: function(obj) {
		this._super(obj);
		this.addField(new MagicTextField("gateway", /^\d+\.\d+\.\d+\.\d+\/\d+$/, ""), "gateway&nbsp;(ip/prefix)");	}
});