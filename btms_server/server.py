###############################################################################
##
##  Copyright (C) 2014, Tavendo GmbH and/or collaborators. All rights reserved.
##
##  Redistribution and use in source and binary forms, with or without
##  modification, are permitted provided that the following conditions are met:
##
##  1. Redistributions of source code must retain the above copyright notice,
##     this list of conditions and the following disclaimer.
##
##  2. Redistributions in binary form must reproduce the above copyright notice,
##     this list of conditions and the following disclaimer in the documentation
##     and/or other materials provided with the distribution.
##
##  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
##  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
##  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
##  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
##  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
##  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
##  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
##  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
##  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
##  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
##  POSSIBILITY OF SUCH DAMAGE.
##
###############################################################################
#from twistar.registry import Registry
#from twistar.dbobject import DBObject

from twisted.enterprise import adbapi
from twisted.internet.defer import inlineCallbacks, returnValue
import MySQLdb.cursors
from datetime import datetime
from baluhn import generate, verify

from autobahn import wamp
from autobahn.twisted.wamp import ApplicationSession
import json



class BtmsBackend(ApplicationSession):

    def __init__(self, config):
        ApplicationSession.__init__(self, config)
        self.init()
        #self.getVenueInit()

    def init(self):
        self._votes = {
            'Banana': 0,
            'Chocolate': 0,
            'Lemon': 0
        }

    @wamp.register(u'io.crossbar.btms.vote.get')
    def getVotes(self):
        return [{'subject': key, 'votes': value} for key, value in self._votes.items()]


    @wamp.register(u'io.crossbar.btms.vote.vote')
    def submitVote(self, subject):
        self._votes[subject] += 1
        result = {'subject': subject, 'votes': self._votes[subject]}
        self.publish('io.crossbar.btms.vote.onvote', result)
        return result

    @wamp.register(u'io.crossbar.btms.vote.reset')
    def resetVotes(self):
        self.init()
        self.publish('io.crossbar.btms.vote.onreset')

    @wamp.register(u'io.crossbar.btms.users.get')
    def getUser(self):
        '''
        def get_result(user):
            return self.db.runQuery("SELECT * FROM btms_users ORDER by user")

        def printResult(result):
            pass
            #self.publish('io.crossbar.btms.users.result', result)
        '''

        #get_result("jaques").addCallback(printResult)
        #print get_result("jaques").callback(result)
        return self.db.runQuery("SELECT * FROM btms_users ORDER by user")
        #return [{'subject': key, 'votes': value} for key, value in self._votes.items()]

    @wamp.register(u'io.crossbar.btms.events.get')
    def getEvents(self):

        date_current = datetime.now().strftime('%Y-%m-%d')


        return self.db.runQuery("SELECT id, title, description, date_start, start_times, date_end, venue_id FROM btms_events WHERE ref = '0' AND date_end >= '"+date_current+"' ORDER by date_end")

    @wamp.register(u'io.crossbar.btms.events.day')
    def getEventsDay(self,event_id):

        return self.db.runQuery("SELECT id, date_day, start_times FROM btms_events WHERE ref = '"+str(event_id)+"'")

    @wamp.register(u'io.crossbar.btms.venue.get')
    def getVenue(self,venue_id):

        return self.db.runQuery("SELECT * FROM btms_venues WHERE ref = '"+str(venue_id)+"' ORDER by id")

    @wamp.register(u'io.crossbar.btms.categories.get')
    def getCategories(self,event_id):

        return self.db.runQuery("SELECT * FROM btms_categories WHERE event_id = '"+str(event_id)+"'")


    @wamp.register(u'io.crossbar.btms.prices.get')
    def getPrices(self,event_id):

        return self.db.runQuery("SELECT id, name, price, cat_id FROM btms_prices WHERE event_id = '"+str(event_id)+"'")

    @wamp.register(u'io.crossbar.btms.transaction_id.get')
    @inlineCallbacks
    def getTransactionId(self,event_id,event_date,event_time,*args):
        #Check if a counter for EventDateTime exists
        result_venues = yield self.db.runQuery("SELECT * FROM btms_counter WHERE event_id = '"+str(event_id)+"' AND"
                                               " date = '"+str(event_date)+"' AND time = '"+str(event_time)+"'")
        for row in result_venues:
            #print row
            counter_id = row['id']
            counter_amount = row['amount']

        #Update counter if exists or create new counter
        try:
            counter_amount = counter_amount + 1
            sql = "UPDATE btms_counter SET btms_counter.amount='%s' WHERE btms_counter.id='%s'" % (counter_amount, counter_id)
            d = self.db.runOperation(sql)
            print 'updated'
        except NameError:
            print 'not exists'
            counter_amount = 1000
            sql = "insert into btms_counter(event_id, date, time, amount ) values('%s','%s','%s','%s')" % (event_id, event_date, event_time, counter_amount)
            d = self.db.runOperation(sql)

        #Generate Transaction Id
        transaction_id = str(event_id)+event_date+event_time+str(counter_amount)
        transaction_id = filter(str.isalnum, transaction_id)

        luhn = generate(transaction_id)



        transaction_id = str(transaction_id)+luhn

        returnValue(transaction_id)


    @wamp.register(u'io.crossbar.btms.venue.get.init')
    @inlineCallbacks
    def getVenueInit(self,venue_id,event_id,date,time,*args):
        eventdatetime_id = "%s_%s_%s" % (event_id,date,time)

        try:
            self.item_list
        except AttributeError:
            self.item_list = {}
            print 'new item_list created'
            try:
                self.freeseat_list
            except AttributeError:
                self.freeseat_list = {}
                print 'new freeseat_list created'



        if eventdatetime_id in self.item_list:
            print 'return existing item_list'
            returnValue(self.item_list[eventdatetime_id])


        else:
            print 'return new item_list'

            try:

                result_venues = yield self.db.runQuery("SELECT * FROM btms_venues WHERE ref = '"+str(venue_id)+"' ORDER by id")
                event_id = str(event_id)


                self.item_list[eventdatetime_id] = {}
                self.freeseat_list[eventdatetime_id] = {}


                for row in result_venues:
                    block = str(row['id'])
                    self.item_list[eventdatetime_id][block] = {'seats':{},'seats_user':{}}


                    if row['art'] == 1:

                        for i in range(0, (row['seats'])):
                                j= i + 1
                                seat = str(j)
                                self.item_list[eventdatetime_id][block]['seats'][seat] = 0
                                self.item_list[eventdatetime_id][block]['seats_user'][seat] = 0


                    if row['art'] == 2:
                        self.freeseat_list[eventdatetime_id][block] = {}
                        self.item_list[eventdatetime_id][block]['amount'] = row['seats']
                        self.freeseat_list[eventdatetime_id][block]['amount'] = row['seats']
                        self.freeseat_list[eventdatetime_id][block]['tid_amount'] = {}

            except Exception as err:
                print "Error", err

            finally:

                try:

                    result_transactions = yield self.db.runQuery("SELECT tid, item_id, cat_id, art, amount, seats, status, user FROM btms_transactions WHERE event_id = '"+str(event_id)+"' AND date = '"+date+"' AND time = '"+time+"'")

                    for row in result_transactions:
                        #Numbered Seats
                        json_string = row['seats'].replace(';',':')
                        json_string = json_string.replace('\\','')
                        json_string = '[' + json_string + ']'


                        item_ov = json.loads(json_string)


                        try:
                            item_ov[0]
                        except IndexError:
                            item_ov = None

                        if item_ov == None:
                            pass
                        else:

                            for block, seat_list in item_ov[0].iteritems():

                                for seat, status in seat_list.iteritems():

                                    self.item_list[eventdatetime_id][block]['seats'][seat] = status
                                    self.item_list[eventdatetime_id][block]['seats_user'][seat] = row['user']

                        #Free Seats
                        if row['art'] == 2:
                            json_string = row['amount'].replace(';',':')
                            json_string = json_string.replace('\\','')
                            json_string = '[' + json_string + ']'


                            item_ov = json.loads(json_string)


                            try:
                                item_ov[0]
                            except IndexError:
                                item_ov = None

                            if item_ov == None:
                                pass
                            else:

                                #self.item_list[eventdatetime_id][row['item_id']]['tid_amount'] = {} #TODO Create own list, only in server, less traffic
                                amount = 0
                                for key, value in item_ov[0].iteritems():
                                    #self.item_list[eventdatetime_id][row['item_id']]['tid_amount'][row['tid']]= value
                                    self.freeseat_list[eventdatetime_id][row['item_id']]['tid_amount'][row['tid']] = value
                                    amount = amount + value

                                self.item_list[eventdatetime_id][row['item_id']]['amount'] = self.freeseat_list[eventdatetime_id][row['item_id']]['amount'] - amount
                                print 'tid amount list:', self.item_list[eventdatetime_id][row['item_id']]['amount']

                except Exception as err:
                    print "Error", err
                finally:
                    pass
                    #print self.item_list
                    #test = 'test123'
                    #returnValue(test)

                    returnValue(self.item_list[eventdatetime_id])


    @wamp.register(u'io.crossbar.btms.item.block')
    def blockItem(self, eventdatetime_id, item_id, user_id, cmd):
        if cmd == 0:
            try:
                self.item_list[eventdatetime_id][str(item_id)]['blocked_by'] = user_id
                block = 1
            except KeyError:
                self.item_list[eventdatetime_id][str(item_id)]['blocked_by'] = user_id
                block = 1

            self.publish('io.crossbar.btms.item.block.action', eventdatetime_id, item_id, user_id, block)

        elif cmd == 1:
            for key, value in self.item_list[eventdatetime_id].iteritems():
                try:
                    if value['blocked_by'] == user_id:
                        self.publish('io.crossbar.btms.item.block.action', eventdatetime_id, key, user_id, 0)
                        self.item_list[eventdatetime_id][str(key)]['blocked_by'] = 0
                except KeyError:
                    pass



    @wamp.register(u'io.crossbar.btms.seats.select')
    def selectSeats(self,edt_id, seat_select_list, user_id):
        print seat_select_list
        new_seat_select_list = {}
        for item_id, seat_list in seat_select_list.iteritems():
            new_seat_select_list = {item_id:{}}
            for seat, status in seat_list.iteritems():

                if self.item_list[edt_id][item_id]['seats'][seat] == 0:
                    self.item_list[edt_id][item_id]['seats'][seat] = 1
                    self.item_list[edt_id][item_id]['seats_user'][seat] = user_id
                    new_seat_select_list[item_id][seat] = 1

                    print 'seat reserved', item_id, seat, status
                else:
                    if self.item_list[edt_id][item_id]['seats_user'][seat] == user_id:
                        self.item_list[edt_id][item_id]['seats'][seat] = 0
                        self.item_list[edt_id][item_id]['seats_user'][seat] = 0
                        new_seat_select_list[item_id][seat] = 0
                        print 'seat is now free', item_id, seat, status
                    else:
                        print 'seat is occupied', item_id, seat, status

        self.publish('io.crossbar.btms.seats.select.action', edt_id, new_seat_select_list, user_id)


    @wamp.register(u'io.crossbar.btms.freeseats.set')
    def setFreeseats(self,edt_id, t_id, item_id, amount):
        try:
            #self.item_list[edt_id][str(item_id)]['tid_amount'][t_id]= amount
            self.freeseat_list[edt_id][str(item_id)]['tid_amount'][t_id] = amount
        except KeyError:
            self.freeseat_list[edt_id][str(item_id)]['tid_amount'] = {}
            self.freeseat_list[edt_id][str(item_id)]['tid_amount'][t_id] = amount

        amount1 = 0
        for key, value in self.freeseat_list[edt_id][str(item_id)]['tid_amount'].iteritems():
            amount1 = amount1 + value

        amount1 = self.freeseat_list[edt_id][str(item_id)]['amount'] - amount1

        self.item_list[edt_id][str(item_id)]['amount'] = amount1
        print amount1

        self.publish('io.crossbar.btms.freeseats.set.action', edt_id, item_id, amount1)


    @wamp.register(u'io.crossbar.btms.bill.add')
    def addtoBill(self, eventdatetime_id, blocks):

        #for block, seat_list in blocks[0].iteritems():

            #for seat, status in seat_list.iteritems():

                #self.item_list[eventdatetime_id][block]['seats'][seat] = 1

        #result = {'subject': subject, 'votes': self._votes[subject]}
        self.publish('io.crossbar.btms.venue.update', blocks)









    @inlineCallbacks
    def onJoin(self, details):
        ## create a new database connection pool. connections are created lazy (as needed)
        ## see: https://twistedmatrix.com/documents/current/api/twisted.enterprise.adbapi.ConnectionPool.html
        ##
        # Connect to the DB

        pool = adbapi.ConnectionPool(
                        'MySQLdb',
                        db='btms',
                        user='btms',
                        passwd='test',
                        host='127.0.0.1',
                        cp_reconnect=True,
                        cursorclass=MySQLdb.cursors.DictCursor
                    )


        yield pool.start()
        print("DB connection pool started")

        ## we'll be doing all database access via this database connection pool
        ##
        self.db = pool

        ## register all procedures on this class which have been
        ## decorated to register them for remoting.
        ##
        res = yield self.register(self)
        print("BtmsBackend: {} procedures registered!".format(len(res)))


