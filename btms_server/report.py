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
import locale
locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')


def createPdfReport(self,event_id, venue_id, event_date, event_time, report_result_dict, e_result, c_result, p_result):
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

        date_day = dt.datetime.strptime(event_date, "%Y-%m-%d")
        date_day_name = date_day.strftime("%A")

        c.drawString(1*cm,28.5*cm, event_title)
        c.drawString(1*cm,28*cm,event_date_start +' - '+event_date_end)



        c.drawString(8*cm,28.5*cm, date_day_name +' '+ event_date)
        c.drawString(8*cm,28*cm, event_time)
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
                         str(value['m_sold_conti'])+ unichr(8364), str(value['m_reserved'])+ unichr(8364), str(value['m_total_pre'])+ unichr(8364),
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
        c.showPage()


    def createPDF(c):
        c.save()

    c = canvas.Canvas("../spool/report.pdf")
    c.setPageSize((21*cm, 29.7*cm))
    page = 1

    header(page)
    body()
		
		
    createPDF(c)





