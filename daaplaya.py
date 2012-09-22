# -*- coding: utf-8 -*-
import gobject
gobject.threads_init()
import gtk
gtk.gdk.threads_init()
import dbus
import dbus.glib # Remove this and things stop working
import avahi
from daap import DAAPClient
import gst
import thread
import time

        
def update_servers_list():
    """ Updates server store """
    servers = ui_state['servers']
    server_names = servers.keys()
    ui_state['server_store'].clear()
    for key in server_names:
        ui_state['server_store'].append((key, ui_state['servers'][key]))

def _get_playlists(key):
    """ Returns all playlist objects of the first database of 
        server with id in param key """
    client = DAAPClient()
    server = ui_state['servers'][key]['address']
    port = ui_state['servers'][key]['port']
    client.connect(server, port)
    session = client.login()
    database = session.databases()[0]
    playlists = database.playlists()
    return playlists
    
def update_playlists_list(key):
    """ Sets playlists store to current set of playlists of
        the first database of server with id in param key """
    playlists = _get_playlists(key)
    ui_state['selected server'] = key
    print "%s playlists in the selected database." % len(playlists)
    ui_state['playlists_store'].clear()
    for p in sorted(playlists, key = lambda pl:repr(pl.name).lower()[2:]):
        print "%s: %s"%(p.id, repr(p.name))
        name = p.name
        ui_state['playlists_store'].append((name ,p.id))
        
def update_playlist_list(key):
    """Sets tracks store to tracks of selected playlist with id in param key"""
    playlists = _get_playlists(ui_state['selected server'])
    for p in playlists:
        if str(p.id) == str(key):
            print "using playlist '%s'"%repr(p.name)
            tracks = p.tracks()
            print "Got %s tracks"%len(tracks)
            ui_state['tracks_store'].clear()
            ui_state['track_objects'] = []
            for track in p.tracks():
                ui_state['tracks_store'].append((track.name[0:80], track.id)) # Avoid song names crowding out other fields
                ui_state['track_objects'].append(track)
            return
    
def new_service(interface, protocol, name, type, domain, flags):
    interface, protocol, name, type, domain, host, aprotocol, address, port, txt, flags = server.ResolveService(interface, protocol, name, type, domain, avahi.PROTO_UNSPEC, dbus.UInt32(0))
    key = "%s" % (name,)
    print "Found service '%s' of type '%s' in domain '%s' at address '%s:%s'" % (name, type, domain, address, port)
    ui_state['servers'][key] = {'name':name, 'address':address, 'port':port}
    update_servers_list()
    
def remove_service(interface, protocol, name, type, domain):
    key = "%s" % (name,)
    if ui_state['servers'].has_key(key):
        del ui_state['servers'][key]
    print "Service '%s' of type '%s' in domain '%s' disappeared." % (name, type, domain)
    update_servers_list()

def server_selected(one, col, three):
    """Executed when user single clicks on a line in the server list,
       displays its playlists"""
    #import pdb;pdb.set_trace()
    path = one.get_path_at_pos(int(col.x), int(col.y))[0]
    iterator = one.get_selection().get_selected_rows()[0].get_iter(path)
    store  = one.get_selection().get_selected_rows()[0]
    value = store.get_value(iterator, 0)
    print "Server %s SELECTED" % value
    update_playlists_list(value)

def playlist_selected(one, col, three):
    """Executed when user single clicks on a line in the playlists list,
       displays its tracks"""
    path = one.get_path_at_pos(int(col.x), int(col.y))[0]
    iterator = one.get_selection().get_selected_rows()[0].get_iter(path)
    store  = one.get_selection().get_selected_rows()[0]
    value = store.get_value(iterator, 1)
    print "Playlist %s SELECTED" % value
    update_playlist_list(value)
    
def track_selected(one, path, three, four):
    """Executed when user double clicks on a line in the tracks list,
       plays the track"""
    selected_row = one.get_selection().get_selected_rows()[0]
    iterator = one.get_selection().get_selected_rows()[0].get_iter(path)
    store  = one.get_selection().get_selected_rows()[0]
    value = store.get_value(iterator, 1)
    print "Song %s SELECTED" % value
    play(value)

def _get_track_from_playlist(track_id):
    print "getting track %s from playlist" % track_id

    tracks = ui_state['track_objects']
    for t in tracks:
        if str(t.id) == track_id:
            print "got track %s from playlist" % track_id
            return t    
    return None
    
def _get_subsequent_track_id_from_playlist(track_id):
    tracks = ui_state['track_objects']
    current_track_found = False
    for t in tracks:
        if current_track_found:
            return t.id
        if str(t.id) == track_id:
            current_track_found = True
    return None
    
def _get_preceding_track_id_from_playlist(track_id):
    tracks = ui_state['track_objects']
    current_track_found = False
    track = None
    for t in tracks:
        if str(t.id) == track_id and track:
            return track.id
        track = t
    return None
    
def convert_ns(t):
    s,ns = divmod(t, 1000000000)
    m,s = divmod(s, 60)

    if m < 60:
        return "%02i:%02i" %(m,s)
    else:
        h,m = divmod(m, 60)
        return "%i:%02i:%02i" %(h,m,s)

def play_thread():
    """Shows where you are in the song"""
    play_thread_id = ui_state['play_thread_id']
    gtk.gdk.threads_enter()
    ui_state['time_label'].set_text("00:00 / 00:00")
    gtk.gdk.threads_leave()
    print "in play thread"
    while play_thread_id == ui_state['play_thread_id']:
        try:
            time.sleep(0.2)
            dur_int = ui_state['player'].query_duration(gst.FORMAT_TIME, None)[0]
            if dur_int == -1:
                continue
            dur_str = convert_ns(dur_int)
            gtk.gdk.threads_enter()
            ui_state['time_label'].set_text("00:00 / " + dur_str)
            gtk.gdk.threads_leave()
            break
        except gst.QueryError:
            print "query error in time stuff"
            pass
            
    time.sleep(0.2)
    while play_thread_id == ui_state['play_thread_id']:
        pos_int = ui_state['player'].query_position(gst.FORMAT_TIME, None)[0]
        pos_str = convert_ns(pos_int)
        if play_thread_id == ui_state['play_thread_id']:
            gtk.gdk.threads_enter()
            ui_state['time_label'].set_text(pos_str + " / " + dur_str)
            gtk.gdk.threads_leave()
        time.sleep(1)

def play(track_id):
    """ Plays a track, fetches it over http. Assumes no authentication """
    print "preparing to play track %s" % track_id
    ui_state['play_button'].set_label('- -')
    ui_state['current_track_id'] = track_id
    tracks = ui_state['track_objects']
    t = _get_track_from_playlist(track_id)
    print "in play: track object retrieved with id %s" % track_id
    if not t:
        print "Got no track with id %s" % track_id
        return
    ui_state['track_label'].set_label("%s %s" %(t.artist, t.name))
    filename = "song.mp3"
    print "fetching over track with id %s" % track_id
    download_url = 'http://%s:%s' % (t.database.session.connection.hostname, t.database.session.connection.port)
    download_url += "/databases/%s/items/%s.%s"%(t.database.id, t.id, t.type)
    player = gst.element_factory_make("playbin2", "player")
    fakesink = gst.element_factory_make("fakesink", "fakesink")
    player.set_property("video-sink", fakesink)
    player.connect("about-to-finish", load_next_from_playlist)
    ui_state['player'].set_state(gst.STATE_NULL)
    ui_state['player'] = player
    player.set_property("uri", download_url)
    player.set_state(gst.STATE_PLAYING)
    ui_state['play_thread_id'] = thread.start_new_thread(play_thread, ())
    ui_state['play_button'].set_label('| |')
    ui_state['time_label'].set_text("00:00 / 00:00")


def pause():
    player = ui_state['player']
    player.set_state(gst.STATE_PAUSED)

def resume_play():
    player = ui_state['player']
    player.set_state(gst.STATE_PLAYING)
    
def play_pause_action(*arg):
    """Toggle play/pause function"""
    label = ui_state['play_button'].get_label()
    if label == ">":
        resume_play()
        ui_state['play_button'].set_label('| |')
    elif label == '| |':
        pause()
        ui_state['play_button'].set_label('>')
    
def load_next_from_playlist(*args,**kw):
    current_track_id = ui_state['current_track_id']
    if current_track_id:
        next_track_id = _get_subsequent_track_id_from_playlist(current_track_id)
        if next_track_id:
            play(str(next_track_id))
        else:
            player = ui_state['player']
            player.set_state(gst.STATE_NULL)
            
def load_previous_from_playlist(*args,**kw):
    current_track_id = ui_state['current_track_id']
    if current_track_id:
        previous_track_id = _get_preceding_track_id_from_playlist(current_track_id)
        if previous_track_id:
            play(str(previous_track_id))
        else:
            player = ui_state['player']
            player.set_state(gst.STATE_NULL)
            
def destroy(*args,**kw):
    """ Quits program """
    player = ui_state['player']
    player.set_state(gst.STATE_NULL)
    gtk.main_quit()
    
# Make gstreamer player with no video
player = gst.element_factory_make("playbin2", "player")
fakesink = gst.element_factory_make("fakesink", "fakesink")
player.set_property("video-sink", fakesink)
player.connect("about-to-finish", load_next_from_playlist)

# ui_state is a central place to store and look up what state the player is in
ui_state = {
            'servers':{},
            'server_store':gtk.ListStore(str, str),
            'selected server':None,
            'playlists_store':gtk.ListStore(str, str),
            'tracks_store':gtk.ListStore(str, str),
            'track_objects' : [],
            'current_track_id':None,
            'player':player,
            'play_button':None,
}
    
# Create a window
w = gtk.Window()
# Add shortcuts for media center remote control
accel_group = gtk.AccelGroup()
accel_group.connect_group(ord('P'), gtk.gdk.CONTROL_MASK,
gtk.ACCEL_LOCKED, play_pause_action) 
accel_group.connect_group(ord('F'), gtk.gdk.CONTROL_MASK,
gtk.ACCEL_LOCKED, load_next_from_playlist)
accel_group.connect_group(ord('B'), gtk.gdk.CONTROL_MASK,
gtk.ACCEL_LOCKED, load_previous_from_playlist)
w.add_accel_group(accel_group)
# shift ctrl -T red button, next database, ctrl - E green button, next playlist, ctrl - i, yellow button
w.set_size_request(800, 300)
w.set_title('Daap playlist player')

# Quit application when this window is closed
w.connect('destroy', destroy)
vbox = gtk.VBox(homogeneous=False, spacing=0)
hbox = gtk.HBox(homogeneous=False, spacing=2)

servers_treeview = gtk.TreeView(model=None)
servers_treeview.set_size_request(100, -1) # does not seem to have any effect
servers_treeview.set_model(model=ui_state['server_store'])
servers_treeviewcolumn = gtk.TreeViewColumn('Servers', gtk.CellRendererText(), text=0)
servers_treeview.append_column(servers_treeviewcolumn)
servers_treeview.connect("button-press-event", server_selected, servers_treeview)
hbox.pack_start(servers_treeview)

sw = gtk.ScrolledWindow()
sw.set_size_request(100, -1) # does not seem to have any effect
sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
playlists_treeview = gtk.TreeView(model=None)
playlists_treeview.set_model(model=ui_state['playlists_store'])
playlists_treeviewcolumn = gtk.TreeViewColumn('Playlists', gtk.CellRendererText(), text=0)
playlists_treeview.append_column(playlists_treeviewcolumn)
playlists_treeview.connect("button-press-event", playlist_selected, playlists_treeview)
sw.add(playlists_treeview)
hbox.pack_start(sw)

sw = gtk.ScrolledWindow()
sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
tracks_treeview = gtk.TreeView(model=None)
tracks_treeview.set_model(model=ui_state['tracks_store'])
tracks_treeviewcolumn = gtk.TreeViewColumn('Songs', gtk.CellRendererText(), text=0)
tracks_treeview.append_column(tracks_treeviewcolumn)
tracks_treeview.connect("row-activated", track_selected, tracks_treeview)
sw.add(tracks_treeview)
hbox.pack_start(sw)

vbox.pack_start(hbox)
# Make lower pane for controls and status
lower_hbox =  gtk.HBox(homogeneous=False, spacing=2)

prev_button = gtk.Button('<<')
prev_button.connect("clicked", load_previous_from_playlist, prev_button)
pause_button = gtk.Button('- -')
pause_button.connect("clicked", play_pause_action, pause_button)
ui_state['play_button'] = pause_button

next_button = gtk.Button('>>')
next_button.connect("clicked", load_next_from_playlist, next_button)
lower_hbox.pack_end(next_button,expand =False, fill =False)
lower_hbox.pack_end(pause_button,expand =False, fill =False)
lower_hbox.pack_end(prev_button,expand =False, fill =False)
label = gtk.Label('(No song playing)')
ui_state['track_label'] = label
lower_hbox.pack_end(label,expand =False, fill =False)
time_label = gtk.Label()
time_label.set_text("00:00 / 00:00")
lower_hbox.add(time_label)
ui_state['time_label'] = time_label

vbox.pack_start(lower_hbox,expand =False, fill =False)

# wrap it up and display the player
w.add(vbox)
w.show_all()

# Find all Daap servers on the local subnet
bus = dbus.SystemBus()
server = dbus.Interface(bus.get_object(avahi.DBUS_NAME, avahi.DBUS_PATH_SERVER), avahi.DBUS_INTERFACE_SERVER)
stype = '_daap._tcp'
domain = 'local'
browser = dbus.Interface(bus.get_object(avahi.DBUS_NAME, server.ServiceBrowserNew(avahi.IF_UNSPEC, avahi.PROTO_UNSPEC, stype, domain, dbus.UInt32(0))), avahi.DBUS_INTERFACE_SERVICE_BROWSER)
browser.connect_to_signal('ItemNew', new_service)
browser.connect_to_signal('ItemRemove', remove_service)

# Start event loop
gtk.main()

