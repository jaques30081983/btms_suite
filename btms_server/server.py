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
from twisted.internet import task
import MySQLdb.cursors

from twistar.registry import Registry
from twistar.dbobject import DBObject
from twistar.dbconfig.mysql import ReconnectingMySQLConnectionPool

from autobahn import wamp
from autobahn.twisted.wamp import ApplicationSession

from baluhn import generate, verify
import json
import datetime as dt
from datetime import datetime

import cups
conn = cups.Connection ()

from ticket import createPdfTicket
from report import createPdfReport
from server_stats import get_server_stats


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
    def getUsers(self):
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

    @wamp.register(u'io.crossbar.btms.user.get')
    def getUser(self,user_id):
        return self.db.runQuery("SELECT * FROM btms_users WHERE id = '"+str(user_id)+"'")

    @wamp.register(u'io.crossbar.btms.user.update')
    def updateUser(self, user_id, user_name, user_secret, user_firstname, user_lastname, user_email, user_phone):
        if user_secret == 'dcddb75469b4b4875094e14561e573d8':
            print 'pw not changed', user_id, user_name, user_secret, user_firstname, user_lastname, user_email, user_phone
            sql = "UPDATE btms_users SET btms_users.user='%s', btms_users.first_name='%s', " \
                  "btms_users.second_name='%s', btms_users.email='%s', btms_users.mobile='%s' " \
                  "WHERE btms_users.id='%s'" % (user_name, user_firstname, user_lastname,
                                                user_email, user_phone, user_id)
        else:
            print 'pw changed', user_id, user_name, user_secret, user_firstname, user_lastname, user_email, user_phone
            sql = "UPDATE btms_users SET btms_users.user='%s', btms_users.secret='%s' , btms_users.first_name='%s', " \
                  "btms_users.second_name='%s', btms_users.email='%s', btms_users.mobile='%s' " \
                  "WHERE btms_users.id='%s'" % (user_name, user_secret, user_firstname, user_lastname,
                                                user_email, user_phone, user_id)

        self.db.runOperation(sql)

    @wamp.register(u'io.crossbar.btms.user.add')
    def addUser(self, user_name, user_secret, user_firstname, user_lastname, user_email, user_phone):
        print 'add_user', user_name, user_secret, user_firstname, user_lastname, user_email, user_phone

        sql = "insert into btms_users(user, secret, role, first_name, second_name, email, mobile) " \
              "values('%s','%s','%s','%s','%s','%s','%s')" % \
              (user_name, user_secret, 'frontend', user_firstname, user_lastname, user_email, user_phone)
        self.db.runOperation(sql)


    @wamp.register(u'io.crossbar.btms.events.add.date')
    def addEventsDate(self,event_id, event_date, event_start_times, admission, user_id):
        sql = "insert into btms_events(ref,date_day,start_times, admission, user_id) " \
              "values('%s','%s','%s','%s','%s')" % \
              (event_id, event_date, event_start_times, admission, user_id)
        self.db.runOperation(sql)

    @wamp.register(u'io.crossbar.btms.events.update.date')
    def updateEventsDate(self,event_date_id, event_date, event_start_times, admission, user_id):
        sql = "UPDATE btms_events SET btms_events.date_day='%s', btms_events.start_times='%s'," \
              " btms_events.admission='%s', btms_events.user_id='%s' " \
              "WHERE btms_events.id='%s'" % (event_date, event_start_times, admission, user_id, event_date_id)
        d = self.db.runOperation(sql)
        print 'updated'

    @wamp.register(u'io.crossbar.btms.events.update.event')
    def updateEvent(self,event_id, event_title, event_description, venue_id, date_start, date_end, admission, user_id):
        sql = "UPDATE btms_events SET btms_events.title='%s', btms_events.description='%s', btms_events.date_start='%s'," \
              " btms_events.date_end='%s', btms_events.admission='%s', btms_events.venue_id='%s', btms_events.user_id='%s' " \
              "WHERE btms_events.id='%s'" % (event_title, event_description, date_start, date_end, admission, venue_id, user_id, event_id)
        d = self.db.runOperation(sql)
        print 'updated'

    @wamp.register(u'io.crossbar.btms.events.delete.date')
    def deleteEventsDate(self, event_date_id):
        #Delete from db
        sql = "DELETE FROM btms_events WHERE id = '"+str(event_date_id)+"'"
        self.db.runOperation(sql)


    @wamp.register(u'io.crossbar.btms.events.get')
    def getEvents(self):
        date_current = datetime.now().strftime('%Y-%m-%d')
        return self.db.runQuery("SELECT id, title, description, date_start, start_times, date_end, admission, venue_id FROM btms_events WHERE ref = '0' AND date_end >= '"+date_current+"' ORDER by date_end")

    @wamp.register(u'io.crossbar.btms.events.day')
    def getEventsDay(self,event_id):
        return self.db.runQuery("SELECT id, date_day, start_times FROM btms_events WHERE ref = '"+str(event_id)+"' ORDER by date_day")

    @wamp.register(u'io.crossbar.btms.journal.days')
    @inlineCallbacks
    def getJournalDays(self,event_id):
        days_list = []
        if event_id == 'all':
            results = yield self.db.runQuery("SELECT reg_date_time FROM btms_journal ORDER by reg_date_time")
        else:
            results = yield self.db.runQuery("SELECT reg_date_time FROM btms_journal WHERE event_id = '"+str(event_id)+"' ORDER by reg_date_time")



        old_date = 0
        for row in results:
            date_time = row['reg_date_time']
            date = date_time[:10]
            if date == old_date:
                pass
            else:
                days_list.append(date)
                old_date = date
        print days_list
        returnValue(days_list)


    @wamp.register(u'io.crossbar.btms.events.get.date')
    def getEventsDate(self,date_id):
        return self.db.runQuery("SELECT id, date_day, start_times, admission FROM btms_events WHERE id = '"+str(date_id)+"' ")


    @wamp.register(u'io.crossbar.btms.venues.get')
    def getVenues(self):

        return self.db.runQuery("SELECT * FROM btms_venues WHERE ref = '0' ORDER by id")

    @wamp.register(u'io.crossbar.btms.venue.get')
    def getVenue(self,venue_id):

        return self.db.runQuery("SELECT * FROM btms_venues WHERE ref = '"+str(venue_id)+"' ORDER by id")

    @wamp.register(u'io.crossbar.btms.categories.get')
    def getCategories(self,venue_id):

        return self.db.runQuery("SELECT * FROM btms_categories WHERE venue_id = '"+str(venue_id)+"'")


    @wamp.register(u'io.crossbar.btms.prices.get')
    def getPrices(self,event_id):

        return self.db.runQuery("SELECT id, name, price, cat_id FROM btms_prices WHERE event_id = '"+str(event_id)+"'")

    @wamp.register(u'io.crossbar.btms.transaction_id.get')
    @inlineCallbacks
    def getTransactionId(self,event_id,event_date,event_time,reservation_art,*args):
        #Check if a counter for EventDateTime exists
        counter_amount = 0
        try:
            result_venues = yield self.db.runQuery("SELECT * FROM btms_counter WHERE event_id = '"+str(event_id)+"' AND date = '"+str(event_date)+"' AND time = '"+str(event_time)+"' AND art ='"+str(reservation_art)+"'")
        except Exception as err:
                print "Error", err

        print 'tid res', result_venues
        for row in result_venues:
            #print row
            counter_id = row['id']
            counter_amount = row['amount']

            counter_amount = counter_amount + 1
            sql = "UPDATE btms_counter SET btms_counter.amount='%s' WHERE btms_counter.id='%s'" % (counter_amount, counter_id)
            d = self.db.runOperation(sql)
            print 'updated'

        #Update counter if exists or create new counter
        if counter_amount == 0:
            if reservation_art == 0:
                counter_amount = 1000
            elif reservation_art == 1:
                counter_amount = 500
            elif reservation_art == 2:
                counter_amount = 100

            sql = "insert into btms_counter(event_id, date, time, amount, art ) values('%s','%s','%s','%s','%s')" % (event_id, event_date, event_time, counter_amount, reservation_art)
            d = self.db.runOperation(sql)

        #Generate Transaction Id
        transaction_id = str(event_id)+event_date+event_time+str(counter_amount)
        transaction_id = filter(str.isalnum, str(transaction_id))

        luhn = generate(transaction_id)

        transaction_id = str(transaction_id)+luhn

        try:
            self.busy_transactions
        except AttributeError:
            self.busy_transactions = []
        self.busy_transactions.append(transaction_id)

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
                self.unnumbered_seat_list
            except AttributeError:
                self.unnumbered_seat_list = {}
                print 'new unnumbered_seat_list created'



        if eventdatetime_id in self.item_list:
            print 'return existing item_list'
            returnValue(self.item_list[eventdatetime_id])


        else:
            print 'return new item_list'

            try:

                result_venues = yield self.db.runQuery("SELECT * FROM btms_venues WHERE ref = '"+str(venue_id)+"' ORDER by id")
                event_id = str(event_id)


                self.item_list[eventdatetime_id] = {}
                self.unnumbered_seat_list[eventdatetime_id] = {}


                for row in result_venues:
                    block = str(row['id'])
                    self.item_list[eventdatetime_id][block] = {'seats':{},'seats_user':{},'seats_tid':{}}
                    self.item_list[eventdatetime_id][block]['cat_id'] = row['cat_id']


                    if row['art'] == 1:

                        for i in range(0, (row['seats'])):
                                j= i + 1
                                seat = str(j)
                                self.item_list[eventdatetime_id][block]['seats'][seat] = 0
                                self.item_list[eventdatetime_id][block]['seats_user'][seat] = 0
                                self.item_list[eventdatetime_id][block]['seats_tid'][seat] = 0


                    if row['art'] == 2:
                        self.unnumbered_seat_list[eventdatetime_id][block] = {}
                        self.item_list[eventdatetime_id][block]['amount'] = row['seats']
                        self.unnumbered_seat_list[eventdatetime_id][block]['amount'] = row['seats']
                        self.unnumbered_seat_list[eventdatetime_id][block]['tid_amount'] = {}

            except Exception as err:
                print "Error", err

            finally:
                #Get Transactions
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
                                    self.item_list[eventdatetime_id][block]['seats_tid'][seat] = row['tid']

                        #Unnumbered Seats
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
                                amount = 0
                                for key, value in item_ov[0].iteritems():
                                    #self.item_list[eventdatetime_id][row['item_id']]['tid_amount'][row['tid']]= value
                                    self.unnumbered_seat_list[eventdatetime_id][row['item_id']]['tid_amount'][row['tid']] = value
                                    amount = amount + value
                                print 'amount', amount

                            self.item_list[eventdatetime_id][row['item_id']]['amount'] = self.item_list[eventdatetime_id][row['item_id']]['amount'] - amount
                            print 'tid amount list:', self.item_list[eventdatetime_id][row['item_id']]['amount']

                except Exception as err:
                    print "Error", err
                finally:
                    try:
                        #Get Contingents
                        result_contingents = yield self.db.runQuery("SELECT id, ref, item_id, cat_id, art, amount, seats, status, user_id FROM btms_contingents WHERE event_id = '"+str(event_id)+"' AND date_day = '"+date+"' AND time = '"+time+"'")
                        print result_contingents
                        for row in result_contingents:

                            transaction_id = eventdatetime_id+str(row['ref'])
                            transaction_id = filter(str.isalnum, str(transaction_id))
                            transaction_id = 'con'+str(transaction_id)


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
                                        self.item_list[eventdatetime_id][block]['seats_user'][seat] = row['user_id']
                                        self.item_list[eventdatetime_id][block]['seats_tid'][seat] = transaction_id

                            #Unnumbered Seats
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
                                    #count from prices in db row
                                    amount = 0
                                    for key, value in item_ov[0].iteritems():
                                        #self.item_list[eventdatetime_id][row['item_id']]['tid_amount'][row['tid']]= value
                                        self.unnumbered_seat_list[eventdatetime_id][row['item_id']]['tid_amount']['con'+str(row['id'])] = value
                                        amount = amount + value
                                    print 'amount', amount, eventdatetime_id, row['item_id'], self.item_list[eventdatetime_id][row['item_id']]['amount']

                                    self.item_list[eventdatetime_id][row['item_id']]['amount'] = self.item_list[eventdatetime_id][row['item_id']]['amount'] - amount

                                    #print 'tid amount list:', self.item_list[eventdatetime_id][row['item_id']]['amount']

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
                self.item_list[eventdatetime_id][str(item_id)]['blocked_by']

            except KeyError:
                self.item_list[eventdatetime_id][str(item_id)]['blocked_by'] = 0


            if self.item_list[eventdatetime_id][str(item_id)]['blocked_by'] == user_id or self.item_list[eventdatetime_id][str(item_id)]['blocked_by'] == 0:
                self.item_list[eventdatetime_id][str(item_id)]['blocked_by'] = user_id
                sucess = True
                self.publish('io.crossbar.btms.item.block.action', eventdatetime_id, item_id, user_id, 1)
            else:
                sucess = False
                print "block stat", self.item_list[eventdatetime_id][str(item_id)]['blocked_by']

            return sucess

        elif cmd == 1:
            for key, value in self.item_list[eventdatetime_id].iteritems():
                try:
                    if value['blocked_by'] == user_id:
                        self.publish('io.crossbar.btms.item.block.action', eventdatetime_id, key, user_id, 0)
                        self.item_list[eventdatetime_id][str(key)]['blocked_by'] = 0
                except KeyError:
                    pass
            return True



    @wamp.register(u'io.crossbar.btms.seats.select')
    def selectSeats(self,edt_id, seat_select_list, cat_id, tid, user_id):
        print seat_select_list
        new_seat_select_list = {}

        for item_id, seat_list in seat_select_list.iteritems():

            new_seat_select_list[item_id] = {}
            for seat, status in seat_list.iteritems():

                if self.item_list[edt_id][item_id]['seats'][seat] == 0:
                    self.item_list[edt_id][item_id]['seats'][seat] = 1
                    self.item_list[edt_id][item_id]['seats_user'][seat] = user_id
                    self.item_list[edt_id][item_id]['seats_tid'][seat] = tid
                    new_seat_select_list[item_id][seat] = 1

                    print 'seat reserved', item_id, seat, status
                else:
                    if self.item_list[edt_id][item_id]['seats_tid'][seat] == tid:
                        self.item_list[edt_id][item_id]['seats'][seat] = 0
                        self.item_list[edt_id][item_id]['seats_user'][seat] = 0
                        self.item_list[edt_id][item_id]['seats_tid'][seat] = 0
                        new_seat_select_list[item_id][seat] = 0
                        print 'seat is now free', item_id, seat, status
                    else:
                        print 'seat is occupied', item_id, seat, status, tid, self.item_list[edt_id][item_id]['seats_tid'][seat]


        self.publish('io.crossbar.btms.seats.select.action', edt_id, new_seat_select_list, cat_id, tid, user_id)


    @wamp.register(u'io.crossbar.btms.unnumbered_seats.set')
    def setUnnumberedSeats(self,edt_id, t_id, item_id, amount):
        try:
            #self.item_list[edt_id][str(item_id)]['tid_amount'][t_id]= amount
            self.unnumbered_seat_list[edt_id][str(item_id)]['tid_amount'][t_id] = amount
        except KeyError:
            self.unnumbered_seat_list[edt_id][str(item_id)]['tid_amount'] = {}
            self.unnumbered_seat_list[edt_id][str(item_id)]['tid_amount'][t_id] = amount

        amount1 = 0
        for key, value in self.unnumbered_seat_list[edt_id][str(item_id)]['tid_amount'].iteritems():
            amount1 = amount1 + value

        amount2 = self.unnumbered_seat_list[edt_id][str(item_id)]['amount'] - amount1

        self.item_list[edt_id][str(item_id)]['amount'] = amount2 #Set for Init
        print amount1

        self.publish('io.crossbar.btms.unnumbered_seats.set.action', edt_id, item_id, amount2)


    @wamp.register(u'io.crossbar.btms.bill.add')
    def addtoBill(self, eventdatetime_id, blocks):

        #for block, seat_list in blocks[0].iteritems():

            #for seat, status in seat_list.iteritems():

                #self.item_list[eventdatetime_id][block]['seats'][seat] = 1

        #result = {'subject': subject, 'votes': self._votes[subject]}
        self.publish('io.crossbar.btms.venue.update', blocks)





    @wamp.register(u'io.crossbar.btms.printers.get')
    def getPrinters(self):
        printers = conn.getPrinters ()
        for printer in printers:
            print printer, printers[printer]["device-uri"]

        return printers

    @wamp.register(u'io.crossbar.btms.ticket.print')
    def printTicket(self,printer,transaction_id, user_name):

        #Print Ticket
        ticket_path = '../spool/ticket_'+ transaction_id +'.pdf'
        printer_returns = conn.printFile(printer, ticket_path, transaction_id+'_'+user_name, {})

        #print 'printer returns:', printer_returns

        return printer_returns

    @wamp.register(u'io.crossbar.btms.ticket.print.job.status')
    def getPrintJobStatus(self,job):

        #Check for ticket is printed

        status = conn.getJobAttributes(job)["job-state"]
        #print 'printed status:', status
        '''
        equals 9 (IPP_JOB_COMPLETED) pysical printed
        IPP_JOB_ABORTED = 8
        IPP_JOB_CANCELED = 7
        IPP_JOB_COMPLETED = 9
        IPP_JOB_HELD = 4
        IPP_JOB_PENDING = 3
        IPP_JOB_PROCESSING = 5
        IPP_JOB_STOPPED = 6
        '''
        job_status = {"job":job,"status":status}
        return job_status

    @wamp.register(u'io.crossbar.btms.event.create')
    #@inlineCallbacks
    def createEvent(self, title, description, venue_id, start_date, end_date, admission_hours, weekday_times, user_id):

        def execute(sql): #TODO not beautiful should be in a pool class ....
            return self.db.runInteraction(_execute, sql)

        def _execute(trans, sql):
            trans.execute(sql)
            return trans.lastrowid

        def insert_days(id, start_date, end_date, admission_hours, weekday_times): #last insert id
            start_date = dt.datetime.strptime(start_date, "%Y-%m-%d")
            end_date = dt.datetime.strptime(end_date, "%Y-%m-%d")

            total_days = (end_date - start_date).days + 1

            week = ['Monday',
              'Tuesday',
              'Wednesday',
              'Thursday',
              'Friday',
              'Saturday',
            'Sunday',]

            for day_number in range(total_days):
                current_date = (start_date + dt.timedelta(days = day_number)).date()

                #dt.datetime.today().weekday()
                weekday = current_date.weekday()

                if weekday_times[str(weekday)] == '':
                    pass
                    print 'droped:', week[weekday]
                else:
                    pass
                    print id, weekday, week[weekday], current_date, weekday_times[str(weekday)]

                    sql2 = "insert into btms_events(ref, date_day, start_times, admission, user_id) values('%s','%s','%s','%s','%s')" % (id, current_date, weekday_times[str(weekday)], admission_hours, user_id)
                    d2 = self.db.runOperation(sql2)



        sql = "insert into btms_events(title, description, venue_id, date_start, date_end, admission, user_id) values('%s','%s','%s','%s','%s','%s','%s')" % (title, description, venue_id, start_date, end_date, admission_hours, user_id)

        d = execute(sql)
        d.addCallback(insert_days, start_date, end_date, admission_hours, weekday_times)

        return 'event created'


    @wamp.register(u'io.crossbar.btms.reserve')
    @inlineCallbacks
    def reserve(self, event_id, event_date, event_time, transaction_id,
                 seat_trans_list, itm_cat_amount_list, pre_res_art, debit, user_id):
        edt_id = "%s_%s_%s" % (event_id,event_date,event_time)
        status = 1

        self.setJournal(transaction_id, event_id, event_date, event_time, '0', itm_cat_amount_list, debit, '0', '0', status, user_id)


        if seat_trans_list == {}:
            pass
        else:

            for item_id, seat_list in seat_trans_list.iteritems():
                pass

            self.publish('io.crossbar.btms.seats.select.action', edt_id, seat_trans_list, 0, None, 0)

            cat_id = self.item_list[edt_id][item_id]['cat_id']
            amount = json.dumps(itm_cat_amount_list[str(cat_id)], separators=(',',';'))
            art = '1'
            seats = json.dumps(seat_trans_list, separators=(',',';'))
            #if retrive_status == False:
            '''
            sql = "insert into btms_transactions(tid, event_id, date, time, item_id, " \
                      "cat_id, art, amount, seats, status, user) " \
                      "values('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" % \
                      (transaction_id, event_id, event_date,
                        event_time, item_id, cat_id, art, amount,
                        seats, status, user_id)

            self.db.runOperation(sql)
            '''

            sql = "insert into btms_transactions(tid, event_id, date, time, item_id, " \
                    "cat_id, art, amount, seats, status, user) " \
                    "values('"+str(transaction_id)+"','"+str(event_id)+"','"+event_date+"','"+event_time+"'," \
                    "'0','"+str(cat_id)+"','"+art+"','"+amount+"','"+seats+"','"+str(status)+"','"+str(user_id)+"') " \
                    "ON DUPLICATE KEY UPDATE amount='"+amount+"', seats='"+seats+"', user='"+str(user_id)+"'"
            try:
                result = yield self.db.runOperation(sql)
            except Exception as err:
                self.item_list = {}
                self.publish('io.crossbar.btms.onLeaveRemote','DB connection closed')
                print "DB Connection Error", err
            #elif retrive_status == True:
                #sql = "UPDATE btms_transactions SET btms_transactions.amount='%s', btms_transactions.seats='%s'," \
                 #     " btms_transactions.user='%s' WHERE btms_transactions.tid='%s' AND " \
                  #    "btms_transactions.cat_id='%s'" % (amount, seats, user_id, transaction_id, cat_id)
                #self.db.runOperation(sql)


        #Insert or Update unnumbered seats and insert in db

        for item_id, value in self.unnumbered_seat_list[edt_id].iteritems():
            try:
                print self.unnumbered_seat_list[edt_id][item_id]['tid_amount'][transaction_id]

                #self.unnumbered_seat_list[edt_id][item_id]['tid_amount'][transaction_id]
                cat_id = self.item_list[edt_id][item_id]['cat_id']
                amount = json.dumps(itm_cat_amount_list[str(cat_id)], separators=(',',';'))
                art = '2'
                seats = '{}'
                #if retrive_status == False:
                sql = "insert into btms_transactions(tid, event_id, date, time, item_id, " \
                      "cat_id, art, amount, seats, status, user) " \
                      "values('"+str(transaction_id)+"','"+str(event_id)+"','"+event_date+"','"+event_time+"'," \
                       "'"+str(item_id)+"','"+str(cat_id)+"','"+art+"','"+amount+"','"+seats+"','"+str(status)+"','"+str(user_id)+"') " \
                      "ON DUPLICATE KEY UPDATE amount='"+amount+"', seats='"+seats+"', user='"+str(user_id)+"'"
                try:
                    result = yield self.db.runOperation(sql)
                except Exception as err:
                    self.item_list = {}
                    self.publish('io.crossbar.btms.onLeaveRemote','DB connection closed')
                    print "DB Connection Error", err
                #elif retrive_status == True:
                    #sql = "UPDATE btms_transactions SET btms_transactions.amount='%s', btms_transactions.seats='%s'," \
                    #  " btms_transactions.user='%s' WHERE btms_transactions.tid='%s' AND " \
                    #  "btms_transactions.item_id='%s'" % (amount, seats, user_id, transaction_id, item_id)
                    #self.db.runOperation(sql)

            except KeyError:
                pass

        transaction_id = str(transaction_id)

        try:
            self.busy_transactions.remove(transaction_id)
        except ValueError:
            print 'Str Transaction Id not in busy list.'
            print 'busy list:', self.busy_transactions


        if pre_res_art == 0:
            transaction_id_part = transaction_id[-5:]
        elif pre_res_art == 1:
            transaction_id_part = transaction_id[-4:]
        elif pre_res_art == 2:
            transaction_id_part = transaction_id[-4:]
        #return transaction_id_part
        returnValue(transaction_id_part)


    @wamp.register(u'io.crossbar.btms.retrieve')
    @inlineCallbacks
    def retrieve(self, eventdatetime_id, in_transaction_id):

        if len(in_transaction_id) <= 5:
            transaction_id = eventdatetime_id+in_transaction_id
            transaction_id = filter(str.isalnum, str(transaction_id))
            verify_result = verify(transaction_id)
        else:
            transaction_id = in_transaction_id
            verify_result = True
        transaction_id = str(transaction_id)
        try:
            self.busy_transactions
        except AttributeError:
            self.busy_transactions = []


        if verify_result == True:
            if transaction_id in self.busy_transactions:
                print'is in list', transaction_id
                returnValue(2)
            else:
                print 'not in list', transaction_id
                try:

                    result = yield self.db.runQuery("SELECT tid, item_id, cat_id, art, amount, seats, status, user FROM btms_transactions WHERE tid = '"+str(transaction_id)+"' ")

                except Exception as err:
                    print "Error", err

                if result == ():
                    returnValue(1)
                else:
                    for row in result:
                        if row['status'] == 1:
                            self.busy_transactions.append(transaction_id)

                            returnValue(result)
                        else:
                            returnValue(3)
        else:
            returnValue(0)






    @wamp.register(u'io.crossbar.btms.transact')
    @inlineCallbacks
    def transact(self, retrive_status, venue_id, event_id, event_date, event_time, transaction_id,
                 seat_trans_list, itm_cat_amount_list, status, account, total_bill_price,
                 back_price, given_price, user_id):

        self.setJournal(transaction_id, event_id, event_date, event_time, account, itm_cat_amount_list,total_bill_price, given_price, back_price, status, user_id)

        edt_id = "%s_%s_%s" % (event_id,event_date,event_time)

        #Check again seat status
        check_result = False
        for item_id, seat_list in seat_trans_list.iteritems():
            for seat, status in seat_list.iteritems():
                check_result = False
                if self.item_list[edt_id][item_id]['seats'][seat] == 1 and self.item_list[edt_id][item_id]['seats_tid'][seat] == transaction_id:
                    self.item_list[edt_id][item_id]['seats'][seat] = 2
                    check_result = True

        #Set seat status if seats are reserved from same user and insert in db
        if check_result == True:
            self.publish('io.crossbar.btms.seats.select.action', edt_id, seat_trans_list, 0, transaction_id, user_id)

            cat_id = self.item_list[edt_id][item_id]['cat_id']
            amount = json.dumps(itm_cat_amount_list[str(cat_id)], separators=(',',';'))
            art = '1'
            seats = json.dumps(seat_trans_list, separators=(',',';'))
            '''
            if retrive_status == False:
                sql = "insert into btms_transactions(tid, event_id, date, time, item_id, " \
                          "cat_id, art, amount, seats, status, user) " \
                          "values('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" % \
                          (transaction_id, event_id, event_date,
                            event_time, item_id, cat_id, art, amount,
                            seats, status, user_id)

                self.db.runOperation(sql)
            elif retrive_status == True:
                    sql = "UPDATE btms_transactions SET btms_transactions.amount='%s', btms_transactions.seats='%s'," \
                          " btms_transactions.status='%s', btms_transactions.user='%s' WHERE btms_transactions.tid='%s' AND " \
                          "btms_transactions.cat_id='%s'" % (amount, seats, '2', user_id, transaction_id, cat_id)
                    self.db.runOperation(sql)
            '''
            sql = "insert into btms_transactions(tid, event_id, date, time, item_id, " \
                "cat_id, art, amount, seats, status, user) " \
                "values('"+str(transaction_id)+"','"+str(event_id)+"','"+event_date+"','"+event_time+"'," \
                "'0','"+str(cat_id)+"','"+art+"','"+amount+"','"+seats+"','"+str(status)+"','"+str(user_id)+"') " \
                "ON DUPLICATE KEY UPDATE amount='"+amount+"', seats='"+seats+"', user='"+str(user_id)+"', status='2' "
            try:
                result = yield self.db.runOperation(sql)
            except Exception as err:
                self.item_list = {}
                self.publish('io.crossbar.btms.onLeaveRemote','DB connection closed')
                print "DB Connection Error", err
        #Get unnumbered seats and insert in db

        for item_id, value in self.unnumbered_seat_list[edt_id].iteritems():
            try:
                print self.unnumbered_seat_list[edt_id][item_id]['tid_amount'][transaction_id]

                #self.unnumbered_seat_list[edt_id][item_id]['tid_amount'][transaction_id]
                cat_id = self.item_list[edt_id][item_id]['cat_id']
                amount = json.dumps(itm_cat_amount_list[str(cat_id)], separators=(',',';'))
                art = '2'
                seats = '{}'
                '''
                if retrive_status == False:
                    sql = "insert into btms_transactions(tid, event_id, date, time, item_id, " \
                          "cat_id, art, amount, seats, status, user) " \
                          "values('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" % \
                          (transaction_id, event_id, event_date,
                            event_time, item_id, cat_id, art, amount,
                            seats, status, user_id)

                    self.db.runOperation(sql)
                elif retrive_status == True:
                    sql = "UPDATE btms_transactions SET btms_transactions.amount='%s', btms_transactions.seats='%s'," \
                          " btms_transactions.status='%s', btms_transactions.user='%s' WHERE btms_transactions.tid='%s' AND " \
                          "btms_transactions.item_id='%s'" % (amount, seats, '2', user_id, transaction_id, item_id)
                    self.db.runOperation(sql)
                '''
                sql = "insert into btms_transactions(tid, event_id, date, time, item_id, " \
                    "cat_id, art, amount, seats, status, user) " \
                    "values('"+str(transaction_id)+"','"+str(event_id)+"','"+event_date+"','"+event_time+"'," \
                    "'"+str(item_id)+"','"+str(cat_id)+"','"+art+"','"+amount+"','"+seats+"','"+str(status)+"','"+str(user_id)+"') " \
                    "ON DUPLICATE KEY UPDATE amount='"+amount+"', seats='"+seats+"', user='"+str(user_id)+"', status='2' "
                try:
                    result = yield self.db.runOperation(sql)
                except Exception as err:
                    self.item_list = {}
                    self.publish('io.crossbar.btms.onLeaveRemote','DB connection closed')
                    print "DB Connection Error", err
            except KeyError:
                pass

        try:
            #Create and Insert Tickets
            #Iterate over seat_list and create new indexed one
            single_seat_list = {}

            i = 0
            for item_id, seat_list in sorted(seat_trans_list.iteritems(), key=lambda seat_trans_list: int(seat_trans_list[0])):
                cat_id = self.item_list[edt_id][item_id]['cat_id']
                try:
                    single_seat_list[cat_id]
                except KeyError:
                    single_seat_list[cat_id] = {}

                for seat, status in sorted(seat_list.iteritems(), key=lambda seat_list: int(seat_list[0])):
                    #if self.item_list[edt_id][item_id]['seats'][seat] == 2 and self.item_list[edt_id][item_id]['seats_user'][seat] == user_id:
                    single_seat_list[cat_id][i] = {}
                    single_seat_list[cat_id][i][item_id] = seat

                    i = i + 1



            #Iterate over unnumbered seat list + i

            for item_id, value in self.unnumbered_seat_list[edt_id].iteritems():

                try:
                    amount = self.unnumbered_seat_list[edt_id][item_id]['tid_amount'][transaction_id]
                    cat_id = self.item_list[edt_id][item_id]['cat_id']
                    i = 0
                    try:
                        single_seat_list[cat_id]
                    except KeyError:
                        single_seat_list[cat_id] = {}



                    for j in range(0,amount):
                        single_seat_list[cat_id][i] = {}
                        single_seat_list[cat_id][i][item_id] = 0
                        i = i + 1
                except KeyError:
                    pass





            #distr prices over categorie seats
            ticket_list = {}
            t = 0
            for cat_id, price_amount_list in sorted(itm_cat_amount_list.iteritems()):
                i = 0
                for price_id, amount in price_amount_list.iteritems():
                    for j in range(0,amount):

                        value = single_seat_list[int(cat_id)][i]
                        item_id = value.items()[0][0]
                        seat = value.items()[0][1]
                        ticket_list[t] = {}
                        ticket_list[t]['cat_id'] = cat_id
                        ticket_list[t]['item_id'] = item_id
                        ticket_list[t]['price_id'] = price_id
                        ticket_list[t]['seat'] = seat

                        i = i + 1
                        t =  t + 1


            #print 'index', ticket_list
            for key, value in sorted(ticket_list.iteritems()):
                print key, value['item_id'], value['price_id'], value['cat_id'], value['seat']
                ticket_id = key
                cat_id = value['cat_id']
                item_id = value['item_id']
                price_id = value['price_id']
                seat = value['seat']

                if seat == 0:
                    art = 2
                else:
                    art = 1

                sql = "insert into btms_tickets(tid, ticket_id, event_id, date, time, item_id, " \
                                      "cat_id, art, price_id, seat, status, user) " \
                                      "values('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" % \
                                      (transaction_id, ticket_id, event_id, event_date,
                                        event_time, item_id, cat_id, art, price_id,
                                        seat, 0, user_id)

                self.db.runOperation(sql)
        finally:

            #print opt, event_id, event_date, event_time, transaction_id, seat_trans_list, status, \
                #account, total_bill_price, back_price, given_price, user_id

            try:
                event_result = yield self.db.runQuery("SELECT id, title, description, admission FROM btms_events WHERE id = '"+str(event_id)+"' ")
                categories_result = yield self.db.runQuery("SELECT * FROM btms_categories WHERE venue_id = '"+str(venue_id)+"'")
                prices_result = yield self.db.runQuery("SELECT id, name, price, description, currency FROM btms_prices WHERE event_id = '"+str(event_id)+"'")
                venue_result = yield  self.db.runQuery("SELECT * FROM btms_venues WHERE ref = '"+str(venue_id)+"' ORDER by id")
                tickets_result = yield self.db.runQuery("SELECT * FROM btms_tickets WHERE tid = '"+str(transaction_id)+"' ORDER by ticket_id")

            finally:
                r = createPdfTicket(self, transaction_id, tickets_result,event_result, categories_result, prices_result, venue_result, user_id)

                try:
                    self.busy_transactions.remove(transaction_id)
                except ValueError:
                    print 'Transaction Id not in busy list.'

                returnValue(r)

    @wamp.register(u'io.crossbar.btms.ticket.reprint')
    @inlineCallbacks
    def reprintTicket(self, event_id, venue_id, transaction_id, user_id):
        try:
            event_result = yield self.db.runQuery("SELECT id, title, description, admission FROM btms_events WHERE id = '"+str(event_id)+"' ")
            categories_result = yield self.db.runQuery("SELECT * FROM btms_categories WHERE venue_id = '"+str(venue_id)+"'")
            prices_result = yield self.db.runQuery("SELECT id, name, price, description, currency FROM btms_prices WHERE event_id = '"+str(event_id)+"'")
            venue_result = yield  self.db.runQuery("SELECT * FROM btms_venues WHERE ref = '"+str(venue_id)+"' ORDER by id")
            tickets_result = yield self.db.runQuery("SELECT * FROM btms_tickets WHERE tid = '"+str(transaction_id)+"' ORDER by ticket_id")

        finally:
            r = createPdfTicket(self, transaction_id, tickets_result,event_result, categories_result, prices_result, venue_result, user_id)

            returnValue(r)

    @wamp.register(u'io.crossbar.btms.reservation.release')
    @inlineCallbacks
    def releaseReservation(self, event_id, event_date, event_time, user_id):
        edt_id = "%s_%s_%s" % (event_id,event_date,event_time)

        try:
            self.busy_transactions
        except AttributeError:
            self.busy_transactions = []

        print self.busy_transactions, event_id, event_date, event_time


        try:
            result = yield self.db.runQuery("SELECT id, tid, item_id, cat_id, art, amount FROM btms_transactions WHERE "
                                            "event_id = '"+str(event_id)+"' AND date = '"+str(event_date)+"' AND "
                                            "time = '"+str(event_time)+"' AND status = '"+str(1)+"'")
            new_seat_select_list = {}
            itm_cat_amount_list = {}
            tid_old = 0
            for row in result:

                if row['tid'] in self.busy_transactions:
                    print'is in list', row['tid']
                else:
                    print 'not in list', row['tid']

                    json_string = row['amount'].replace(';',':')
                    json_string = json_string.replace('\\','')
                    #json_string = '[' + json_string + ']'
                    amount = json.loads(json_string)

                    itm_cat_amount_list[row['cat_id']] = amount
                    #Numbered Seats
                    for item_id, value in self.item_list[edt_id].iteritems():

                        for seat, tid in value['seats_tid'].iteritems(): #items

                            if row['tid'] == tid:

                                try:
                                    new_seat_select_list[item_id]
                                except KeyError:
                                    new_seat_select_list[item_id] = {}
                                if self.item_list[edt_id][item_id]['seats'][seat] == 1:
                                    new_seat_select_list[item_id][seat] = 0

                                    self.item_list[edt_id][item_id]['seats'][seat] = 0
                                    self.item_list[edt_id][item_id]['seats_user'][seat] = 0
                                    self.item_list[edt_id][item_id]['seats_tid'][seat] = 0

                    #Unnumbered Seats
                    if row['art'] == 2:
                        print 'rowart', row['art'], row['item_id'], row['tid']
                        self.unnumbered_seat_list[edt_id][str(row['item_id'])]['tid_amount'][str(row['tid'])] = 0

                    #Delete from db with status 1 and not busy
                    sql = "DELETE FROM btms_transactions WHERE id = '"+str(row['id'])+"'"
                    self.db.runOperation(sql)


                    #Set from last iteration
                    self.setJournal(row['tid'], event_id, event_date, event_time, 1220, 0, '0', '0', '0', 3, user_id)


        except Exception as err:
            print "Error", err
        finally:
            self.publish('io.crossbar.btms.seats.select.action', edt_id, new_seat_select_list, 0, None, 0)
            #Puplish Unnumbered Seats
            for item_id, value in self.unnumbered_seat_list[edt_id].iteritems():
                amount1 = 0
                for key1, value1 in value['tid_amount'].iteritems():
                    amount1 = amount1 + value1
                    print key1, value1

                amount2 = self.unnumbered_seat_list[edt_id][str(item_id)]['amount'] - amount1

                self.item_list[edt_id][str(item_id)]['amount'] = amount2
                print amount1, amount2

                self.publish('io.crossbar.btms.unnumbered_seats.set.action', edt_id, item_id, amount2)


    @wamp.register(u'io.crossbar.btms.contingents.get')
    @inlineCallbacks
    def getContingents(self,cmd, conti_id, event_date, event_time):
        if cmd == 0:
            try:
                #TODO WHERE event_id and time
                result = yield self.db.runQuery("SELECT id, title FROM btms_contingents WHERE ref = '0' ORDER by id")
            except Exception as err:
                print "Error", err
            finally:
                returnValue(result)
        elif cmd == 1:
            try:
                result = yield self.db.runQuery("SELECT item_id, cat_id, art, amount, seats FROM btms_contingents WHERE ref = '"+str(conti_id)+"' AND date_day = '"+event_date+"' AND time = '"+event_time+"' ORDER by id")
            except Exception as err:
                print "Error", err
            finally:
                returnValue(result)


    @wamp.register(u'io.crossbar.btms.contingent.release')
    #@inlineCallbacks
    def releaseContingent(self, event_id, event_date, event_time, conti_id, seat_trans_list, itm_cat_amount_list, total_bill_price, user_id):
        print 'Contingent released', event_id, event_date, event_time, conti_id, seat_trans_list, itm_cat_amount_list, total_bill_price, user_id
        edt_id = "%s_%s_%s" % (event_id,event_date,event_time)
        transaction_id = edt_id+str(conti_id)
        transaction_id = filter(str.isalnum, str(transaction_id))
        transaction_id = 'con'+str(transaction_id)

        self.setJournal(transaction_id, event_id, event_date, event_time, 1210, itm_cat_amount_list,total_bill_price, 0, 0, 2, user_id)


        if seat_trans_list == {}:
            pass
        else:

            for item_id, seat_list in seat_trans_list.iteritems():
                for seat, status in seat_list.iteritems():
                    self.item_list[edt_id][item_id]['seats'][seat] = status


            self.publish('io.crossbar.btms.seats.select.action', edt_id, seat_trans_list, 0, transaction_id, 0)

            cat_id = self.item_list[edt_id][item_id]['cat_id']
            amount = json.dumps(itm_cat_amount_list[str(cat_id)], separators=(',',';'))
            art = '1'
            seats = json.dumps(seat_trans_list, separators=(',',';'))
            #if retrive_status == False:
            '''
            sql = "insert into btms_transactions(tid, event_id, date, time, item_id, " \
                      "cat_id, art, amount, seats, status, user) " \
                      "values('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" % \
                      (transaction_id, event_id, event_date,
                        event_time, item_id, cat_id, art, amount,
                        seats, status, user_id)

            self.db.runOperation(sql)


            sql = "insert into btms_transactions(tid, event_id, date, time, item_id, " \
                    "cat_id, art, amount, seats, status, user) " \
                    "values('"+str(transaction_id)+"','"+str(event_id)+"','"+event_date+"','"+event_time+"'," \
                    "'0','"+str(cat_id)+"','"+art+"','"+amount+"','"+seats+"','"+str(status)+"','"+str(user_id)+"') " \
                    "ON DUPLICATE KEY UPDATE amount='"+amount+"', seats='"+seats+"', user='"+str(user_id)+"'"

            self.db.runOperation(sql)
            '''

            sql = "UPDATE btms_contingents SET btms_contingents.amount='%s', btms_contingents.seats='%s', btms_contingents.status='%s'," \
                  " btms_contingents.user_id='%s' WHERE btms_contingents.ref='%s' AND " \
                  "btms_contingents.date_day='%s' AND btms_contingents.time='%s' AND " \
                  "btms_contingents.cat_id='%s'" % (amount, seats, '2', user_id, conti_id, event_date, event_time, cat_id)
            self.db.runOperation(sql)


        #Insert or Update unnumbered seats and insert in db

        for item_id, value in self.unnumbered_seat_list[edt_id].iteritems():
            try:
                print self.unnumbered_seat_list[edt_id][item_id]['tid_amount'][transaction_id]

                #self.unnumbered_seat_list[edt_id][item_id]['tid_amount'][transaction_id]
                cat_id = self.item_list[edt_id][item_id]['cat_id']
                amount = json.dumps(itm_cat_amount_list[str(cat_id)], separators=(',',';'))
                art = '2'
                seats = '{}'
                #if retrive_status == False:
                '''
                sql = "insert into btms_transactions(tid, event_id, date, time, item_id, " \
                      "cat_id, art, amount, seats, status, user) " \
                      "values('"+str(transaction_id)+"','"+str(event_id)+"','"+event_date+"','"+event_time+"'," \
                       "'"+str(item_id)+"','"+str(cat_id)+"','"+art+"','"+amount+"','"+seats+"','"+str(status)+"','"+str(user_id)+"') " \
                      "ON DUPLICATE KEY UPDATE amount='"+amount+"', seats='"+seats+"', user='"+str(user_id)+"'"

                self.db.runOperation(sql)
                '''
                #elif retrive_status == True:
                    #sql = "UPDATE btms_transactions SET btms_transactions.amount='%s', btms_transactions.seats='%s'," \
                    #  " btms_transactions.user='%s' WHERE btms_transactions.tid='%s' AND " \
                    #  "btms_transactions.item_id='%s'" % (amount, seats, user_id, transaction_id, item_id)
                    #self.db.runOperation(sql)

                sql = "UPDATE btms_contingents SET btms_contingents.amount='%s', btms_contingents.seats='%s', btms_contingents.status='%s'," \
                  " btms_contingents.user_id='%s' WHERE btms_contingents.ref='%s' AND " \
                  "btms_contingents.date_day='%s' AND btms_contingents.time='%s' AND " \
                  "btms_contingents.cat_id='%s'" % (amount, seats, '2', user_id, conti_id, event_date, event_time, cat_id)
                self.db.runOperation(sql)

            except KeyError:
                pass
        try:
            self.busy_transactions
        except AttributeError:
            self.busy_transactions = []

        try:
            self.busy_transactions.remove(transaction_id)
        except ValueError:
            print 'Transaction Id not in busy list.'
        return



    @wamp.register(u'io.crossbar.btms.contingent.add')
    def addContingent(self, cmd, event_id, event_date_start, event_date_end, event_date, event_time, conti_id, title, seat_trans_list, itm_cat_amount_list, user_id):
        print 'Contingent add',cmd, event_id, event_date, event_time, conti_id, title, seat_trans_list, itm_cat_amount_list, user_id
        edt_id = "%s_%s_%s" % (event_id,event_date,event_time)
        #transaction_id = 'con0'

        if cmd == 0:
            def return_last_id(last_insert_id):
                return last_insert_id

            def execute(sql): #TODO not beautiful should be in a pool class ....
                return self.db.runInteraction(_execute, sql)

            def _execute(trans, sql):
                trans.execute(sql)
                return trans.lastrowid

            sql = "insert into btms_contingents(ref, title, event_id, date_start, date_end, date_day, time, item_id, cat_id, art, amount, seats, status, user_id) " \
                  "values('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" \
                  % (0, title, event_id, event_date_start, event_date_end, 0, event_time, 0, 0, 0, {}, {}, 0, user_id)
            #id, ref, title,event_id, date_start, date_end, date_day, time, item_id, cat_id, art, amount, seats, status, user_id, log

            d = execute(sql)
            d.addCallback(return_last_id)

            return d

        elif cmd == 1:


            @inlineCallbacks
            def insert_contingents():
                transaction_id = edt_id+str(conti_id)
                transaction_id = filter(str.isalnum, str(transaction_id))
                transaction_id = 'con'+str(transaction_id)

                #Prepare numbered Seats
                if seat_trans_list == {}:
                    pass
                else:

                    for item_id, seat_list in seat_trans_list.iteritems():
                        for seat, status in seat_list.iteritems():
                            self.item_list[edt_id][item_id]['seats'][seat] = 4
                            #self.item_list[edt_id][item_id]['seats_tid'][seat] = transaction_id

                    self.publish('io.crossbar.btms.seats.select.action', edt_id, seat_trans_list, 0, None, 0)


                    nr_cat_id = self.item_list[edt_id][item_id]['cat_id']
                    nr_amount = json.dumps(itm_cat_amount_list[str(nr_cat_id)], separators=(',',';'))
                    nr_art = '1'
                    nr_seats = json.dumps(seat_trans_list, separators=(',',';'))


                #Insert Contingent for every day of event and time
                result_days = yield self.getEventsDay(event_id)

                for rows in result_days:

                    #Insert numbered seats
                    if seat_trans_list == {}:
                        pass
                    else:
                        sql = "insert into btms_contingents(ref, title, event_id, date_start, date_end, date_day, time, item_id, cat_id, art, amount, seats, status, user_id) " \
                            "values('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" \
                            % (conti_id, '', event_id, 0, 0, rows['date_day'], event_time, 0, nr_cat_id, nr_art, nr_amount, nr_seats, 0, user_id)

                        self.db.runOperation(sql)

                    #Insert unnumbered seats and insert in db
                    for item_id, value in self.unnumbered_seat_list[edt_id].iteritems():
                        try:
                            print self.unnumbered_seat_list[edt_id][item_id]['tid_amount'][transaction_id]
                            unnr_cat_id = self.item_list[edt_id][item_id]['cat_id']
                            unnr_amount = json.dumps(itm_cat_amount_list[str(unnr_cat_id)], separators=(',',';'))
                            unnr_art = '2'
                            unnr_seats = '{}'



                            #Insert
                            sql2 = "insert into btms_contingents(ref, title, event_id, date_start, date_end, date_day, time, item_id, cat_id, art, amount, seats, status, user_id) " \
                                "values('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" \
                                % (conti_id, '', event_id, 0, 0, rows['date_day'], event_time, item_id, unnr_cat_id, unnr_art, unnr_amount, unnr_seats, 0, user_id)

                            self.db.runOperation(sql2)

                        except KeyError:
                            pass

                #remove from busy transactions
                try:
                    self.busy_transactions
                except AttributeError:
                    self.busy_transactions = []

                try:
                    self.busy_transactions.remove(transaction_id)
                except ValueError:
                    print 'Transaction Id not in busy list.'

            insert_contingents()








    @wamp.register(u'io.crossbar.btms.journal.get')
    def getJournal(self,cmd, event_id, event_date, event_time, user_id):
        if cmd == 'cash_today':
            results = self.db.runQuery("SELECT tid, debit, credit, given, back, reg_date_time FROM btms_journal " \
                                   "WHERE event_id = '"+str(event_id)+"' AND event_date = '"+event_date+"' AND " \
                                    " event_time = '"+event_time+"' AND user_id = '"+str(user_id)+"' AND account = '1000'" \
                                    "ORDER by reg_date_time DESC LIMIT 15")
            return results
        elif cmd == 'card_today':
            results = self.db.runQuery("SELECT tid, debit, credit, given, back, reg_date_time FROM btms_journal " \
                           "WHERE event_id = '"+str(event_id)+"' AND event_date = '"+event_date+"' AND " \
                            " event_time = '"+event_time+"' AND user_id = '"+str(user_id)+"' AND account = '1200'" \
                            "ORDER by reg_date_time DESC LIMIT 15")
            return results
        elif cmd == 'reserved_today':
            results = self.db.runQuery("SELECT tid, debit, credit, given, back, reg_date_time FROM btms_journal " \
                           "WHERE event_id = '"+str(event_id)+"' AND event_date = '"+event_date+"' AND " \
                            " event_time = '"+event_time+"' AND user_id = '"+str(user_id)+"' AND status = '1'" \
                            "ORDER by reg_date_time DESC LIMIT 15")
            return results

    @wamp.register(u'io.crossbar.btms.journal.set')
    def setJournal(self, tid, event_id, event_date, event_time, account, itm_cat_amount_list, debit, given, back, status, user_id):

        reg_date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        amount = json.dumps(itm_cat_amount_list, separators=(',',';'))
        '''
        sql = "insert into btms_journal(tid, event_id, event_date, event_time, account, amount, debit, given, back, status, user_id, reg_date_time)" \
              " values('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" % (tid, event_id, event_date, event_time, account, amount, debit, given, back, status, user_id, reg_date_time)
        self.db.runOperation(sql)
        '''
        if itm_cat_amount_list == 0:
            #If release reservations
            sql = "UPDATE btms_journal SET btms_journal.account='%s', btms_journal.status='%s', btms_journal.user_id='%s'" \
                  " WHERE btms_journal.tid='%s' " % (account, status, user_id, tid)
            self.db.runOperation(sql)
        else:
            sql = "insert into btms_journal(tid, event_id, event_date, event_time, account, amount, debit, given, back, status, user_id, reg_date_time) " \
                    "values('"+str(tid)+"','"+str(event_id)+"','"+event_date+"','"+event_time+"'," \
                    " '"+str(account)+"','"+amount+"','"+str(debit)+"','"+str(given)+"','"+str(back)+"','"+str(status)+"','"+str(user_id)+"','"+str(reg_date_time)+"') " \
                    "ON DUPLICATE KEY UPDATE account='"+str(account)+"', amount='"+amount+"', debit='"+str(debit)+"', given='"+str(given)+"', back='"+str(back)+"', " \
                    "status='"+str(status)+"', user_id='"+str(user_id)+"', reg_date_time='"+str(reg_date_time)+"' "
            self.db.runOperation(sql)


    @wamp.register(u'io.crossbar.btms.report.get')
    @inlineCallbacks
    def getReport(self,cmd, event_id, venue_id, event_date, event_time, selected_user_id, cmd_print, printer, for_on_date, user_id):
        print cmd, event_id, venue_id, event_date, event_time, selected_user_id, printer, user_id, for_on_date
        if cmd == 0:
            try:
                if selected_user_id == 'all':
                    if for_on_date == 0:
                        results = yield self.db.runQuery("SELECT account, amount, debit, status, user_id FROM btms_journal " \
                            "WHERE event_id = '"+str(event_id)+"' AND event_date = '"+event_date+"' AND " \
                            " event_time = '"+event_time+"' ")
                    elif for_on_date == 1:
                        results = yield self.db.runQuery("SELECT account, amount, debit, status, user_id FROM btms_journal " \
                            "WHERE event_id = '"+str(event_id)+"' AND reg_date_time LIKE '"+event_date+'%'+"' ")
                else:
                    if for_on_date == 0:
                        results = yield self.db.runQuery("SELECT account, amount, debit, status, user_id FROM btms_journal " \
                            "WHERE event_id = '"+str(event_id)+"' AND event_date = '"+event_date+"' AND " \
                            " event_time = '"+event_time+"' AND user_id = '"+str(selected_user_id)+"' ")
                    elif for_on_date == 1:
                        results = yield self.db.runQuery("SELECT account, amount, debit, status, user_id FROM btms_journal " \
                            "WHERE event_id = '"+str(event_id)+"' AND reg_date_time LIKE '"+event_date+'%'+"' AND user_id = '"+str(selected_user_id)+"' ")

            except Exception as err:
                print "Error", err
                results = {}

            #Get Prices
            try:
                prices = yield self.getPrices(event_id)
                itm_price_list = {}
                for prow in prices:
                    print prow['id'], prow['price']
                    itm_price_list[prow['id']] = prow['price']

            except Exception as err:
                print "Error", err

            report_result_dict = {}
            report_result_dict['all'] = {}
            report_result_dict['all']['m_total_sold'] = 0
            report_result_dict['all']['m_sold_cash'] = 0
            report_result_dict['all']['m_sold_card'] = 0
            report_result_dict['all']['m_sold_conti'] = 0
            report_result_dict['all']['m_total_pre'] = 0
            report_result_dict['all']['m_reserved'] = 0
            report_result_dict['all']['m_not_visited'] = 0
            report_result_dict['all']['m_prices'] = {}


            report_result_dict['all']['a_total_sold'] = 0
            report_result_dict['all']['a_sold_cash'] = 0
            report_result_dict['all']['a_sold_card'] = 0
            report_result_dict['all']['a_sold_conti'] = 0
            report_result_dict['all']['a_total_pre'] = 0
            report_result_dict['all']['a_reserved'] = 0
            report_result_dict['all']['a_not_visited'] = 0
            report_result_dict['all']['a_prices'] = {}

            for row in results:
                if row['status'] == 3:
                    pass #Dont Count the not visited
                else:
                    #Money
                    if row['account'] == 1210:
                        pass #No data available from resellers
                    else:
                        report_result_dict['all']['m_total_pre'] = report_result_dict['all']['m_total_pre'] + row['debit']

                #Get Amount
                json_string = row['amount'].replace(';',':')
                json_string = json_string.replace('\\','')
                json_string = '[' + json_string + ']'
                item_amount = json.loads(json_string)

                try:
                    item_amount[0]
                    total_amount = 0
                    for cat, value in item_amount[0].iteritems():
                        try:
                            report_result_dict['cat_'+str(cat)]
                        except KeyError:
                            report_result_dict['cat_'+str(cat)] = {}

                            report_result_dict['cat_'+str(cat)]['a_total_sold'] = 0
                            report_result_dict['cat_'+str(cat)]['a_sold_cash'] = 0
                            report_result_dict['cat_'+str(cat)]['a_sold_card'] = 0
                            report_result_dict['cat_'+str(cat)]['a_sold_conti'] = 0
                            report_result_dict['cat_'+str(cat)]['a_reserved'] = 0
                            report_result_dict['cat_'+str(cat)]['a_total_pre'] = 0
                            report_result_dict['cat_'+str(cat)]['a_not_visited'] = 0
                            report_result_dict['cat_'+str(cat)]['a_prices'] = {}


                            report_result_dict['cat_'+str(cat)]['m_total_sold'] = 0
                            report_result_dict['cat_'+str(cat)]['m_sold_cash'] = 0
                            report_result_dict['cat_'+str(cat)]['m_sold_card'] = 0
                            report_result_dict['cat_'+str(cat)]['m_sold_conti'] = 0
                            report_result_dict['cat_'+str(cat)]['m_reserved'] = 0
                            report_result_dict['cat_'+str(cat)]['m_total_pre'] = 0
                            report_result_dict['cat_'+str(cat)]['m_not_visited'] = 0
                            report_result_dict['cat_'+str(cat)]['m_prices'] = {}



                        cat_amount = 0
                        cat_price = 0
                        for price_id, value in value.iteritems():
                            #Amount
                            total_amount = total_amount + value
                            cat_amount = cat_amount + value

                            #Money
                            itm_price = float(itm_price_list[int(price_id)]) * value
                            cat_price = cat_price + itm_price


                        if row['status'] == 3:
                            pass #Dont Count the not visited
                        else:
                            report_result_dict['cat_'+str(cat)]['a_total_pre'] = report_result_dict['cat_'+str(cat)]['a_total_pre'] + cat_amount
                            if row['account'] == 1210:
                                pass #No data available from resellers
                            else:
                                report_result_dict['cat_'+str(cat)]['m_total_pre'] = report_result_dict['cat_'+str(cat)]['m_total_pre'] + cat_price

                    if row['status'] == 3:
                        pass #Dont Count the not visited
                    else:
                        report_result_dict['all']['a_total_pre'] = report_result_dict['all']['a_total_pre'] + total_amount

                except IndexError:
                    pass
                #Sold
                if row['status'] == 2:
                    #Money
                    if row['account'] == 1210:
                        pass #No data available from resellers
                    else:
                        report_result_dict['all']['m_total_sold'] = report_result_dict['all']['m_total_sold'] + row['debit']
                    #Tickets
                    try:
                        item_amount[0]
                        total_amount = 0

                        for cat, value in item_amount[0].iteritems():
                            cat_amount = 0
                            cat_price = 0
                            for price_id, value in value.iteritems():
                                #Amount
                                total_amount = total_amount + value
                                cat_amount = cat_amount + value
                                try:
                                    report_result_dict['cat_'+str(cat)]['a_prices'][price_id] = report_result_dict['cat_'+str(cat)]['a_prices'][price_id] + value
                                except KeyError:
                                    report_result_dict['cat_'+str(cat)]['a_prices'][price_id] = value
                                #Money
                                if row['account'] == 1210:
                                    itm_price = 0
                                else:
                                    itm_price = float(itm_price_list[int(price_id)]) * value

                                cat_price = cat_price + itm_price
                                try:
                                    report_result_dict['cat_'+str(cat)]['m_prices'][price_id] = report_result_dict['cat_'+str(cat)]['m_prices'][price_id] + itm_price
                                except KeyError:
                                    report_result_dict['cat_'+str(cat)]['m_prices'][price_id] = itm_price

                            report_result_dict['cat_'+str(cat)]['a_total_sold'] = report_result_dict['cat_'+str(cat)]['a_total_sold'] + cat_amount
                            if row['account'] == 1210:
                                pass #No data available from resellers
                            else:
                                report_result_dict['cat_'+str(cat)]['m_total_sold'] = report_result_dict['cat_'+str(cat)]['m_total_sold'] + cat_price

                        report_result_dict['all']['a_total_sold'] = report_result_dict['all']['a_total_sold'] + total_amount
                    except IndexError:
                        pass
                    #Sold Cash
                    if row['account'] == 1000:
                        #Money
                        report_result_dict['all']['m_sold_cash'] = report_result_dict['all']['m_sold_cash'] + row['debit']

                        #Tickets
                        try:
                            item_amount[0]
                            total_amount = 0
                            for cat, value in item_amount[0].iteritems():
                                cat_amount = 0
                                cat_price = 0
                                for price_id, value in value.iteritems():
                                    #Amount
                                    total_amount = total_amount + value
                                    cat_amount = cat_amount + value
                                    #Money
                                    itm_price = float(itm_price_list[int(price_id)]) * value
                                    cat_price = cat_price + itm_price

                                report_result_dict['cat_'+str(cat)]['a_sold_cash'] = report_result_dict['cat_'+str(cat)]['a_sold_cash'] + cat_amount
                                report_result_dict['cat_'+str(cat)]['m_sold_cash'] = report_result_dict['cat_'+str(cat)]['m_sold_cash'] + cat_price

                            report_result_dict['all']['a_sold_cash'] = report_result_dict['all']['a_sold_cash'] + total_amount

                        except IndexError:
                            pass
                    #Sold Card
                    if row['account'] == 1200:
                        #Money
                        report_result_dict['all']['m_sold_card'] = report_result_dict['all']['m_sold_card'] + row['debit']
                        #report_result_dict['cat_'+str(cat)]['m_sold_card'] = report_result_dict['cat_'+str(cat)]['m_sold_card'] + row['debit']

                        #Tickets
                        try:
                            item_amount[0]
                            total_amount = 0
                            for cat, value in item_amount[0].iteritems():
                                cat_amount = 0
                                cat_price = 0
                                for price_id, value in value.iteritems():
                                    #Amount
                                    total_amount = total_amount + value
                                    cat_amount = cat_amount + value
                                    #Money
                                    itm_price = float(itm_price_list[int(price_id)]) * value
                                    cat_price = cat_price + itm_price
                                report_result_dict['cat_'+str(cat)]['a_sold_card'] = report_result_dict['cat_'+str(cat)]['a_sold_card'] + cat_amount
                                report_result_dict['cat_'+str(cat)]['m_sold_card'] = report_result_dict['cat_'+str(cat)]['m_sold_card'] + cat_price

                            report_result_dict['all']['a_sold_card'] = report_result_dict['all']['a_sold_card'] + total_amount
                        except IndexError:
                            pass
                    #Sold Contingent
                    if row['account'] == 1210:
                        #Money
                        #report_result_dict['all']['m_sold_conti'] = report_result_dict['all']['m_sold_conti'] + row['debit']

                        #Tickets

                        try:
                            item_amount[0]
                            total_amount = 0
                            for cat, value in item_amount[0].iteritems():
                                cat_amount = 0
                                cat_price = 0
                                for price_id, value in value.iteritems():
                                    #Amount
                                    total_amount = total_amount + value
                                    cat_amount = cat_amount + value
                                    #Money
                                    itm_price = float(itm_price_list[int(price_id)]) * value
                                    cat_price = cat_price + itm_price

                                report_result_dict['cat_'+str(cat)]['a_sold_conti'] = report_result_dict['cat_'+str(cat)]['a_sold_conti'] + cat_amount
                                #report_result_dict['cat_'+str(cat)]['m_sold_conti'] = report_result_dict['cat_'+str(cat)]['m_sold_conti'] + cat_price

                            report_result_dict['all']['a_sold_conti'] = report_result_dict['all']['a_sold_conti'] + total_amount
                        except IndexError:
                            pass


                #Reserved
                if row['status'] == 1:
                    #Money Pre
                    if row['account'] == 1210:
                        pass
                    else:
                        report_result_dict['all']['m_reserved'] = report_result_dict['all']['m_reserved'] + row['debit']


                    #Tickets
                    try:
                        item_amount[0]
                        total_amount = 0
                        for cat, value in item_amount[0].iteritems():
                            cat_amount = 0
                            cat_price = 0
                            for price_id, value in value.iteritems():
                                #Amount
                                total_amount = total_amount + value
                                cat_amount = cat_amount + value
                                #Money
                                itm_price = float(itm_price_list[int(price_id)]) * value
                                cat_price = cat_price + itm_price

                            report_result_dict['cat_'+str(cat)]['a_reserved'] = report_result_dict['cat_'+str(cat)]['a_reserved'] + cat_amount
                            report_result_dict['cat_'+str(cat)]['m_reserved'] = report_result_dict['cat_'+str(cat)]['m_reserved'] + cat_price
                        if row['account'] == 1210:
                            pass
                        else:
                            report_result_dict['all']['a_reserved'] = report_result_dict['all']['a_reserved'] + total_amount
                    except IndexError:
                        pass
                #Not visited
                if row['status'] == 3:
                    #Money Pre
                    if row['account'] == 1210:
                        pass
                    else:
                        report_result_dict['all']['m_not_visited'] = report_result_dict['all']['m_not_visited'] + row['debit']

                    #Tickets
                    try:
                        item_amount[0]
                        total_amount = 0
                        for cat, value in item_amount[0].iteritems():
                            cat_amount = 0
                            cat_price = 0
                            for price_id, value in value.iteritems():
                                #Amount
                                total_amount = total_amount + value
                                cat_amount = cat_amount + value
                                #Money
                                itm_price = float(itm_price_list[int(price_id)]) * value
                                cat_price = cat_price + itm_price

                            report_result_dict['cat_'+str(cat)]['a_not_visited'] = report_result_dict['cat_'+str(cat)]['a_not_visited'] + cat_amount
                            report_result_dict['cat_'+str(cat)]['m_not_visited'] = report_result_dict['cat_'+str(cat)]['m_not_visited'] + cat_price
                        if row['account'] == 1210:
                            pass
                        else:
                            report_result_dict['all']['a_not_visited'] = report_result_dict['all']['a_not_visited'] + total_amount
                    except IndexError:
                        pass

            if cmd_print == 0:
                returnValue(report_result_dict)
            elif cmd_print == 1:
                event_result = yield self.db.runQuery("SELECT id, title, description, date_start, date_end, admission FROM btms_events WHERE id = '"+str(event_id)+"' ")
                categories_result = yield self.db.runQuery("SELECT * FROM btms_categories WHERE venue_id = '"+str(venue_id)+"'")
                prices_result = yield self.db.runQuery("SELECT id, name, price, description, cat_id, currency FROM btms_prices WHERE event_id = '"+str(event_id)+"'")


                createPdfReport(self, event_id, venue_id, event_date, event_time, report_result_dict,event_result,categories_result,prices_result)

                #Create and print report
                ticket_path = '../spool/report.pdf'
                printer_returns = conn.printFile(printer, ticket_path, 'report_'+str(event_id)+'_'+event_date+'_'+event_time+'_'+str(user_id), {})

                returnValue(printer_returns)

        elif cmd == 1:
            print 'print report', printer
            #TODO print report

    @wamp.register(u'io.crossbar.btms.server.get')
    #@inlineCallbacks
    def getServer(self):
        return get_server_stats()

    @wamp.register(u'io.crossbar.btms.valid.validate')
    @inlineCallbacks
    def validate(self,qrcode, vendor, user_id):
        if vendor == 'btms':
            transaction_id, ticket_id = qrcode.split('_', 1)
            print 'tid and ticketid:',transaction_id, ticket_id
            status = 5
            try:
                results = yield self.db.runQuery("SELECT id, status FROM btms_tickets " \
                               "WHERE tid = '"+str(transaction_id)+"' AND ticket_id = '"+ticket_id+"' ")
                for row in results:
                    status = row['status']
                    id = row['id']
                    print 'Ticket DBID:', row['id']

                if status == 0:
                    sql = "UPDATE btms_tickets SET btms_tickets.status='%s', btms_tickets.user='%s'  " \
                      "WHERE btms_tickets.id='%s'" % (1, user_id, id)
                    self.db.runOperation(sql)

                if status == 3:
                    sql = "UPDATE btms_tickets SET btms_tickets.status='%s', btms_tickets.user='%s'  " \
                      "WHERE btms_tickets.id='%s'" % (4, user_id, id)
                    self.db.runOperation(sql)

            except Exception as Err:
                print 'Error', Err

        else:
            print 'Vendor / Code:', vendor, qrcode
            status = 5
            try:
                results = yield self.db.runQuery("SELECT id, status FROM btms_tickets_external " \
                               "WHERE ticket_id = '"+qrcode+"' ")
                for row in results:
                    status = row['status']
                    id = row['id']
                    print 'Ticket DBID:', row['id']

                if status == 0:
                    sql = "UPDATE btms_tickets_external SET btms_tickets_external.status='%s', btms_tickets_external.user='%s'  " \
                      "WHERE btms_tickets_external.id='%s'" % (1, user_id, id)
                    self.db.runOperation(sql)

                if status == 5:
                    sql = "insert into btms_tickets_external(ticket_id, vendor, status, user) " \
                                      "values('%s','%s','%s','%s')" % \
                                      (qrcode, vendor, 1, user_id)
                    status = 0

                    self.db.runOperation(sql)

            except Exception as Err:
                print 'Error', Err

        returnValue(status)

    @wamp.register(u'io.crossbar.btms.users.logout')
    def logout_users(self, user_id, login_time):
        self.publish('io.crossbar.btms.onLogoutUser',user_id, login_time, 'log out users with same id')

    @inlineCallbacks
    def onJoin(self, details):
        ## create a new database connection pool. connections are created lazy (as needed)
        ## see: https://twistedmatrix.com/documents/current/api/twisted.enterprise.adbapi.ConnectionPool.html
        ##
        # Connect to the DB

        Registry.DBPOOL = ReconnectingMySQLConnectionPool(
                        'MySQLdb',
                        db='btms',
                        user='btms',
                        passwd='test',
                        host='127.0.0.1',
                        cp_reconnect=True,
                        cursorclass=MySQLdb.cursors.DictCursor
                    )


        #yield pool.start()
        print("DB connection pool started")

        ## we'll be doing all database access via this database connection pool
        ##
        self.db = Registry.DBPOOL
        ## Keep DB connection alive
        @inlineCallbacks
        def keepAliveDB():
            try:
                result = yield self.db.runQuery("SELECT (1)")
                print "keep alive, db querry run", result

            except Exception as err:
                self.publish('io.crossbar.btms.onLeaveRemote','DB connection closed')
                print "DB Connection Error", err

        l = task.LoopingCall(keepAliveDB)
        l.start(60.0) # call every minute


        ## register all procedures on this class which have been
        ## decorated to register them for remoting.
        ##
        res = yield self.register(self)
        print("BtmsBackend: {} procedures registered!".format(len(res)))


