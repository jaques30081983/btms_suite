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

#from plyer import notification

from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from functools import partial
import hashlib
import datetime as dt
import json

from collections import namedtuple
from kivy.properties import ObjectProperty, ListProperty, BooleanProperty, NumericProperty
from jnius import autoclass, PythonJavaClass, java_method, cast
from android.runnable import run_on_ui_thread
from kivy.network.urlrequest import UrlRequest
from functools import partial
from kivy.uix.widget import Widget

# preload java classes
System = autoclass('java.lang.System')
System.loadLibrary('iconv')
PythonActivity = autoclass('org.renpy.android.PythonActivity')
Camera = autoclass('android.hardware.Camera')
ParametersCam = autoclass('android.hardware.Camera$Parameters')

ImageScanner = autoclass('net.sourceforge.zbar.ImageScanner')
Config = autoclass('net.sourceforge.zbar.Config')
SurfaceView = autoclass('android.view.SurfaceView')
LayoutParams = autoclass('android.view.ViewGroup$LayoutParams')
Image = autoclass('net.sourceforge.zbar.Image')
ImageFormat = autoclass('android.graphics.ImageFormat')
LinearLayout = autoclass('android.widget.LinearLayout')
Symbol = autoclass('net.sourceforge.zbar.Symbol')




class PreviewCallback(PythonJavaClass):
    '''Interface used to get back the preview frame of the Android Camera
    '''
    __javainterfaces__ = ('android.hardware.Camera$PreviewCallback', )

    def __init__(self, callback):
        super(PreviewCallback, self).__init__()
        self.callback = callback

    @java_method('([BLandroid/hardware/Camera;)V')
    def onPreviewFrame(self, data, camera):
        self.callback(camera, data)


class SurfaceHolderCallback(PythonJavaClass):
    '''Interface used to know exactly when the Surface used for the Android
    Camera will be created and changed.
    '''

    __javainterfaces__ = ('android.view.SurfaceHolder$Callback', )

    def __init__(self, callback):
        super(SurfaceHolderCallback, self).__init__()
        self.callback = callback

    @java_method('(Landroid/view/SurfaceHolder;III)V')
    def surfaceChanged(self, surface, fmt, width, height):
        self.callback(fmt, width, height)

    @java_method('(Landroid/view/SurfaceHolder;)V')
    def surfaceCreated(self, surface):
        pass

    @java_method('(Landroid/view/SurfaceHolder;)V')
    def surfaceDestroyed(self, surface):
        pass


class AndroidWidgetHolder(Widget):
    '''Act as a placeholder for an Android widget.
    It will automatically add / remove the android view depending if the widget
    view is set or not. The android view will act as an overlay, so any graphics
    instruction in this area will be covered by the overlay.
    '''

    view = ObjectProperty(allownone=True)
    '''Must be an Android View
    '''

    def __init__(self, **kwargs):
        self._old_view = None
        from kivy.core.window import Window
        self._window = Window
        kwargs['size_hint'] = (None, None)
        super(AndroidWidgetHolder, self).__init__(**kwargs)

    def on_view(self, instance, view):
        if self._old_view is not None:
            layout = cast(LinearLayout, self._old_view.getParent())
            layout.removeView(self._old_view)
            self._old_view = None

        if view is None:
            return

        activity = PythonActivity.mActivity
        activity.addContentView(view, LayoutParams(*self.size))
        view.setZOrderOnTop(True)
        view.setX(self.x)
        view.setY(self._window.height - self.y - self.height)
        self._old_view = view

    def on_size(self, instance, size):
        if self.view:
            params = self.view.getLayoutParams()
            params.width = self.width
            params.height = self.height
            self.view.setLayoutParams(params)
            self.view.setY(self._window.height - self.y - self.height)

    def on_x(self, instance, x):
        if self.view:
            self.view.setX(x)

    def on_y(self, instance, y):
        if self.view:
            self.view.setY(self._window.height - self.y - self.height)


class AndroidCamera(Widget):
    '''Widget for controling an Android Camera.
    '''

    index = NumericProperty(0)

    __events__ = ('on_preview_frame', )

    def __init__(self, **kwargs):
        self._holder = None
        self._android_camera = None
        super(AndroidCamera, self).__init__(**kwargs)
        self._holder = AndroidWidgetHolder(size=self.size, pos=self.pos)
        self.add_widget(self._holder)

    @run_on_ui_thread
    def stop(self):
        if self._android_camera is None:
            return
        self._android_camera.setPreviewCallback(None)
        self._android_camera.release()
        self._android_camera = None
        self._holder.view = None

    @run_on_ui_thread
    def start(self):
        if self._android_camera is not None:
            return

        self._android_camera = Camera.open(self.index)

        # create a fake surfaceview to get the previewCallback working.
        self._android_surface = SurfaceView(PythonActivity.mActivity)
        surface_holder = self._android_surface.getHolder()

        # create our own surface holder to correctly call the next method when
        # the surface is ready
        self._android_surface_cb = SurfaceHolderCallback(self._on_surface_changed)
        surface_holder.addCallback(self._android_surface_cb)

        # attach the android surfaceview to our android widget holder
        self._holder.view = self._android_surface

    def _on_surface_changed(self, fmt, width, height):
        # internal, called when the android SurfaceView is ready
        # FIXME if the size is not handled by the camera, it will failed.
        global lampstate

        params = self._android_camera.getParameters()
        params.setPreviewSize(width, height)
        params.setFocusMode(ParametersCam.FOCUS_MODE_CONTINUOUS_PICTURE)

        if lampstate == 1:
            params.setFlashMode(ParametersCam.FLASH_MODE_TORCH)


        self._android_camera.setParameters(params)
        self._android_camera.setDisplayOrientation(90)

        # now that we know the camera size, we'll create 2 buffers for faster
        # result (using Callback buffer approach, as described in Camera android
        # documentation)
        # it also reduce the GC collection
        bpp = ImageFormat.getBitsPerPixel(params.getPreviewFormat()) / 8.
        buf = '\x00' * int(width * height * bpp)
        self._android_camera.addCallbackBuffer(buf)
        self._android_camera.addCallbackBuffer(buf)

        # create a PreviewCallback to get back the onPreviewFrame into python
        self._previewCallback = PreviewCallback(self._on_preview_frame)

        # connect everything and start the preview
        self._android_camera.setPreviewCallbackWithBuffer(self._previewCallback);
        self._android_camera.setPreviewDisplay(self._android_surface.getHolder())
        self._android_camera.startPreview();

    def _on_preview_frame(self, camera, data):
        # internal, called by the PreviewCallback when onPreviewFrame is
        # received
        self.dispatch('on_preview_frame', camera, data)
        # reintroduce the data buffer into the queue
        self._android_camera.addCallbackBuffer(data)

    def on_preview_frame(self, camera, data):
        pass

    def on_size(self, instance, size):
        if self._holder:
            self._holder.size = size

    def on_pos(self, instance, pos):
        if self._holder:
            self._holder.pos = pos


class BtmsValidWampComponentAuth(ApplicationSession):
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
        #self.subscribe(ui.on_users_message, u'io.crossbar.btms.users.result')
        self.subscribe(ui.on_venue_update, u'io.crossbar.btms.venue.update')
        self.subscribe(ui.on_block_item, u'io.crossbar.btms.item.block.action')
        self.subscribe(ui.on_select_seats, u'io.crossbar.btms.seats.select.action')
        self.subscribe(ui.on_set_unnumbered_seats, u'io.crossbar.btms.unnumbered_seats.set.action')
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


class BtmsValidRoot(BoxLayout):
    """
    The Root widget, defined in conjunction with the rule in btms.kv.
    """
    seat_stat_img = ('images/bet_sitz_30px_01.png', 'images/bet_sitz_30px_02.png', 'images/bet_sitz_30px_03.png', 'images/bet_sitz_30px_04.png', 'images/bet_sitz_30px_05.png')

    global lampstate
    lampstate = 0
    camera_size = ListProperty([720, 720])

    symbols = ListProperty([])

    # XXX can't work now, due to overlay.
    show_bounds = BooleanProperty(False)

    Qrcode = namedtuple('Qrcode',
            ['type', 'data', 'bounds', 'quality', 'count'])

    #def __init__(self, **kwargs):
        #super(ZbarQrcodeDetector, self).__init__(**kwargs)






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
        runner.run(BtmsValidWampComponentAuth, start_reactor=False)

    @inlineCallbacks
    def on_session(self, session):
        """
        Called from WAMP session when attached to Crossbar router.
        """
        self.session = session
        self.ids.sm.current = 'work1'

        results = yield self.session.call(u'io.crossbar.btms.users.get')
        self.get_users(results)

        self.ids.kv_user_button.text = btms_user
        for row in results:
            if row['user'] == btms_user: #TODO simply btms_user to user
                self.user_id = row['id']
                self.user = btms_user

        #self.session.leave()


        #Init Camera
        self._camera = AndroidCamera(
                size=self.camera_size,
                size_hint=(None,None),pos_hint={'x': .25, 'y': .5}, width=50)

        self._camera.bind(on_preview_frame=self._detect_qrcode_frame)
        self.ids.detector.add_widget(self._camera)
        self.qr_result = '0'
        self._lamp = 0

        # create a scanner used for detecting qrcode
        self._scanner = ImageScanner()
        self._scanner.setConfig(0, Config.ENABLE, 1)
        self._scanner.setConfig(Symbol.QRCODE, Config.ENABLE, 1)
        self._scanner.setConfig(0, Config.X_DENSITY, 3)
        self._scanner.setConfig(0, Config.Y_DENSITY, 3)


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
            self.ids.kv_user_list.add_widget(Button(text=str(row['user']),on_release=partial(self.change_user,str(row['user']))))

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



    def toggle_lamp(self):
        global lampstate
        if self._lamp == 1:
            self._lamp = 0
            self.ids.lamp_btn.text = 'Lamp Off'
            lampstate = 0

        elif self._lamp == 0:
            self._lamp = 1
            self.ids.lamp_btn.text = 'Lamp On'
            lampstate = 1


    def start(self):
        self._camera.start()

    def stop(self):
        self._camera.stop()

    def _detect_qrcode_frame(self, instance, camera, data):
        global data_qr
        # the image we got by default from a camera is using the NV21 format
        # zbar only allow Y800/GREY image, so we first need to convert,
        # then start the detection on the image
        parameters = camera.getParameters()
        size = parameters.getPreviewSize()
        barcode = Image(size.width, size.height, 'NV21')
        barcode.setData(data)
        barcode = barcode.convert('Y800')

        result = self._scanner.scanImage(barcode)

        if result == 0:
            self.symbols = []
            return

        # we detected qrcode! extract and dispatch them
        symbols = []
        it = barcode.getSymbols().iterator()
        while it.hasNext():
            symbol = it.next()
            qrcode = BtmsValidRoot.Qrcode(
                type=symbol.getType(),
                data=symbol.getData(),
                quality=symbol.getQuality(),
                count=symbol.getCount(),
                bounds=symbol.getBounds())
            symbols.append(qrcode)

            data_qr = symbol.getData()
            #self.ids.result_label.text = data_qr
            self.validate()
        self.symbols = symbols

    @inlineCallbacks
    def validate(self):
        global data_qr
        global data_qr_old

        try:
            data_qr_old
        except NameError:
            data_qr_old = 0



        def result_validation(status):

            if status == 0:
                status_text = 'Is valid ' + str(data_qr)
                self.ids.result_label.background_color = [0,1,0,1]
                self.ids.result_screen.background_color = [0,1,0,1]
            elif status == 1:
                status_text = 'Not valid ' + str(data_qr)
                self.ids.result_label.background_color = [1,0,0,1]
                self.ids.result_screen.background_color = [1,0,0,1]
            elif status == 2:
                status_text = 'Back to the office ' + str(data_qr)
                self.ids.result_label.background_color = [1,1,0,1]
                self.ids.result_screen.background_color = [1,1,0,1]
            elif status == 3:
                status_text = 'Valid VIP ' + str(data_qr)
                self.ids.result_label.background_color = [0,1,0,1]
                self.ids.result_screen.background_color = [0,1,0,1]
            elif status == 4:
                status_text = 'Not valid VIP ' + str(data_qr)
                self.ids.result_label.background_color = [1,0,0,1]
                self.ids.result_screen.background_color = [1,0,0,1]
            elif status == 5:
                status_text = 'Not in DB, not valid ' + str(data_qr)
                self.ids.result_label.background_color = [1,0,0,1]
                self.ids.result_screen.background_color = [1,0,0,1]

            self.ids.result_label.text = status_text

            def my_callback(dt):
                self.ids.result_screen.background_color = [1,1,1,1]
            Clock.schedule_once(my_callback, .5)

        if len(data_qr) > 19:

            if data_qr == data_qr_old:
                pass
            else:

                data_qr_old = data_qr
                #working_server_adress = self.ids.kv_server_adress.text
                #session_id = '0'


                try:
                    results = yield self.session.call(u'io.crossbar.btms.valid.validate',data_qr,self.user_id)
                    result_validation(results)
                    #self.ids.result_label.text = str(results)

                except Exception as err:
                    print "Error", err

                #req = UrlRequest(
                #        'http://' + working_server_adress + '/btms_backoffice/index.php?s=' + session_id + '&b=valid_ticket&tidid='
                #        + data_qr, result_validation)


	def on_symbol(self, symbols):
#		#print 'found', len(symbols), 'symbols'
		for symbol in symbols:
			self.qr_result= '- qrcode: {}'.format(symbol.data)


		# stop the detector if we found a symbol.
		# don't if you want continuous detection.
		#detector.stop()

#	detector = ZbarQrcodeDetector()
	#self.bind(symbols=on_symbols)


	'''
    # can't work, due to the overlay.
    def on_symbols(self, instance, value):
        if self.show_bounds:
            self.update_bounds()

    def update_bounds(self):
        self.canvas.after.remove_group('bounds')
        if not self.symbols:
            return
        with self.canvas.after:
            Color(1, 0, 0, group='bounds')
            for symbol in self.symbols:
                x, y, w, h = symbol.bounds
                x = self._camera.right - x - w
                y = self._camera.top - y - h
                Line(rectangle=[x, y, w, h], group='bounds')
    '''





class BtmsValidApp(App):

    def build(self):
        self.title = 'BTMS Valid 16.02a'
        self.root = BtmsValidRoot()
        self.root.ids.kv_user_change.disabled = True

        if store.exists('settings'):
            self.root.ids.kv_server_adress.text = store.get('settings')['server_adress']
            self.root.ids.kv_user_input.text = store.get('settings')['user']
            L = store.get('userlist')['user_list']
            self.root.ids.kv_user_change.disabled = False
            for user in L:
                self.root.ids.kv_user_list.add_widget(Button(text=user,on_release=partial(self.root.change_user,user)))


        #self.start_wamp_component()

        return self.root



    def on_pause(self):
        self.root.stop() #Stop Camera
        return True

    def on_resume(self):
        pass

if __name__ == '__main__':
    BtmsValidApp().run()
