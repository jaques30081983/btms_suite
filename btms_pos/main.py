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
from autobahn.twisted.wamp import ApplicationSession
from autobahn.twisted.wamp import ApplicationRunner
from autobahn.wamp import auth
from twisted.internet.defer import inlineCallbacks
from twisted.internet import defer
#import msgpack
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
import datetime as dt


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
        self.subscribe(ui.on_venue_update, u'io.crossbar.btms.venue.update')
        self.subscribe(ui.on_block_item, u'io.crossbar.btms.item.block.action')
        self.subscribe(ui.on_select_seats, u'io.crossbar.btms.seats.select.action')
        self.subscribe(ui.on_set_unnumbered_seats, u'io.crossbar.btms.unnumbered_seats.set.action')




    def onLeave(self, details):
        print("onLeave: {}".format(details))
        if ui.logout_op == 0 or ui.logout_op == None:
            ui.ids.sm.current = 'server_connect'
            ui.ids.kv_user_log.text = ui.ids.kv_user_log.text + '\n' + ("onLeave: {}".format(details))
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
        for row in results:
            if row['user'] == btms_user: #TODO simply btms_user to user
                self.user_id = row['id']
                self.user = btms_user



        results = yield self.session.call(u'io.crossbar.btms.events.get')
        self.get_events(results)


        #self.session.leave()

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

    @inlineCallbacks
    def get_venues(self, *args):

        def result_venues(results):

            venue_titles_list = {}
            venue_itm = {}
            venue_id = 0

            for row in results:
                #venue_titles_list[row['id']] = row['title'] + '\n' + row['description']
                if venue_id == 0:
                    self.ids.venue_btn.text = str(row['id']) +', '+ row['title'] +' ('+ row['description'] +')'
                    self.set_venue(row['id'])
                venue_id = row['id']

                venue_itm['venue_btn_' + str(row['id'])] = Button(id=str(row['id']),
                                                                  text=str(row['id']) +', '+ row['title'] +' ('+  row['description'] +')',
                                                                  size_hint_y=None, height=44)
                venue_itm['venue_btn_' + str(row['id'])].bind(
                    on_release=lambda venue_btn: self.ids.venue_title.select(venue_btn.text))

                venue_itm['venue_btn_' + str(row['id'])].bind(
                    on_release=partial(self.set_venue,row['id']))

                self.ids.venue_title.add_widget(venue_itm['venue_btn_' + str(row['id'])])


        results = yield self.session.call(u'io.crossbar.btms.venues.get')
        result_venues(results)

    def set_venue(self,id, *args):
        self.selected_venue_id = id


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


                self.get_event_days(event_id,venue_id)


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
        self.event_id = event_id
        self.venue_id = venue_id
        self.load_new_venue = 0 #toggle for get_venue_update in set_event_time
        def result_event_day(results):


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
                date_day = dt.datetime.strptime(row['date_day'], "%Y-%m-%d")
                date_day_name = date_day.strftime("%a")


                if date_id == 0:
                    date_id = row['id']
                    self.ids.event_date_btn.text = date_day_name +' '+ row['date_day']
                    #self.event_date = row['date_day']
                    self.set_event_day_times(row['date_day'])


                event_date_itm['event_date_btn_' + str(row['id'])] = Button(id=str(row['id']), text=date_day_name +' '+ row['date_day'],
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
        #Set Date
        self.event_date = day[-10:]


        #Set Time List
        event_times_list = []
        i=0
        for kv in self.event_date_time_dict[self.event_date].split(","):
            #key, value = kv.split(";")

            event_times_list.append(kv)

            if i == 0:
                #Set Init Time
                self.ids.event_time.text = kv
                self.set_event_time(kv)
            i = i+1

        self.ids.event_time.values = event_times_list




    def set_event_time(self, time, *args):
        self.event_time = time
        self.eventdatetime_id = "%s_%s_%s" % (self.event_id,self.event_date,self.event_time)

        if self.load_new_venue == 1:
            self.get_venue_status(self.venue_id,self.event_id)




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
            #global seat_list
            #global free_seat_list
            itm = {}
            self.seat_list = {}
            self.unnumbered_seat_list = {}
            bill_itm = {}
            bill_itm_price_amount = {}
            bill_total_price = {}
            self.transaction_id = 0


            #Iterate over items
            for row in results:

                row_id = str(row['id'])
                self.seat_list[str(row['id'])] = {}


                if row['art'] == 1:
                    #Numbered seats
                    float_layout2 = FloatLayout(size_hint=[0.325, .003])
                    itm['venue_item_'+row_id] = Button(pos_hint={'x': .0, 'y': .0}, size_hint=[1, 1], on_release=partial(self.switch_item, 0, row['col'], row['row'], row['id'], row['cat_id'], row['seats'], row['title']))
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
                    itm['venue_item_user'+row_id] = Label(text='', pos_hint={'x': .0, 'y': .0}, size_hint=[1, 1], font_size=self.width * 0.025, markup=True)

                    float_layout2.add_widget(itm['venue_item_user'+row_id])

                    self.ids.sale_item_list_box.add_widget(float_layout2)

                if row['art'] == 2:
                    # Unnumbered Seats
                    self.unnumbered_seat_list[row['id']] = row['cat_id']

                    float_layout1 = FloatLayout(size_hint=[0.325, .003])
                    itm['venue_item_'+row_id] = Button(pos_hint={'x': .0, 'y': .0}, size_hint=[1, 1], text=row['title'],
                                                    on_release=partial(self.update_bill, row['id'], row['cat_id'],0,2))

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
            self.load_new_venue = 1 #loading of venue finished
            self.get_venue_status(venue_id,event_id)
            self.get_prices(venue_id, event_id)



        try:
            results = yield self.session.call(u'io.crossbar.btms.venue.get',venue_id)
            result_venue(results)


        except Exception as err:
            print "Error", err




    def switch_item(self, com, cols, rows, item_id, cat_id, seats, title, *args):
        self.block_item(item_id, com)
        self.ids.sale_item_list_box2.clear_widgets(children=None)
        if com == 0:
            #Create 2nd View

            #Add additional row if its nessesary
            if cols * rows < seats:
                rows = rows + 1


            #Check if Numberbox are full
            selected_seats = 0
            if self.ids.number_display_box.text == '' or self.ids.number_display_box.text == 0:
                amount = 0
                add_to_bill_toggle = 0
            else:
                amount = int(self.ids.number_display_box.text)
                add_to_bill_toggle = 0

            #Create Item with Seats
            grid_layout2 = (GridLayout(size_hint=[1,0.2], padding=1, spacing=3, cols=cols,rows=rows))

            preload= ImageButton(source=seat_stat_img[0]) #Workaround Kivy dont load directly

            seat_select_list = {str(item_id):{}}

            for i in range(0, seats):
                j= i + 1

                #try:
                #    self.seat_list[str(item_id)][j]
                #except KeyError:
                #    self.seat_list[str(item_id)][j] = 0
                seat_select_item = {str(item_id):{str(j):1}}
                if amount > 0:
                    if self.seat_list[str(item_id)][j] == 0:
                        #self.seat_list[str(item_id)][j] = 3
                        seat_select_list[str(item_id)][str(j)] = 1

                        amount = amount - 1


                        selected_seats = selected_seats + 1
                        if add_to_bill_toggle == 0:
                            #first_seat = j
                            add_to_bill_toggle = 1

                itm['venue_item_' + str(item_id) + '_' + str(j)] = ImageButton(source=seat_stat_img[self.seat_list[str(item_id)][j]], text=str(j)+'\n \n \n',
                    size_hint=[1, 1], on_release=partial(self.select_seats, seat_select_item, cat_id))
                grid_layout2.add_widget(itm['venue_item_' + str(item_id) + '_' + str(j)])


            self.ids.sale_item_list_box2.add_widget(Button(text=title, size_hint=[1, 0.02],on_release=partial(self.switch_item,1,'', '', item_id, cat_id, '', '')))
            self.ids.sale_item_list_box2.add_widget(grid_layout2)
            self.ids.sale_item_list_box2.add_widget(Button(text='Back\n\n\n', size_hint=[1, 0.1],on_release=partial(self.switch_item,1,'', '', item_id, cat_id,'', '')))
            self.ids.item_screen_manager.current = 'second_item_screen'

            if add_to_bill_toggle == 1:

                self.select_seats(seat_select_list, cat_id)
                self.ids.number_display_box.text = ''
                #self.add_to_bill(item_id, first_seat, cat_id, 1, event_id)

        elif com == 1:
            #Switch back to overview
            self.ids.item_screen_manager.current = 'first_item_screen'

    @inlineCallbacks
    def get_venue_status(self,venue_id,event_id):
        results = yield self.session.call(u'io.crossbar.btms.venue.get.init',venue_id,event_id,self.event_date,self.event_time)

        #print results

        #TODO Result is None
        for key, value in results.iteritems():
            #Numbered Seats
            for seat, status in value['seats'].iteritems():

                #if status == 1 and self.user_id == value['seats_user'][seat]:
                #    status = 3

                self.seat_list[str(key)][int(seat)] = status
                itm['venue_item_ov' + str(key) + '_' + str(seat)].source = seat_stat_img[int(status)]


            #Free Seats
            try:

                itm['venue_itm_label_' + str(key)].text = str(value['amount'])
                itm['venue_itm_pbar_'+str(key)].value = value['amount']

            except KeyError:
                pass

            #Blocked Items
            try:
                value2 = value['blocked_by']
                print 'print blocked:', value2
                self.on_block_item(self.eventdatetime_id, key, value2, 1)
            except KeyError:
                pass




    @inlineCallbacks
    def get_prices(self, venue_id, event_id, *args):
        self.ids.bill_item_list_box.clear_widgets(children=None)
        try:
            self.prices = yield self.session.call(u'io.crossbar.btms.prices.get',event_id)

            self.get_categories(venue_id,self.prices)

        except Exception as err:
            print "Error", err

    @inlineCallbacks
    def get_categories(self, venue_id, prices, *args):
        def result_categories(results):
            self.itm_price = {}
            self.itm_cat_price_amount = {}
            self.itm_price_amount = {}
            self.itm_cat_first_price = {}
            self.total_cat_price_list = {}
            for row in results:
                self.itm_cat_price_amount[row['id']] = {}
                self.itm_price_amount[row['id']] = {}
                self.itm_price[row['id']] = {}

                self.itm_price[row['id']]['float'] = FloatLayout(size_hint=[1, None])

                self.itm_price[row['id']]['float'].add_widget(Label(text='-[b]' + row['name']
                    + '[/b]', markup=True, pos_hint={'x': -0.34, 'y': 0.42},
                    font_size=self.width * 0.015))
                #Price Area
                self.itm_price[row['id']]['box'] = BoxLayout(size_hint=[0.85, 1],
                                                                  pos_hint={'x': 0, 'y': 0},
                                                                  orientation='horizontal')


                #Iterate over Prices
                first_price_toggle = 0
                for prow in prices:
                    if prow['cat_id'] == row['id']:
                        self.itm_cat_price_amount[row['id']][prow['id']] = {}
                        self.itm_cat_price_amount[row['id']][prow['id']]['price'] = prow['price']
                        self.itm_cat_price_amount[row['id']][prow['id']]['amount'] = 0

                        if first_price_toggle == 0:
                            first_price_toggle = 1
                            self.itm_cat_first_price[row['id']] = prow['id']


                        pbox = BoxLayout(size_hint=[1, 1], orientation='vertical')
                        pbox.add_widget(Label(text=prow['name'], font_size=self.width * 0.015))

                        self.itm_cat_price_amount[row['id']][prow['id']]['button'] = Button(text='0', font_size=self.width * 0.020, on_release=partial(self.update_bill,0,row['id'],prow['id'],0))
                        pbox.add_widget(self.itm_cat_price_amount[row['id']][prow['id']]['button'])


                        self.itm_price[row['id']]['box'].add_widget(pbox)

                #CL and Total    Area
                self.itm_price[row['id']]['tbox'] = BoxLayout(size_hint=[0.15, 1],
                                                                  pos_hint={'x': 0.85, 'y': 0},
                                                                  orientation='horizontal')
                tbox = BoxLayout(size_hint=[1, 1], orientation='vertical')
                tbox.add_widget(Button(text='CL'))
                self.itm_price[row['id']]['tbutton'] = Button(text='0')
                tbox.add_widget(self.itm_price[row['id']]['tbutton'])

                self.itm_price[row['id']]['tbox'].add_widget(tbox)

                #Add in Cat Area
                self.itm_price[row['id']]['float'].add_widget(self.itm_price[row['id']]['box'])
                self.itm_price[row['id']]['float'].add_widget(self.itm_price[row['id']]['tbox'])
                self.ids.bill_item_list_box.add_widget(self.itm_price[row['id']]['float'])




        try:
            results = yield self.session.call(u'io.crossbar.btms.categories.get',venue_id)
            result_categories(results)


        except Exception as err:
            print "Error", err

    def block_item(self,item_id, cmd):

        self.session.call(u'io.crossbar.btms.item.block', self.eventdatetime_id, item_id, self.user_id, cmd)

    def on_block_item(self,eventdatetime_id, item_id, user_id, block):
        if eventdatetime_id == self.eventdatetime_id:
            if block == 1:
                if user_id == self.user_id or user_id == 0:
                    pass
                else:
                    itm['venue_item_' + str(item_id)].disabled = True
                    itm['venue_item_user'+str(item_id)].text = '[color=ffcc00]'+self.user_list[user_id]+'[/color]'

            else:
                itm['venue_item_' + str(item_id)].disabled = False
                itm['venue_item_user'+str(item_id)].text = ''

    def select_seats(self,seat_select_list, cat_id, *args):

        self.session.call(u'io.crossbar.btms.seats.select', self.eventdatetime_id, seat_select_list, cat_id, self.user_id)

    def on_select_seats(self,edt_id, seat_select_list, cat_id, user_id):
        print 'on_select_seats',edt_id, seat_select_list, user_id

        if edt_id == self.eventdatetime_id:
            if user_id == self.user_id:
                for item_id, seat_list in seat_select_list.iteritems():
                    for seat, status in seat_list.iteritems():
                        print item_id, seat, status

                        if status == 1:
                            status = 3
                        itm['venue_item_ov' + str(item_id) + '_' + str(seat)].source = seat_stat_img[int(status)]
                        itm['venue_item_' + str(item_id) + '_' + str(seat)].source = seat_stat_img[int(status)]
                        self.seat_list[str(item_id)][int(seat)] = status
                        if status == 3 or status == 0:
                            self.update_bill(item_id, cat_id, 0, 1)
            else:
                for item_id, seat_list in seat_select_list.iteritems():
                    for seat, status in seat_list.iteritems():
                        print item_id, seat, status
                        self.seat_list[str(item_id)][int(seat)] = status
                        itm['venue_item_ov' + str(item_id) + '_' + str(seat)].source = seat_stat_img[int(status)]

    def set_unnumbered_seats(self, item_id, amount):
        self.session.call(u'io.crossbar.btms.unnumbered_seats.set', self.eventdatetime_id, self.transaction_id, item_id, amount)


    def on_set_unnumbered_seats(self,edt_id, item_id, amount):
        if edt_id == self.eventdatetime_id:
            itm['venue_itm_pbar_'+str(item_id)].value = amount
            itm['venue_itm_label_'+str(item_id)].text = str(amount)


    def on_venue_update(self,result):
        self.ids.number_display_box.text = result
        print result

    @inlineCallbacks
    def get_transaction_id(self, *args):
        self.transaction_id = yield self.session.call(u'io.crossbar.btms.transaction_id.get',self.event_id,self.event_date,self.event_time,)



    @inlineCallbacks
    def update_bill(self, item_id, cat_id, price_id, art, *args):


        try:
            if self.transaction_id == 0:
                self.transaction_id = yield self.session.call(u'io.crossbar.btms.transaction_id.get',self.event_id,self.event_date,self.event_time,)

                #Disable Event, Date, Time Selection
                self.ids.event_btn.disabled = True
                self.ids.event_date_btn.disabled = True
                self.ids.event_time.disabled = True
                self.ids.res_number_display_box.text = ''
        except Exception as err:
            print "Error", err

        print self.transaction_id



        print'update_bill:', item_id, cat_id, art
        #self.ids.kv_total_button.text = '0' + unichr(8364)
        self.ids.kv_given_button.text = '0' + unichr(8364)
        self.ids.kv_back_button.text = '0' + unichr(8364)


        seat_amount = 0


        if art == 0:
            first_price_id = self.itm_cat_first_price[cat_id]
            if self.ids.number_display_box.text == '':
                for key, value in self.itm_cat_price_amount[cat_id].iteritems():
                    self.itm_cat_price_amount[cat_id][key]['button'].text = '0'
                    seat_amount = seat_amount + value['amount']
                    self.itm_cat_price_amount[cat_id][key]['amount'] = 0

                self.itm_cat_price_amount[cat_id][price_id]['amount']  = seat_amount
                self.itm_cat_price_amount[cat_id][price_id]['button'].text = str(seat_amount)


            else:
                #Count total amount of Categorie
                for key, value in self.itm_cat_price_amount[cat_id].iteritems():
                    seat_amount = seat_amount + value['amount']

                #Check if given bigger than seat_amount
                if  int(self.ids.number_display_box.text) >= seat_amount:
                    given_number = seat_amount
                else:
                    given_number =  int(self.ids.number_display_box.text)


                if given_number >= self.itm_cat_price_amount[cat_id][first_price_id]['amount']:
                    given_number = self.itm_cat_price_amount[cat_id][first_price_id]['amount']

                self.itm_cat_price_amount[cat_id][price_id]['amount']  = given_number
                self.itm_cat_price_amount[cat_id][price_id]['button'].text = str(given_number)

                self.ids.number_display_box.text = ''

                #Hold balance
                amount = 0
                for key, value in self.itm_cat_price_amount[cat_id].iteritems():
                    if first_price_id == key:
                        pass
                    else:
                        amount = amount + value['amount']
                amount1 = seat_amount - amount

                self.itm_cat_price_amount[cat_id][first_price_id]['amount'] = amount1
                self.itm_cat_price_amount[cat_id][first_price_id]['button'].text = str(amount1)



        elif art == 1:
            #Get Selected Seats

            for item_id, seats in self.seat_list.items():
                for seat, status in seats.items():
                    if status == 3:
                        seat_amount = seat_amount + 1
            #Set all to 0

            for key, value in self.itm_cat_price_amount[cat_id].iteritems():
                self.itm_cat_price_amount[cat_id][key]['button'].text = '0'
                self.itm_cat_price_amount[cat_id][key]['amount'] = 0


            #Set Amount to first price
            price_id = self.itm_cat_first_price[cat_id]
            self.itm_cat_price_amount[cat_id][price_id]['amount'] = seat_amount
            self.itm_cat_price_amount[cat_id][price_id]['button'].text = str(seat_amount)

            total_cat_price = seat_amount * float(self.itm_cat_price_amount[cat_id][price_id]['price'])
            self.itm_price[cat_id]['tbutton'].text = str(total_cat_price) + unichr(8364)


        elif art == 2:
            price_id = self.itm_cat_first_price[cat_id]
            if self.ids.number_display_box.text == '':
                try:
                    amount = self.itm_price_amount[cat_id][item_id] + 1
                except KeyError:
                    amount = 1
                    self.itm_price_amount[cat_id][item_id] = amount

            else:
                amount = int(self.ids.number_display_box.text)

            #Set amount for item
            self.itm_price_amount[cat_id][item_id] = amount
            itm['venue_itm_label_amount'+str(item_id)].text = str(amount)

            self.set_unnumbered_seats(item_id, amount)

            #Set amount for categorie from same items
            amount = 0

            for key, value in self.itm_cat_price_amount[cat_id].iteritems():
                    self.itm_cat_price_amount[cat_id][key]['button'].text = '0'
                    self.itm_cat_price_amount[cat_id][key]['amount'] = 0


            for key, value in self.itm_price_amount[cat_id].iteritems():
                amount = amount + value

            self.itm_cat_price_amount[cat_id][price_id]['amount'] = amount
            self.itm_cat_price_amount[cat_id][price_id]['button'].text = str(amount)



            self.ids.number_display_box.text = ''
        elif art == 3:
            pass


        #Compute Total Price of Categorie
        total_cat_price = 0
        for key, value in self.itm_cat_price_amount[cat_id].iteritems():
            summ = value['amount'] * float(self.itm_cat_price_amount[cat_id][key]['price'])
            total_cat_price = total_cat_price + summ

        self.itm_price[cat_id]['tbutton'].text = str(total_cat_price) + unichr(8364)
        self.total_cat_price_list[cat_id] = total_cat_price

        #Iterate over all Categories
        self.total_bill_price = 0
        for key, value in self.total_cat_price_list.iteritems():
            print 'total', key, value
            self.total_bill_price = self.total_bill_price + value

        self.ids.kv_total_button.text = str(self.total_bill_price) + unichr(8364)


        #self.seat_select_list = {str(item_id):{str(seat):1}}
        #self.select_seats(self.seat_select_list)

        #if self.session:
            #block = ''
            #eventdatetime_id = "%s_%s_%s" % (self.event_id,self.event_date,self.event_time)
            #self.session.call(u'io.crossbar.btms.bill.add', eventdatetime_id, block)

    #@inlineCallbacks
    def cash(self, *args):
        #Give, Back
        if self.ids.number_display_box.text == '' or self.ids.number_display_box.text == 0:
            self.ids.kv_given_button.text = str(self.total_bill_price) + unichr(8364)
            self.ids.kv_back_button.text =  '0' + unichr(8364)
            self.back_price = 0
            self.given_price = self.total_bill_price

            self.transact('cash')
        else:
            self.ids.kv_given_button.text = self.ids.number_display_box.text + unichr(8364)

            back_price = float(self.ids.number_display_box.text) - self.total_bill_price
            if back_price <= 0:
                self.ids.kv_given_button.text =  '!!!'
                self.ids.kv_back_button.text =  '0' + unichr(8364)
            else:
                self.ids.kv_back_button.text = str(back_price) + unichr(8364)


                self.back_price = back_price
                self.given_price = float(self.ids.number_display_box.text)
                self.transact('cash')
            self.ids.number_display_box.text = ''





    def card(self, *args):
        #call ext api, like payleven, sumup, etc...
        self.ids.kv_card_button.text = 'n. a.'

        def my_callback(dt):
            self.ids.kv_card_button.text = 'CARD'
        Clock.schedule_once(my_callback, 2)


    @inlineCallbacks
    def transact(self, opt, *args):

        if opt == 'cash':
            account = 1000 #SKR03
            status = 2
        elif opt == 'card':
            account = 1200 #SKR03
            status = 2
        elif opt == 'reserve':
            account = 0
            status = 1

        #Collect Data
        seat_trans_list = {}
        for item_id, seats in self.seat_list.items():
            for seat, status1 in seats.items():
                if status1 == 3:
                    try:
                        seat_trans_list[str(item_id)]
                    except KeyError:
                        seat_trans_list[str(item_id)] = {}
                    seat_trans_list[str(item_id)][str(seat)] = 2


        itm_cat_amount_list = {}
        for cat_id, value in self.itm_cat_price_amount.iteritems():
            itm_cat_amount_list[str(cat_id)] = {}
            for price_id, value1 in value.iteritems():
                if value1['amount'] == 0:
                    pass
                else:
                    itm_cat_amount_list[str(cat_id)][str(price_id)] = value1['amount']






        try:
            results = yield self.session.call(u'io.crossbar.btms.transact',
                                              opt, self.event_id, self.event_date, self.event_time,
                                              self.transaction_id, seat_trans_list, itm_cat_amount_list, status, account,
                                              self.total_bill_price, self.back_price,self.given_price,
                                              self.user_id)

            self.ids.number_display_box.text = results

        except Exception as err:
            print "Error", err

        finally:
            self.print_ticket()
            self.transaction_id_old = self.transaction_id #Will be used if printing not work
            self.reset_transaction()


    def reset_transaction(self):
        #self.ids.kv_total_button.text = '0' + unichr(8364)
        #self.ids.kv_given_button.text = '0' + unichr(8364)
        #self.ids.kv_back_button.text =  '0' + unichr(8364)
        self.ids.item_screen_manager.current = 'first_item_screen'
        self.block_item(0, 1)

        self.ids.event_btn.disabled = False
        self.ids.event_date_btn.disabled = False
        self.ids.event_time.disabled = False

        self.transaction_id = 0


        self.total_cat_price_list = {}

        #Reset Price/Amount Section
        for cat_id, value in self.itm_cat_price_amount.iteritems():
            self.itm_price[cat_id]['tbutton'].text = '0'
            for price_id, value1 in value.iteritems():
                value1['button'].text = '0'
                value1['amount'] = 0

        #Reset Item Amounts
        for item_id, cat_id in self.unnumbered_seat_list.iteritems():
            print item_id, cat_id
            self.itm_price_amount[cat_id][item_id] = 0
            itm['venue_itm_label_amount'+str(item_id)].text = '0'


    @inlineCallbacks
    def print_ticket(self, *args):

        #Print
        try:
            results = yield self.session.call(u'io.crossbar.btms.ticket.print', self.ticket_printer, self.transaction_id)

            print results

        except Exception as err:
            print "Error", err



    @inlineCallbacks
    def get_printers(self, *args):

        #Get Printers
        try:
            printers = yield self.session.call(u'io.crossbar.btms.printers.get')
            printers_list = []
            for printer in printers:
                print printer, printers[printer]["device-uri"]
                printers_list.append(printer)

            self.ids.kv_ticket_printer_spinner.values = printers_list
            self.ids.kv_bon_printer_spinner.values = printers_list
            self.ids.kv_report_printer_spinner.values = printers_list
            self.printer_set = True

        except Exception as err:
            print "Error", err

    def set_printer(self, option, printer, *args):
        print option, printer

        try:
            self.printer_set
        except AttributeError:
            self.printer_set = False

        if self.printer_set == True:
            try:
                self.ticket_printer
            except AttributeError:
                self.ticket_printer = ''
                self.bon_printer = ''
                self.report_printer = ''


            if option == 'ticket':
                self.ticket_printer = printer
                self.ids.kv_printer_button.text = 'Printer: ' + printer
                store.put('printers',ticket=printer, bon=self.bon_printer, report=self.report_printer)
            elif option == 'bon':
                self.bon_printer = printer
                store.put('printers',ticket=self.ticket_printer, bon=printer,  report=self.report_printer)
            elif option == 'report':
                self.report_printer = printer
                store.put('printers',ticket=self.ticket_printer, bon=self.bon_printer, report=printer)

    def get_printer_status(self, transaction_id, printer, *args):
        print option, printer
        #TODO check printer status

    @inlineCallbacks
    def create_events(self):
        title = self.ids.kv_create_event_title.text
        description = self.ids.kv_create_event_description.text
        venue_id = self.selected_venue_id

        start_date = self.ids.kv_create_event_date_start.text
        end_date = self.ids.kv_create_event_date_end.text
        admission_hours = self.ids.kv_create_event_admission_hours.text

        mon_times = self.ids.kv_create_event_mon_times.text
        tue_times = self.ids.kv_create_event_tue_times.text
        wed_times = self.ids.kv_create_event_wed_times.text
        thu_times = self.ids.kv_create_event_thu_times.text
        fri_times = self.ids.kv_create_event_fri_times.text
        sat_times = self.ids.kv_create_event_sat_times.text
        sun_times = self.ids.kv_create_event_sun_times.text

        weekday_times = {'0':mon_times, '1':tue_times, '2':wed_times, '3':thu_times, '4':fri_times, '5':sat_times, '6':sun_times}


        try:
            result = yield self.session.call(u'io.crossbar.btms.event.create', title, description, venue_id, start_date, end_date, admission_hours, weekday_times, str(self.user_id))

        except Exception as err:
            print "Error", err


        finally:
            print result






# Buttons
class ImageButton(Button):
    pass

class BtmsApp(App):

    def build(self):
        self.title = 'BTMS 16.01a'
        self.root = BtmsRoot()
        self.root.ids.kv_user_change.disabled = True

        if store.exists('settings'):
            self.root.ids.kv_server_adress.text = store.get('settings')['server_adress']
            self.root.ids.kv_user_input.text = store.get('settings')['user']
            L = store.get('userlist')['user_list']
            self.root.ids.kv_user_change.disabled = False
            for user in L:
                self.root.ids.kv_user_list.add_widget(Button(text=user,on_release=partial(self.root.change_user,user)))

        if store.exists('printers'):
            self.root.ticket_printer = store.get('printers')['ticket']
            self.root.bon_printer = store.get('printers')['bon']
            self.root.report_printer = store.get('printers')['report']

            self.root.ids.kv_printer_button.text = 'Printer: ' + store.get('printers')['ticket']
            self.root.ids.kv_ticket_printer_spinner.text = self.root.ticket_printer
            self.root.ids.kv_bon_printer_spinner.text = store.get('printers')['bon']
            self.root.ids.kv_report_printer_spinner.text = store.get('printers')['report']

        #self.start_wamp_component()

        return self.root



    def on_pause(self):
        return True

    def on_resume(self):
        pass

if __name__ == '__main__':
    BtmsApp().run()
