# -*- coding: iso-8859-15 -*-
"""
This is BTMS, Bigwood Ticket Management System,
just reserve, sell and print tickets....
"""

# copyright Jakob Laemmle, the GNU GENERAL PUBLIC LICENSE Version 2 license applies

# Kivy's install_twisted_reactor MUST be called early on!

from kivy.support import install_twisted_reactor
install_twisted_reactor()

from kivy.app import App
from kivy.clock import Clock
#from kivy.factory import Factory
#from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ListProperty
from autobahn.twisted.wamp import ApplicationSession
from autobahn.twisted.wamp import ApplicationRunner
from autobahn.wamp import auth
from twisted.internet.defer import inlineCallbacks, returnValue
#from twisted.internet import defer
#import msgpack
from kivy.storage.jsonstore import JsonStore
store = JsonStore('btms_config.json')
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.bubble import Bubble
from kivy.metrics import dp
from kivy.core.audio import SoundLoader

#from plyer import notification

from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from functools import partial
import hashlib
import datetime as dt
import json

from kivy.properties import ObjectProperty, ListProperty, BooleanProperty, NumericProperty
from functools import partial
from kivy.uix.widget import Widget






class BtmsPosDispWampComponentAuth(ApplicationSession):
    """
    A WAMP application component which is run from the Kivy UI.
    """

    def onConnect(self):
        print("connected. joining realm {} as user {} ...".format(self.config.realm, btms_user))

        self.join(self.config.realm, [u"wampcra"], btms_user)

    def onChallenge(self, challenge):

        print("authentication challenge received: {}".format(challenge))
        if challenge.method == u"wampcra":
            if u'salt' in challenge.extra:
                key = auth.derive_key(btms_password.text.encode('utf8'),
                    challenge.extra['salt'].encode('utf8'),
                    challenge.extra.get('iterations', None),
                    challenge.extra.get('keylen', None))
            else:
                key = btms_password.encode('utf8')
            signature = auth.compute_wcs(key, challenge.extra['challenge'].encode('utf8'))
            return signature.decode('ascii')
        else:
            raise Exception("don't know how to compute challenge for authmethod {}".format(challenge.method))

    def onJoin(self, details):
        print("auth session ready", self.config.extra)
        global ui
        # get the Kivy UI component this session was started from
        ui = self.config.extra['ui']
        ui.on_session(self)



        # subscribe to WAMP PubSub events and call the Kivy UI component's
        # function when such an event is received

        self.subscribe(ui.on_msg, u'io.crossbar.btms.pos.displays.msg.send')
        self.subscribe(ui.onLeaveRemote, u'io.crossbar.btms.onLeaveRemote')


    def onLeave(self, details):
        print("onLeave: {}".format(details))

        if ui.logout_op == 0 or ui.logout_op == None:
            ui.ids.sm.current = 'server_connect'
            ui.ids.kv_user_log.text = ui.ids.kv_user_log.text + '\n' + ("onLeave: {}".format(details))
        elif ui.logout_op == 1:
            ui.ids.sm.current = 'login_user'

    def onDisconnect(self):
        details = ""

        print("onDisconnect: {}".format(details))
        if ui.logout_op == 0 or ui.logout_op == None:
            ui.ids.sm.current = 'server_connect'
            ui.ids.kv_user_log.text = ui.ids.kv_user_log.text + '\n' + ("onDisconnect: {}".format(details))
        elif ui.logout_op == 1:
            ui.ids.sm.current = 'login_user'


class BtmsPosDispRoot(BoxLayout):
    """
    The Root widget, defined in conjunction with the rule in btms.kv.
    """
    seat_stat_img = ('images/bet_sitz_30px_01.png', 'images/bet_sitz_30px_02.png', 'images/bet_sitz_30px_03.png', 'images/bet_sitz_30px_04.png', 'images/bet_sitz_30px_05.png')

    def start_wamp_component_auth(self, server_url, user, password):
        global btms_user
        global btms_password
        btms_user = user
        btms_password = hashlib.md5( password ).hexdigest()
        self.logout_op = 0
        """
        Create a WAMP session and start the WAMP component
        """
        self.session = None

        # adapt to fit the Crossbar.io instance you're using

        url, realm = u"ws://"+server_url+"/ws", u"btmsserverauth"
        store.put('settings', server_adress=server_url, ssl='0', user=user)
        # Create our WAMP application component
        runner = ApplicationRunner(url=url,
                                   realm=realm,
                                   extra=dict(ui=self))

        # Start our WAMP application component without starting the reactor because
        # that was already started by kivy
        runner.run(BtmsPosDispWampComponentAuth, start_reactor=False)

    @inlineCallbacks
    def on_session(self, session):
        """
        Called from WAMP session when attached to Crossbar router.
        """
        self.session = session
        self.ids.sm.current = 'work1'
        self.camera_state = 0

        results = yield self.session.call(u'io.crossbar.btms.users.get')
        self.get_users(results)

        self.ids.kv_user_button.text = btms_user
        for row in results:
            if row['user'] == btms_user: #TODO simply btms_user to user
                self.user_id = row['id']
                self.user = btms_user

        #Register display on server
        if self.ids.kv_pos_display_input.text == '':
            self.ids.kv_pos_display_input.text = 'noname'

        self.pos_display = self.ids.kv_pos_display_input.text

        self.session.call(u'io.crossbar.btms.pos.displays.reg', self.pos_display,'')

        #self.session.leave()



    def onLeaveRemote(self,details):
        ui.ids.kv_user_log.text = ui.ids.kv_user_log.text + '\n' + ("onLeaveRemote: {}".format(details))
        print details
        self.session.leave()

    def get_users(self,results):
        user_list1 = []
        self.user_list = {}
        self.ids.kv_user_list.clear_widgets(children=None)
        for row in results:
            print row['user']
            self.user_list[row['id']] = row['user']
            user_list1.append(row['user'])
            self.ids.kv_user_list.add_widget(Button(text=str(row['user']), on_release=partial(self.change_user,str(row['user'])),size_hint=[1, None], height=dp(60)))
        self.ids.kv_user_list.bind(minimum_height=self.ids.kv_user_list.setter('height'))
        store.put('userlist', user_list=user_list1)


    def change_user(self,user,*args):
        self.ids.kv_password_input.text = ''
        self.ids.kv_user_input.text = user

        self.ids.sm.current = 'server_connect'


    def logout(self,op):
        self.logout_op = op
        self.ids.kv_password_input.text = ''
        self.ids.kv_user_change.disabled = False
        self.session.leave()

        #self.ids.sm.current = 'login_user'

    def on_msg(self,display, msg):
        print display, msg

        if display == self.pos_display:
            self.ids.result_screen_money.text = str(msg['total_price']) + unichr(8364)
            self.ids.result_screen_info.text = msg['info']

    def set_pos_display(self, *args):
        self.session.call(u'io.crossbar.btms.pos.displays.reg', self.ids.kv_pos_display_input.text, self.pos_display)
        self.pos_display = self.ids.kv_pos_display_input.text
        store.put('displays',display=self.pos_display)

class BtmsPosDispApp(App):

    def build(self):
        self.title = 'BTMS Pos Display 16.04a'
        self.root = BtmsPosDispRoot()
        #self.root.ids.kv_user_change.disabled = True

        if store.exists('settings'):
            self.root.ids.kv_server_adress.text = store.get('settings')['server_adress']
            self.root.ids.kv_user_input.text = store.get('settings')['user']
            L = store.get('userlist')['user_list']
            self.root.ids.kv_user_change.disabled = False
            for user in L:
                self.root.ids.kv_user_list.add_widget(Button(text=user, on_release=partial(self.root.change_user,user),size_hint=[1, None], height=dp(40)))
            self.root.ids.kv_user_list.bind(minimum_height=self.root.ids.kv_user_list.setter('height'))

        if store.exists('displays'):
            self.root.ids.kv_pos_display_input.text = store.get('displays')['display']

        #self.start_wamp_component()

        return self.root



    #def on_pause(self):
        #self.root.stop() #Stop Camera
        #return True

    #def on_resume(self):
        #self.root.stop() #Stop Camera
    #TODO Pause and Resume not working if Camera is running

if __name__ == '__main__':
    BtmsPosDispApp().run()
