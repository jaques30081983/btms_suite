from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
#from reportlab.graphics.barcode import eanbc, qr, usps, createBarcodeDrawing, getCodeNames

from pystrich.datamatrix import DataMatrixEncoder
#import PIL
from reportlab.lib.utils import ImageReader
from cStringIO import StringIO

#from reportlab.graphics.shapes import Drawing
#from reportlab.graphics import renderPDF
import datetime as dt
import locale
locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')


def createPdfTicket(self,transaction_id, t_result,e_result, c_result, p_result, v_result, user_id):

    #print 'tid',transaction_id
    #print 'ticket', t_result
    #print 'cat', c_result
    #print 'price', p_result
    #print 'venue', v_result
    #print 'uid', user_id

    styles = getSampleStyleSheet()

    #event
    for erow in e_result:
        event_id = erow['id']
        event_title = erow['title']
        event_description = erow['description']
        event_admission = erow['admission']
    #cat
    cat_name = {}
    for crow in c_result:
        cat_name[crow['id']] = crow['name']
    #venue
    itm_title = {}
    itm_description = {}
    itm_col = {}
    itm_row = {}
    itm_seats = {}
    itm_space = {}

    for vrow in v_result:
        itm_title[vrow['id']] = vrow['title']
        itm_description[vrow['id']] = vrow['description']
        itm_col[vrow['id']] = vrow['col']
        itm_row[vrow['id']] = vrow['row']
        itm_seats[vrow['id']] = vrow['seats']
        itm_space[vrow['id']] = vrow['space']

    #prices
    pri_name = {}
    for prow in p_result:
        pri_name[prow['id']] = {}
        pri_name[prow['id']]['name'] = prow['name']
        pri_name[prow['id']]['description'] = prow['description']
        pri_name[prow['id']]['price'] = prow['price']
        pri_name[prow['id']]['currency'] = prow['currency']


    c = canvas.Canvas('../spool/ticket_'+ transaction_id +'.pdf')
    c.setPageSize((8.2*cm, 15.2*cm))
    for row in t_result:

        date_day = dt.datetime.strptime(row['date'], "%Y-%m-%d")
        date_day_german = date_day.strftime("%d.%m.%Y")
        date_day_name = date_day.strftime("%A")

        event_start_time  = dt.datetime.strptime(row['time'], "%H:%M")

        hour,minute = event_admission.split(":")


        admission_time = event_start_time - dt.timedelta(hours=int(hour), minutes=int(minute))
        admission_time_1 = format(admission_time, '%H:%M')
        #c.drawImage("company_logo_01.png", 1*cm, 9*cm,6*cm,6*cm)

        #c.line(1*cm,8.7*cm,7*cm,8.7*cm)

        c.drawString(1.1*cm,9*cm, event_description)

        p = Paragraph('<font size=13>'+date_day_name+' <b>'+date_day_german+'</b></font>',styles["Normal"])
        p.wrapOn(c, 8.2*cm, 15.2*cm)
        p.drawOn(c, 1.1*cm, 8.5*cm)


        #c.drawString(1.1*cm,8.5*cm,date_day_name+' '+date_day_german)
        c.drawString(1.1*cm,8.0*cm,'Beginn: '+ row['time'] +' Uhr')
        c.drawString(1.1*cm,7.5*cm,'Einlass: '+ admission_time_1 +' Uhr')

        c.line(1.1*cm,7.3*cm,7.1*cm,7.3*cm)


        seat_text = '0'
        if row['art'] == 1:
            seat_text = 'Platz: <b>'+ str(row['seat'])+'</b>'

        elif row['art'] == 2:
            seat_text = ' '

        elif row['art'] == 3:

            cols = itm_col[int(row['item_id'])]
            rows = itm_row[int(row['item_id'])]
            seats = itm_seats[int(row['item_id'])]
            space = itm_space[int(row['item_id'])]


            #Add additional row if its nessesary
            if cols * rows < seats:
                rows = rows + 1

            #Add additional col for Row Name
            cols = cols + 1

            #Extend seats for row description
            seats = seats + rows

            space = space.split(',')
            k = 0
            j= 0
            matrix = cols * rows
            for i in range(0, matrix):
                if k == 0 or k == cols:
                    #Set row name
                    row_name = str(space[i])
                    k =0
                else:
                    if space[i] == '0':
                        pass
                    else:

                        j= j + 1

                        if str(j) == row['seat']:
                            seat_text = 'Reihe: <b>'+ str(row_name)+'</b>, Platz: <b>'+ str(space[i])+'</b>'

                k = k +1




        #c.drawString(1.1*cm,6.2*cm,itm_title[int(row['item_id'])] + seat_text)
        #block_name, block_number  = itm_title[int(row['item_id'])].split(' ', 1)
        p1 = Paragraph('<font size=13><b>'+itm_description[int(row['item_id'])]+'</b></font>',styles["Normal"])
        p1.wrapOn(c, 8.2*cm, 15.2*cm)
        p1.drawOn(c, 1.1*cm, 6.8*cm)

        p2 = Paragraph('<font size=13>'+seat_text+'</font>',styles["Normal"])
        p2.wrapOn(c, 8.2*cm, 15.2*cm)
        p2.drawOn(c, 1.1*cm, 6.3*cm)

        c.line(1.1*cm,6*cm,7.1*cm,6*cm)

        c.drawString(1.1*cm,5.4*cm, cat_name[row['cat_id']]) #Categorie Name
        c.drawString(1.1*cm,4.6*cm,pri_name[int(row['price_id'])]['description'])
        c.drawString(1.1*cm,3.9*cm,pri_name[int(row['price_id'])]['price'] +' '+ pri_name[int(row['price_id'])]['currency'])

        #c.drawString(1*cm,7.0*cm,"DE 13405 Berlin")
        # draw a QR code
        '''
        qr_code = qr.QrCodeWidget(str(row['tid'])+'_'+str(row['ticket_id']))
        bounds = qr_code.getBounds()
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        d = Drawing(45, 45, transform=[80./width,0,0,80./height,0,0])
        d.add(qr_code)
        renderPDF.draw(d, c, 4.4*cm, 3.1*cm)
        '''
        #d = createBarcodeDrawing('ECC200DataMatrix', value=str(row['tid'])+'_'+str(row['ticket_id']))

        #d.scale(.45,.45)
        #renderPDF.draw(d, c, 4.4*cm, 3.1*cm)
        #print getCodeNames()

        encoder = DataMatrixEncoder(str(row['tid'])+'_'+str(row['ticket_id']))
        output = encoder.get_imagedata()
        io_img = StringIO(output)
        reportlab_io_img = ImageReader(io_img)
        c.drawImage(reportlab_io_img, 5*cm,3.8*cm, width=1.5*cm,height=1.5*cm,mask=None)



        p = Paragraph('<font size=8>'+row['tid']+" "+str(row['ticket_id'])+'</font>',styles["Normal"])
        p.wrapOn(c, 8.2*cm, 15.2*cm)
        p.drawOn(c, 1.1*cm, 2.8*cm)

        #c.drawString(1.1*cm,2.8*cm,row['tid']+" "+str(row['ticket_id']))
        #c.line(1.1*cm,2.2*cm,7.1*cm,2.2*cm)
        c.showPage()

    c.save()
    return True



