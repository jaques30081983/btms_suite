# -*- coding: iso-8859-15 -*-
"""
This is BTMS, Bigwood Ticket Management System,
just reserve, sell and print tickets....
"""

# copyright Jakob Laemmle, the Apache 2.0 license applies

# Kivy's install_twisted_reactor MUST be called early on!

from kivy.support import install_twisted_reactor
install_twisted_reactor()

from kivy.app import App
#from kivy.factory import Factory
#from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from autobahn.twisted.wamp import ApplicationSession
from autobahn.twisted.wamp import ApplicationRunner
from autobahn.wamp import auth
from twisted.internet.defer import inlineCallbacks
from twisted.internet import defer
from kivy.storage.jsonstore import JsonStore
store = JsonStore('btms_config.json')
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.bubble import Bubble

from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from functools import partial
import hashlib

class BtmsWampComponent(ApplicationSession):
    """
    A WAMP application component which is run from the Kivy UI.
    """

    def onJoin(self, details):
        print("session ready", self.config.extra)

        # get the Kivy UI component this session was started from
        ui = self.config.extra['ui']
        ui.on_session(self)

        # subscribe to WAMP PubSub events and call the Kivy UI component's
        # function when such an event is received
        self.subscribe(ui.on_users_message, u'io.crossbar.btms.users.result')


    def onLeave(self, details):
        print("onLeave: {}".format(details))
        self.disconnect()


class BtmsWampComponentAuth(ApplicationSession):
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


    def onLeave(self, details):
        print("onLeave: {}".format(details))
        if ui.logout_op == 0 or ui.logout_op == None:
            ui.ids.sm.current = 'server_connect'
        elif ui.logout_op == 1:
            ui.ids.sm.current = 'login_user'


class BtmsRoot(BoxLayout):
    """
    The Root widget, defined in conjunction with the rule in btms.kv.
    """
    global seat_stat_img
    seat_stat_img = ('images/bet_sitz_30px_01.png', 'images/bet_sitz_30px_02.png', 'images/bet_sitz_30px_03.png', 'images/bet_sitz_30px_04.png', 'images/bet_sitz_30px_01.png','images/bet_sitz_30px_05.png')


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
        runner.run(BtmsWampComponentAuth, start_reactor=False)

    @inlineCallbacks
    def on_session(self, session):
        """
        Called from WAMP session when attached to Crossbar router.
        """
        self.session = session
        self.ids.sm.current = 'work1'
       #self.ids.kv_user_list.clear_widgets(children=None)
        results = yield self.session.call(u'io.crossbar.btms.users.get')
        self.get_users(results)
        self.ids.kv_user_button.text = btms_user

        results = yield self.session.call(u'io.crossbar.btms.events.get')
        self.get_events(results)


        #self.session.leave()

    def get_users(self,results):
        user_list = []
        self.ids.kv_user_list.clear_widgets(children=None)
        for row in results:
            print row['user']
            user_list.append(row['user'])
            self.ids.kv_user_list.add_widget(Button(text=str(row['user']),on_release=partial(self.change_user,str(row['user']))))

        store.put('userlist', user_list=user_list)


    def change_user(self,user,*args):
        self.ids.kv_password_input.text = ''
        self.ids.kv_user_input.text = user

        self.ids.sm.current = 'server_connect'

    def on_users_message(self,result):
        """
        Called from VotesWampComponent when Crossbar router published reset event.
        """
        #print result.first_name
        #self.ids.box_with_vote_widgets.add_widget(Button(text='User: ' + str(users_results['user'])))
        for row in result:
            print row['user']
            self.ids.box_with_vote_widgets.add_widget(Button(text='User: \n' + str(row['user'])
            + '\n ' + str(row['first_name'])
            + '\n ' + unicode(row['second_name'], 'iso-8859-15')
            ))

    def logout(self,op):
        self.logout_op = op
        self.ids.kv_password_input.text = ''
        self.ids.kv_user_change.disabled = False
        self.session.leave()

        #self.ids.sm.current = 'login_user'

    #Programm

    def get_events(self,results):
        global event_titles_list
        event_titles_list = {}
        event_itm = {}

        self.ids.event_title.clear_widgets()
        global event_id
        event_id = 0

        for row in results:

            print row['id']
            print row['title']
            print row['date_start']
            print row['date_end']
            print row['start_times']

            event_titles_list[row['id']] = row['title'] + '\n' + row['date_start'] + ' - ' + row['date_end']

            if event_id == 0:
                event_id = row['id']
                venue_id = row['venue_id']
                #self.get_venue(event_id, venue_id)
                self.get_event_days(event_id,venue_id)
                #self.get_prices(event_id)

                self.ids.event_btn.text = row['title'] + '\n' + row['date_start'] + ' - ' + row['date_end']

            event_itm['event_btn_' + str(row['id'])] = Button(id=str(row['id']),
                                                              text=row['title'] + '\n' + row['date_start'] + ' - ' +
                                                                   row['date_end'], size_hint_y=None, height=44)
            event_itm['event_btn_' + str(row['id'])].bind(
                on_release=lambda event_btn: self.ids.event_title.select(event_btn.text))
            event_itm['event_btn_' + str(row['id'])].bind(on_release=partial(self.get_event_days,row['id'],row['venue_id']))
            #event_itm['event_btn_' + str(row['id'])].bind(on_release=partial(self.get_venue, row['id'], row['venue_id']))


            self.ids.event_title.add_widget(event_itm['event_btn_' + str(row['id'])])
            # Dates

        #self.ids.event_title.values = event_titles_list

    @inlineCallbacks
    def get_event_days(self, event_id, venue_id, *args):
        def result_event_day(results):
            global event_date

            event_date_match = 0
            date_id = 0
            event_date_itm = {}
            self.event_date_time_dict = {}
            event_itm = {}

            self.ids.event_date.clear_widgets()

            for row in results:
                print 'event_date'
                print row['id']
                print row['date_day']
                print row['start_times']
                self.event_date_time_dict[row['date_day']]= row['start_times']
                # Dates

                if date_id == 0:
                    date_id = row['id']
                    self.ids.event_date_btn.text = row['date_day']
                    event_date = row['date_day']
                    self.set_event_day_times(row['date_day'])


                event_date_itm['event_date_btn_' + str(row['id'])] = Button(id=str(row['id']), text=row['date_day'],
                                                                            size_hint_y=None, height=44)
                event_date_itm['event_date_btn_' + str(row['id'])].bind(
                    on_release=lambda event_date_btn: self.ids.event_date.select(event_date_btn.text))
                event_date_itm['event_date_btn_' + str(row['id'])].bind(
                    on_release=partial(self.set_event_day_times, row['date_day']))

                self.ids.event_date.add_widget(event_date_itm['event_date_btn_' + str(row['id'])])


        try:
            results = yield self.session.call(u'io.crossbar.btms.events.day',event_id)
            result_event_day(results)


        except Exception as err:
            print "Error", err
        finally:

            self.ids.event_title.dismiss() #ugly work around, cause drop down not react
            self.ids.event_btn.text = event_titles_list[event_id] #ugly work around, cause drop down not react
            self.get_venue(event_id, venue_id)






    def set_event_day_times(self, day, *args):
        event_times_list = []

        for kv in self.event_date_time_dict[day].split(","):
            key, value = kv.split(";")
            event_times_list.append(value)

            if key == '1':
                self.ids.event_time.text = value

        self.ids.event_time.values = event_times_list

    def set_event_time(self, time, *args):
        pass

    @inlineCallbacks
    def get_venue(self, event_id1, venue_id, *args):
        global event_id
        event_id = event_id1



        def result_venue(results):
            #Clear item box
            self.ids.sale_item_list_box.clear_widgets(children=None)

            #Init
            global itm
            global bill_itm
            global bill_itm_price_amount
            global bill_total_price
            global seat_list
            global free_seat_list
            itm = {}
            seat_list = {}
            free_seat_list = {}
            bill_itm = {}
            bill_itm_price_amount = {}
            bill_total_price = {}


            #Iterate over items
            for row in results:

                row_id = str(row['id'])
                seat_list[str(row['id'])] = {}

                #Numbered seats
                if row['art'] == 1:



                    def switching_function(com, cols, rows, item_id, cat_id, seats, title, *args):
                        self.ids.sale_item_list_box2.clear_widgets(children=None)
                        if com == 0:

                            #Add additional row if its nessesary
                            if cols * rows < seats:
                                rows = rows + 1


                            #Check for free Seats
                            #free_seats = 0
                            #for key, value in seat_list[str(item_id)].items():
                            #    if value == 0:
                            #        free_seats = free_seats + 1

                            #Check if Numberbox are full
                            selected_seats = 0
                            if self.ids.number_display_box.text == '' or self.ids.number_display_box.text == 0:
                                amount = 0
                                add_to_bill_toggle = 0
                            else:
                                amount = int(self.ids.number_display_box.text)
                                #if amount > seats:
                                #    amount= seats

                                add_to_bill_toggle = 0

                            #Create Item with Seats
                            grid_layout2 = (GridLayout(size_hint=[1,0.2], padding=1, spacing=3, cols=cols,rows=rows))

                            for i in range(0, seats):
                                j= i + 1

                                preload= ImageButton(source=seat_stat_img[0])


                                try:
                                    seat_list[str(item_id)][j]
                                except KeyError:
                                    seat_list[str(item_id)][j] = 0

                                if amount > 0:
                                    if seat_list[str(item_id)][j] == 0:
                                        seat_list[str(item_id)][j] = 3

                                        amount = amount - 1


                                        selected_seats = selected_seats + 1
                                        if add_to_bill_toggle == 0:
                                            first_seat = j
                                            add_to_bill_toggle = 1






                                itm['venue_item_' + str(item_id) + '_' + str(j)] = ImageButton(source=seat_stat_img[seat_list[str(item_id)][j]], text=str(j)+'\n \n \n',
                                    size_hint=[1, 1], on_release=partial(self.add_to_bill, item_id, j, cat_id, 1, event_id))
                                grid_layout2.add_widget(itm['venue_item_' + str(item_id) + '_' + str(j)])
                            self.ids.sale_item_list_box2.add_widget(Button(text=title, size_hint=[1, 0.02],on_release=partial(switching_function,1,row['col'], row['row'], row['id'], cat_id, row['seats'], row['title'])))

                            self.ids.sale_item_list_box2.add_widget(grid_layout2)


                            self.ids.sale_item_list_box2.add_widget(Button(text='Back\n\n\n', size_hint=[1, 0.1],on_release=partial(switching_function,1,row['col'], row['row'], row['id'], cat_id, row['seats'], row['title'])))


                            self.ids.item_screen_manager.current = 'second_item_screen'

                            if add_to_bill_toggle == 1:
                                self.ids.number_display_box.text = str(selected_seats)
                                self.add_to_bill(item_id, first_seat, cat_id, 1, event_id)

                        elif com == 1:
                            self.ids.item_screen_manager.current = 'first_item_screen'


                    #Button for numbered seats
                    float_layout2 = FloatLayout(size_hint=[0.325, .003])
                    itm['venue_item_'+row_id] = Button(pos_hint={'x': .0, 'y': .0}, size_hint=[1, 1], on_release=partial(switching_function, 0, row['col'], row['row'], row['id'], row['cat_id'], row['seats'], row['title']))
                    float_layout2.add_widget(itm['venue_item_'+row_id])

                    float_layout2.add_widget(Label(text=row['title'], pos_hint={'x': .0, 'y': .35}, size_hint=[1, 1]))

                    if row['col'] * row['row'] < row['seats']:
                        row['row'] = row['row'] + 1

                    grid_layout1 = (
                    GridLayout(pos_hint={'x': .0, 'y': -.095}, size_hint=[1, 1], padding=10, spacing=3, cols=row['col'],
                               rows=row['row']))

                    for i in range(0, (row['seats'])):
                        j= i + 1
                        itm['venue_item_ov'+row_id + '_' + str(j)] = Image(size_hint=[0.2, .3], source=seat_stat_img[0])
                        grid_layout1.add_widget(itm['venue_item_ov'+row_id+'_'+str(j)])


                    float_layout2.add_widget(grid_layout1)

                    self.ids.sale_item_list_box.add_widget(float_layout2)

                if row['art'] == 2:
                    # Freie Plaetze
                    free_seat_list[row['id']] = row['seats']

                    float_layout1 = FloatLayout(size_hint=[0.325, .003])
                    itm['venue_item_'+row_id] = Button(pos_hint={'x': .0, 'y': .0}, size_hint=[1, 1], text=row['title'],
                                                    on_release=partial(self.add_to_bill, row['id'], 0,
                                                                       row['cat_id'],2, event_id))

                    float_layout1.add_widget(itm['venue_item_'+row_id])
                    itm['venue_item_seats_'+row_id] = row['seats']

                    itm['venue_itm_pbar_'+row_id] = ProgressBar(pos_hint={'x': .01, 'y': -0.20}, size_hint=[.98, 1],
                                    value=0, max=row['seats'])
                    float_layout1.add_widget(itm['venue_itm_pbar_'+row_id])

                    itm['venue_itm_label_'+row_id] = Label(text=str(row['seats']), pos_hint={'x': .0, 'y': -.35}, size_hint=[1, 1])
                    float_layout1.add_widget(itm['venue_itm_label_'+row_id])

                    itm['venue_itm_label_amount'+row_id] = Label(text='0', pos_hint={'x': .0, 'y': .30}, size_hint=[1, 1], font_size=self.width * 0.03)
                    float_layout1.add_widget(itm['venue_itm_label_amount'+row_id])
                    self.ids.sale_item_list_box.add_widget(float_layout1)


            #self.get_items(event_id)

        try:
            results = yield self.session.call(u'io.crossbar.btms.venue.get',venue_id)
            result_venue(results)


        except Exception as err:
            print "Error", err

        finally:
            self.get_prices(event_id)
            results = yield self.session.call(u'io.crossbar.btms.venue.get.update',venue_id,event_id,u'2016-05-01','16:00')
            print results



            #Init Update Schedule
            #Clock.schedule_interval(self.get_venue_update,1)

    @inlineCallbacks
    def get_prices(self, event_id, *args):
        self.ids.bill_item_list_box.clear_widgets(children=None)
        try:
            prices = yield self.session.call(u'io.crossbar.btms.prices.get',event_id)
            self.get_categories(event_id,prices)

        except Exception as err:
            print "Error", err

    @inlineCallbacks
    def get_categories(self, event_id, prices, *args):
        def result_categories(results):
            itm_price = {}
            for row in results:
                itm_price[row['id']] = {}

                itm_price[row['id']]['float'] = FloatLayout(size_hint=[1, None])

                itm_price[row['id']]['float'].add_widget(Label(text='-[b]' + row['name']
                    + '[/b]', markup=True, pos_hint={'x': -0.34, 'y': 0.42},
                    font_size=self.width * 0.015))
                #Price Area
                itm_price[row['id']]['box'] = BoxLayout(size_hint=[0.85, 1],
                                                                  pos_hint={'x': 0, 'y': 0},
                                                                  orientation='horizontal')


                #Iterate over Prices
                for prow in prices:
                    if prow['cat_id'] == row['id']:
                        pbox = BoxLayout(size_hint=[1, 1], orientation='vertical')
                        pbox.add_widget(Label(text=prow['name'], font_size=self.width * 0.015))
                        pbox.add_widget(Button(text='0'))


                        itm_price[row['id']]['box'].add_widget(pbox)

                #CL and Total Area
                itm_price[row['id']]['tbox'] = BoxLayout(size_hint=[0.15, 1],
                                                                  pos_hint={'x': 0.85, 'y': 0},
                                                                  orientation='horizontal')
                tbox = BoxLayout(size_hint=[1, 1], orientation='vertical')
                tbox.add_widget(Button(text='CL'))
                tbox.add_widget(Button(text='0'))
                itm_price[row['id']]['tbox'].add_widget(tbox)

                #Add in Cat Area
                itm_price[row['id']]['float'].add_widget(itm_price[row['id']]['box'])
                itm_price[row['id']]['float'].add_widget(itm_price[row['id']]['tbox'])
                self.ids.bill_item_list_box.add_widget(itm_price[row['id']]['float'])




        try:
            results = yield self.session.call(u'io.crossbar.btms.categories.get',event_id)
            result_categories(results)


        except Exception as err:
            print "Error", err


    def on_venue_update(self,result):
        global seat_list
        for row in result:
            print row['user']



    def add_to_bill(self, item_id, seat, cat_id, art, event_id, *args):
        pass

# Buttons
class ImageButton(Button):
    pass

class BtmsApp(App):

    def build(self):
        self.title = 'BTMS 15.11a'
        self.root = BtmsRoot()
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
        return True

    def on_resume(self):
        pass

if __name__ == '__main__':
    BtmsApp().run()
