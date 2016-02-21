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


def createPdfReport(self,event_id, event_title, venue_id, event_date, event_time, report_result_dict):
    styles = getSampleStyleSheet()
    def header(page):
        #Header 100 Range Cat II, III
        c.drawString(1*cm,28.5*cm, event_title)
        c.drawString(1*cm,28*cm,event_date +' '+event_time)

        date_day_name = ''#TODO

        c.drawString(12*cm,28.5*cm, date_day_name +' '+ event_date)
        c.drawString(12*cm,28*cm, event_time)
        c.drawString(17*cm,28.5*cm,"Total Page "+str(page))

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
            p = Paragraph('<para alignment="center"><b>'+cat+'</b></para>',styles["Normal"])
            data.append(['','','',p,'','',''])
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
                    colors.whitesmoke, None,None
                ]),]

        t = Table(data, colWidths=(2.7*cm, 2.7*cm, 2.7*cm, 2.7*cm, 2.7*cm, 2.7*cm, 2.7*cm))
        t.setStyle(TableStyle(tstyle))
        t.wrapOn(c, 1*cm, 0*cm)

        pos_y =  26.5 - size_y

        t.drawOn(c, 1*cm, pos_y*cm)
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
        d.drawOn(c, 1*cm, 7*cm)

        c.showPage()


    def createPDF(c):
        c.save()

    c = canvas.Canvas("../spool/report.pdf")
    c.setPageSize((21*cm, 29.7*cm))
    page = 1

    header(page)
    body()
		
		
    createPDF(c)





