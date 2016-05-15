#from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, TableStyle
#from reportlab.graphics.barcode import eanbc, qr, usps
#from reportlab.graphics.shapes import Drawing
#from reportlab.graphics import renderPDF
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus.tables import Table
#from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing
import datetime as dt

from reportlab.graphics.charts.lineplots import GridLinePlot
from reportlab.lib.colors import Color
from reportlab.graphics.charts.legends import LineLegend
from reportlab.graphics.shapes import Drawing, _DrawingEditorMixin
from reportlab.lib.validators import Auto
from reportlab.graphics.charts.axes import NormalDateXValueAxis



import locale
locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')


def createPdfReport(self,event_id, venue_id, event_date, event_time, report_result_dict, e_result, c_result, p_result, report_date_dict,selected_user_id):
    styles = getSampleStyleSheet()
    date_current = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    #event
    for erow in e_result:
        event_id = erow['id']
        event_title = erow['title']
        event_description = erow['description']
        event_date_start = erow['date_start']
        event_date_end = erow['date_end']
        event_admission = erow['admission']
    #cat
    cat_name = {}
    for crow in c_result:
        cat_name['cat_'+str(crow['id'])] = crow['name']
    #venue
    #itm_title = {}
    #for vrow in v_result:
        #itm_title[vrow['id']] = vrow['title']


    def header(page):
        #Header
        if event_date == 'all':
            date_day_name = 'all'
        else:
            date_day = dt.datetime.strptime(event_date, "%Y-%m-%d")
            date_day_name = date_day.strftime("%A")

        c.drawString(1*cm,28.5*cm, event_title)
        c.drawString(1*cm,28*cm,event_date_start +' - '+event_date_end)



        c.drawString(8*cm,28.5*cm, date_day_name +' '+ event_date)
        c.drawString(8*cm,28*cm, event_time)
        if event_date == 'all':
            c.drawString(10*cm,28*cm, 'Total')
        else:
            if event_time == 'all':
                 c.drawString(10*cm,28*cm, 'ON Date')
            else:
                c.drawString(10*cm,28*cm, 'FOR Date')

        c.drawString(12.5*cm,28*cm, 'User ' + str(selected_user_id))

        c.drawString(18*cm,28.5*cm,"Page "+str(page))
        c.drawString(15.5*cm,28*cm,date_current)


        c.line(1*cm,27.5*cm,20*cm,27.5*cm)


    def body():
        #Body

        size_y = 0.62
        data= [['Sold', 'Cash', 'Card', 'Contingent', 'Reserved', 'Expected', 'Unsold Reserv.']]
        for cat, value in report_result_dict.iteritems():
            size_y = size_y + 1.86
            '''
            if cat == 'all':
                report_cat_name = 'All'
            else:
                report_cat_name = self.report_cat_list[event_id][cat]
            '''
            if cat == 'all':
                categorie_name = 'All'
            else:
                categorie_name = cat_name[cat]

            p = Paragraph('<para alignment="center"><b>'+categorie_name+'</b></para>',styles["Normal"])
            data.append([p,'','','','','',''])
            if cat == 'all':
                data_for_pie = [value['a_total_sold'], value['a_sold_cash'], value['a_sold_card'],
                         value['a_sold_conti'], value['a_reserved'],
                         value['a_not_visited']]

            data.append([value['a_total_sold'], value['a_sold_cash'], value['a_sold_card'],
                         value['a_sold_conti'], value['a_reserved'], value['a_total_pre'],
                         value['a_not_visited']])

            data.append([str(value['m_total_sold'])+ unichr(8364), str(value['m_sold_cash'])+ unichr(8364), str(value['m_sold_card'])+ unichr(8364),
                         '-', str(value['m_reserved'])+ unichr(8364), str(value['m_total_pre'])+ unichr(8364),
                         str(value['m_not_visited'])+ unichr(8364)])


        tstyle = [('INNERGRID', (0,0), (-1,-1), 0.25, colors.grey),
                ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                  ('ALIGN', (0,1), (-1,-1), 'RIGHT'),

                  ('COLBACKGROUNDS', (0, 0), (-1, -1), [
                    colors.lightpink, colors.lightpink, colors.lightpink, colors.lightpink, colors.lightyellow, colors.lightgrey, colors.lightyellow
                ]),
                  ('ROWBACKGROUNDS', (0, 1), (-1, -1), [
                    colors.lightslategray, None,None
                ]),]

        t = Table(data)
        t.setStyle(TableStyle(tstyle))
        t.wrapOn(c, 19*cm, 0*cm)
        pos_y =  26.5 - size_y
        t.drawOn(c, 1*cm, pos_y*cm)

        #Price Details
        #size_y = 0.62

        pdata= []
        for cat, value in report_result_dict.iteritems():
            size_y = size_y + 1.86

            if cat == 'all':
                pass
            else:
                categorie_name = cat_name[cat]

                p = Paragraph('<para alignment="center"><b>'+categorie_name+'</b></para>',styles["Normal"])
                pdata.append([p])

                data_price_titles = []
                data_price_amount = []
                data_price_total = []
                for prow in p_result:
                    if cat == 'cat_'+str(prow['cat_id']):
                        data_price_titles.append(prow['name'])
                        try:
                            data_price_amount.append(str(value['a_prices'][str(prow['id'])]))
                        except KeyError:
                            data_price_amount.append('0')

                        try:
                            data_price_total.append(str(value['m_prices'][str(prow['id'])])+ unichr(8364))
                        except KeyError:
                            data_price_total.append('0'+ unichr(8364))

                print data_price_titles
                pdata.append(data_price_titles)
                pdata.append(data_price_amount)
                pdata.append(data_price_total)


        tstyle = [('INNERGRID', (0,0), (-1,-1), 0.25, colors.grey),
                ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                  ('ALIGN', (0,1), (-1,-1), 'RIGHT'),

                  ('COLBACKGROUNDS', (0, 0), (-1, -1), [
                    colors.lightgrey,  colors.whitesmoke
                ]),
                  ('ROWBACKGROUNDS', (0, 0), (-1, -1), [
                    colors.lightslategray, None,None,None
                ]),]

        t = Table(pdata)
        t.setStyle(TableStyle(tstyle))
        t.wrapOn(c, 19*cm, 0*cm)
        pos_y =  25 - size_y
        t.drawOn(c, 1*cm, pos_y*cm)

        '''
        #Pie Chart

        d = Drawing(500, 500)
        pc = Pie()
        pc.x = 65
        pc.y = 15
        pc.width = 200
        pc.height = 200
        pc.data = data_for_pie
        pc.labels = ['Sold','Cash','Card','Contingent','Reserved','Unsold Reserv.']
        pc.slices.strokeWidth=0.5
        pc.slices[0].popout = 10
        #pc.slices[0].strokeWidth = 2
        #pc.slices[0].strokeDashArray = [2,2]
        pc.slices[0].labelRadius = 1.3
        pc.slices[0].fontColor = colors.red
        pc.slices[0].fillColor = colors.lightpink
        pc.slices[1].fillColor = colors.lightpink
        pc.slices[2].fillColor = colors.lightpink
        pc.slices[3].fillColor = colors.lightpink
        pc.slices[4].fillColor = colors.lightyellow
        pc.slices[5].fillColor = colors.lightyellow
        d.add(pc)
        d.wrapOn(c, 5*cm, 5*cm)
        d.drawOn(c, 1*cm, 1*cm)
        '''
        if event_date == 'all':
            data = []
            sold = []
            reserved = []
            unsold_reserved = []
            sold_contingent = []

            for key, value in sorted(report_date_dict.iteritems(), key=lambda report_date_dict: report_date_dict[0]):
                date_day_dt = dt.datetime.strptime(key, "%Y-%m-%d")
                date_day = date_day_dt.strftime("%Y%m%d")

                sold.append((int(date_day), value['sold']))

                reserved.append((int(date_day),value['reserved']))

                unsold_reserved.append((int(date_day),value['unsold_reserved']))

                sold_contingent.append((int(date_day),value['sold_contingent']))


            data.append(sold)
            data.append(reserved)
            data.append(unsold_reserved)
            data.append(sold_contingent)

            print data

            # sample data
            _colors    = Color(.90,0,0), Color(.801961,.801961,0), Color(.380392,.380392,0), Color(.580392,0,0)
            _catNames  = 'Sold', 'Reserved', 'Unsold Reserved', 'Contingents'

            d = Drawing(400, 200)
            # adding the actual chart here.
            plot = GridLinePlot()
            plot.y                             = 50
            plot.x                             = 15
            plot.width                         = 525
            plot.height                        = 125
            plot.xValueAxis.xLabelFormat       = '{ddd} {dd}. {mm}.'
            plot.lineLabels.fontSize           = 6
            plot.lineLabels.boxStrokeWidth     = 0.5
            plot.lineLabels.visible            = 1
            plot.lineLabels.boxAnchor          = 'c'
            plot.lineLabels.angle              = 0
            plot.lineLabelNudge                = 10
            plot.joinedLines                   = 1
            plot.lines.strokeWidth             = 1.5
            plot.lines[0].strokeColor          = _colors[0]
            plot.lines[1].strokeColor          = _colors[1]
            plot.lines[2].strokeColor          = _colors[2]
            plot.lines[3].strokeColor          = _colors[3]
            #sample data
            plot.data = data
            '''
            plot.data  = [[(20010630, 1000),
                           (20011231, 101),
                           (20020630, 100.05),
                           (20021231, 102),
                           (20030630, 103),
                           (20031230, 104),
                           (20040630, 99.200000000000003),
                           (20041231, 99.099999999999994)],

                          [(20010630, 100.8),
                           (20011231, 100.90000000000001),
                           (20020630, 100.2),
                           (20021231, 100.09999999999999),
                           (20030630, 100),
                           (20031230, 100.05),
                           (20040630, 99.900000000000006),
                           (20041231, 99.799999999999997)],

                          [(20010630, 99.700000000000003),
                           (20011231, 99.799999999999997),
                           (20020630, 100),
                           (20021231, 100.01000000000001),
                           (20030630, 95),
                           (20031230, 90),
                           (20040630, 85),
                           (20041231, 80)]]
            '''
            # y axis
            plot.yValueAxis.tickRight              = 0
            plot.yValueAxis.maximumTicks           = 10
            #plot.yValueAxis.leftAxisPercent        = 0
            plot.yValueAxis.tickLeft               = 5
            plot.yValueAxis.valueMax               = None
            plot.yValueAxis.valueMin               = None
            plot.yValueAxis.rangeRound             = 'both'
            plot.yValueAxis.requiredRange          = 30
            plot.yValueAxis.valueSteps             = None
            plot.yValueAxis.valueStep              = None
            plot.yValueAxis.forceZero              = 0
            plot.yValueAxis.labels.fontSize        = 7
            plot.yValueAxis.labels.dy              = 0
            plot.yValueAxis.avoidBoundFrac         = 0.1
            # x axis
            plot.xValueAxis.labels.fontName        = 'Helvetica'
            plot.xValueAxis.labels.fontSize        = 7
            plot.xValueAxis.valueSteps             = None
            plot.xValueAxis.dailyFreq              = 0
            plot.xValueAxis.gridStrokeWidth        = 0.25
            plot.xValueAxis.labels.angle           = 90
            plot.xValueAxis.maximumTicks           = 20
            plot.xValueAxis.tickDown               = 3
            plot.xValueAxis.dailyFreq              = 0
            plot.xValueAxis.bottomAxisLabelSlack   = 0
            plot.xValueAxis.minimumTickSpacing     = 10
            plot.xValueAxis.visibleGrid            = 0
            plot.xValueAxis.gridEnd                =   0
            plot.xValueAxis.gridStart              = 0
            plot.xValueAxis.labels.angle           = 45
            plot.xValueAxis.labels.boxAnchor       = 'e'
            plot.xValueAxis.labels.dx              = 0
            plot.xValueAxis.labels.dy              = -5

            # adding legend
            legend = LineLegend()
            legend.boxAnchor       = 'sw'
            legend.x               = 20
            legend.y               = -2
            legend.columnMaximum   = 1
            legend.yGap            = 0
            legend.deltax          = 50
            legend.deltay          = 0
            legend.dx              = 10
            legend.dy              = 1.5
            legend.fontSize        = 7
            legend.alignment       = 'right'
            legend.dxTextSpace     = 5
            legend.colorNamePairs  = [(_colors[i], _catNames[i]) for i in xrange(len(plot.data))]

            d.add(plot)
            d.add(legend)

            d.wrapOn(c, 18*cm, 5*cm)
            d.drawOn(c, 1*cm, 1*cm)


        c.showPage()


    def createPDF(c):
        c.save()

    c = canvas.Canvas("../spool/report.pdf")
    c.setPageSize((21*cm, 29.7*cm))
    page = 1

    header(page)
    body()
		
		
    createPDF(c)





