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

from autobahn import wamp
from autobahn.twisted.wamp import ApplicationSession




class BtmsBackend(ApplicationSession):

    def __init__(self, config):
        ApplicationSession.__init__(self, config)
        self.init()

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
        
        def get_result(user):
            return self.db.runQuery("SELECT * FROM btms_users ORDER by user")

        def printResult(result):
            pass
            #self.publish('io.crossbar.btms.users.result', result)
            

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

        return self.db.runQuery("SELECT name, price, cat_id FROM btms_prices WHERE event_id = '"+str(event_id)+"'")



    @inlineCallbacks
    def onJoin(self, details):
        ## create a new database connection pool. connections are created lazy (as needed)
        ## see: https://twistedmatrix.com/documents/current/api/twisted.enterprise.adbapi.ConnectionPool.html
        ##
        # Connect to the DB
        #Registry.DBPOOL = adbapi.ConnectionPool('MySQLdb',host="127.0.0.1", user="root", passwd="sjaq123", db="btms")
        #pool = Registry.getConfig()
        #pool = adbapi.ConnectionPool("MySQLdb", host="127.0.0.1", user="root", passwd="sjaq123", db="btms")

        pool = adbapi.ConnectionPool(
                        'MySQLdb',
                        db='btms',
                        user='root',
                        passwd='sjaq123',
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
        print("VotesBackend: {} procedures registered!".format(len(res)))


