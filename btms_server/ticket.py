from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.graphics.barcode import eanbc, qr, usps
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
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
    for vrow in v_result:
        itm_title[vrow['id']] = vrow['title']

    #prices
    pri_name = {}
    for prow in p_result:
        pri_name[prow['id']] = {}
        pri_name[prow['id']]['name'] = prow['name']
        pri_name[prow['id']]['description'] = prow['description']
        pri_name[prow['id']]['price'] = prow['price']
        pri_name[prow['id']]['currency'] = prow['currency']


    c = canvas.Canvas('../spool/ticket_'+ transaction_id +'.pdf')
    c.setPageSize((8*cm, 16*cm))
    for row in t_result:

        date_day = dt.datetime.strptime(row['date'], "%Y-%m-%d")
        date_day_name = date_day.strftime("%A")

        event_start_time  = dt.datetime.strptime(row['time'], "%H:%M")

        hour,minute = event_admission.split(":")


        admission_time = event_start_time - dt.timedelta(hours=int(hour), minutes=int(minute))
        admission_time_1 = format(admission_time, '%H:%M')
        #c.drawImage("company_logo_01.png", 1*cm, 9*cm,6*cm,6*cm)

        c.line(1*cm,8.7*cm,7*cm,8.7*cm)

        c.drawString(1*cm,8*cm, event_description)
        c.drawString(1*cm,7.5*cm,date_day_name+' '+row['date'])
        c.drawString(1*cm,7.0*cm,'Beginn: '+ row['time'] +' Uhr')
        c.drawString(1*cm,6.5*cm,'Einlass: '+ admission_time_1 +' Uhr')

        c.line(1*cm,6.3*cm,7*cm,6.3*cm)

        c.drawString(1*cm,5.5*cm, cat_name[row['cat_id']])
        if row['seat'] == '0':
            seat_text = ' '
        else:
            seat_text = ', Sitz: '+ str(row['seat'])
            #seat_text = '1'

        c.drawString(1*cm,5*cm,itm_title[int(row['item_id'])] + seat_text)

        c.line(1*cm,4.5*cm,7*cm,4.5*cm)

        c.drawString(1*cm,3.7*cm,pri_name[int(row['price_id'])]['description'])
        c.drawString(1*cm,2.5*cm,pri_name[int(row['price_id'])]['price'] +' '+ pri_name[int(row['price_id'])]['currency'])

        #c.drawString(1*cm,7.0*cm,"DE 13405 Berlin")
        # draw a QR code
        qr_code = qr.QrCodeWidget(str(row['tid'])+'_'+str(row['ticket_id']))
        bounds = qr_code.getBounds()
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        d = Drawing(45, 45, transform=[99./width,0,0,99./height,0,0])
        d.add(qr_code)
        renderPDF.draw(d, c, 4*cm, 1.1*cm)


        c.drawString(1*cm,1*cm,"TID: "+ row['tid'] + "_" + str(row['ticket_id']))

        c.showPage()

    c.save()
    return 'ticket created'



