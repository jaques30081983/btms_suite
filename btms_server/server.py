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
from ticket import createPdfTicket

from autobahn import wamp
from autobahn.twisted.wamp import ApplicationSession
import json
import datetime as dt

import cups
conn = cups.Connection ()


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

        return self.db.runQuery("SELECT id, date_day, start_times FROM btms_events WHERE ref = '"+str(event_id)+"' ORDER by date_day")

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
    def selectSeats(self,edt_id, seat_select_list, cat_id, tid, user_id):
        print seat_select_list
        new_seat_select_list = {}
        for item_id, seat_list in seat_select_list.iteritems():
            new_seat_select_list = {item_id:{}}
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
                        print 'seat is occupied', item_id, seat, status

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
    def reserve(self, retrive_status, event_id, event_date, event_time, transaction_id,
                 seat_trans_list, itm_cat_amount_list, user_id):
        edt_id = "%s_%s_%s" % (event_id,event_date,event_time)
        status = 1



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

            self.db.runOperation(sql)

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

                self.db.runOperation(sql)
                #elif retrive_status == True:
                    #sql = "UPDATE btms_transactions SET btms_transactions.amount='%s', btms_transactions.seats='%s'," \
                    #  " btms_transactions.user='%s' WHERE btms_transactions.tid='%s' AND " \
                    #  "btms_transactions.item_id='%s'" % (amount, seats, user_id, transaction_id, item_id)
                    #self.db.runOperation(sql)

            except KeyError:
                pass

        try:
            self.busy_transactions.remove(transaction_id)
        except ValueError:
            print 'Transaction Id not in busy list.'
        transaction_id_part = transaction_id[-5:]
        return transaction_id_part


    @wamp.register(u'io.crossbar.btms.retrieve')
    @inlineCallbacks
    def retrieve(self, eventdatetime_id, transaction_id_part):

        transaction_id = eventdatetime_id+transaction_id_part
        transaction_id = filter(str.isalnum, str(transaction_id))
        verify_result = verify(transaction_id)

        if verify_result == True:
            try:

                result = yield self.db.runQuery("SELECT tid, item_id, cat_id, art, amount, seats, status, user FROM btms_transactions WHERE tid = '"+str(transaction_id)+"' ")

            except Exception as err:
                print "Error", err

            if result == ():
                returnValue(True)
            else:
                try:
                    self.busy_transactions
                except AttributeError:
                    self.busy_transactions = []
                self.busy_transactions.append(transaction_id)

                returnValue(result)
        else:
            returnValue(False)






    @wamp.register(u'io.crossbar.btms.transact')
    @inlineCallbacks
    def transact(self, retrive_status, venue_id, event_id, event_date, event_time, transaction_id,
                 seat_trans_list, itm_cat_amount_list, status, account, total_bill_price,
                 back_price, given_price, user_id):


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
            self.db.runOperation(sql)
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
                self.db.runOperation(sql)

            except KeyError:
                pass

        try:
            #Create and Insert Tickets
            #Iterate over seat_list and create new indexed one
            single_seat_list = {}

            i = 0
            for item_id, seat_list in sorted(seat_trans_list.iteritems()):
                cat_id = self.item_list[edt_id][item_id]['cat_id']
                try:
                    single_seat_list[cat_id]
                except KeyError:
                    single_seat_list[cat_id] = {}

                for seat, status in sorted(seat_list.iteritems()):
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
                                        seat, status, user_id)

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
    def releaseReservation(self, event_id, event_date, event_time):
        edt_id = "%s_%s_%s" % (event_id,event_date,event_time)
        try:
            self.busy_transactions
        except AttributeError:
            self.busy_transactions = []

        print self.busy_transactions, event_id, event_date, event_time


        try:
            result = yield self.db.runQuery("SELECT tid, item_id, art FROM btms_transactions WHERE "
                                            "event_id = '"+str(event_id)+"' AND date = '"+str(event_date)+"' AND "
                                            "time = '"+str(event_time)+"' AND status = '"+str(1)+"'")
            new_seat_select_list = {}
            for row in result:

                if row['tid'] in self.busy_transactions:
                    print'is in list', row['tid']
                else:
                    print 'not in list', row['tid']
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

                    #TODO delete from db with status 1 and not busy


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


